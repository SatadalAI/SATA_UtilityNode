import { app } from "../../../scripts/app.js";

// Register extension
app.registerExtension({
    name: "SATA_UtilityNode.PromptAutocomplete",
    
    async setup() {
        // Add settings
        app.ui.settings.addSetting({
            id: "SATA.PromptAutocomplete.Trigger",
            name: "Prompt Autocomplete Trigger Character",
            type: "text",
            defaultValue: "#",
        });

        app.ui.settings.addSetting({
            id: "SATA.PromptAutocomplete.Global",
            name: "Prompt Autocomplete Global Mode (All Text Widgets)",
            type: "boolean",
            defaultValue: false,
        });
    },

    async nodeCreated(node) {
        // Check if we should attach to this node
        const isTargetNode = node.comfyClass === "PromptAutocomplete";
        const isGlobal = app.ui.settings.getSettingValue("SATA.PromptAutocomplete.Global", false);

        if (!isTargetNode && !isGlobal) return;

        // Find text widgets
        const textWidgets = node.widgets?.filter(w => w.type === "customtext" || w.type === "text" || w.type === "STRING");
        if (!textWidgets) return;

        // Load snippets (cache them)
        if (!this.snippetsCache) {
            await this.loadSnippets();
        }

        textWidgets.forEach(w => {
            this.attachAutocomplete(w);
        });
    },

    snippetsCache: null,

    async loadSnippets() {
        try {
            // 1. List files
            const listResp = await fetch("/sata/autocomplete/list");
            const listData = await listResp.json();
            const files = listData.files || [];

            this.snippetsCache = {};

            // 2. Load content for each file
            for (const file of files) {
                const contentResp = await fetch(`/sata/autocomplete/get?file=${encodeURIComponent(file)}`);
                const contentData = await contentResp.json();
                this.snippetsCache[file] = contentData.items || [];
            }
            console.log("[PromptAutocomplete] Loaded snippets:", Object.keys(this.snippetsCache));
        } catch (err) {
            console.error("[PromptAutocomplete] Failed to load snippets:", err);
        }
    },

    attachAutocomplete(widget) {
        // We need to hook into the DOM element of the widget
        // ComfyUI widgets usually expose their input element via `inputEl` or we might need to find it.
        // For standard multiline text widgets, it's often a textarea.

        // Wait for the widget to have an element
        const originalDraw = widget.draw;
        const self = this;

        // Hook into the input element creation/usage
        // NOTE: ComfyUI's customtext widget often creates a textarea. 
        // We can try to find the textarea in the DOM if it's active, or hook the input callback.
        
        // A more robust way for ComfyUI widgets:
        // The widget has an `inputEl` property if it's a DOM widget.
        
        // Let's try to hook the `inputEl` if it exists, or wait for it.
        
        // Helper to setup the listener
        function setupListener(input) {
            if (input.dataset.hasAutocomplete) return;
            input.dataset.hasAutocomplete = "true";

            input.addEventListener("keydown", (e) => self.handleKeydown(e, input, widget));
            input.addEventListener("input", (e) => self.handleInput(e, input, widget));
        }

        // Check if inputEl already exists
        if (widget.inputEl) {
            setupListener(widget.inputEl);
        } else {
            // If not, it might be created later. We can hook `onInput` or similar, 
            // but `inputEl` is usually created when the node is drawn or added.
            // Let's poll or hook draw? Hooking draw is safer to catch it.
             widget.draw = function(ctx, node, widgetWidth, y, widgetHeight) {
                const result = originalDraw?.apply(this, arguments);
                if (this.inputEl) {
                    setupListener(this.inputEl);
                }
                return result;
            }
        }
    },

    // --- Autocomplete Logic ---
    
    popup: null,
    active: false,
    currentCategory: null, // null = showing categories, string = showing items
    selectedIndex: 0,
    filteredItems: [],
    triggerChar: "#",

    handleInput(e, input, widget) {
        const trigger = app.ui.settings.getSettingValue("SATA.PromptAutocomplete.Trigger", "#");
        this.triggerChar = trigger;

        const val = input.value;
        const cursor = input.selectionStart;

        // Simple check: is the character before cursor the trigger?
        // Or are we in a "trigger session"?
        
        // If we just typed the trigger
        if (e.data === trigger) {
            this.showPopup(input, cursor);
            return;
        }

        // If active, update filter
        if (this.active) {
            // Find the text after the last trigger
            const lastTriggerIndex = val.lastIndexOf(trigger, cursor - 1);
            if (lastTriggerIndex === -1) {
                this.closePopup();
                return;
            }

            const query = val.substring(lastTriggerIndex + 1, cursor);
            
            // Check if we have a category selected (format: #category:query)
            // But wait, the plan said: Select Category -> Then Items.
            // So maybe we just filter categories first.
            
            if (this.currentCategory) {
                // We are inside a category
                // Check if the query contains the category prefix? 
                // Actually, let's keep it simple:
                // 1. Type # -> Show list of files (categories)
                // 2. Select file -> Insert "filename:" ? Or just switch mode?
                // Let's do: Type # -> Show categories. 
                // If user types more, filter categories.
                // If user selects category, we switch to showing items of that category.
                // But how do we represent that in text? 
                // Maybe we don't change text, just internal state?
                // Standard way: #category:item
                
                // Let's parse the text to see where we are.
                // If text is "#cat", we filter categories.
                // If text is "#cat:ite", we filter items in "cat".
                
                const parts = query.split(":");
                if (parts.length > 1) {
                    // We have a category selected
                    const catName = parts[0];
                    const itemQuery = parts.slice(1).join(":"); // rest is item query
                    
                    // Check if catName is valid
                    if (this.snippetsCache[catName + ".csv"] || this.snippetsCache[catName + ".json"] || this.snippetsCache[catName]) {
                        // It's a valid category (roughly). 
                        // Let's find the exact filename key
                        let key = Object.keys(this.snippetsCache).find(k => k.startsWith(catName));
                        if (key) {
                            this.currentCategory = key;
                            this.updateItems(itemQuery);
                            return;
                        }
                    }
                }
                
                // If no colon, or invalid category, we are filtering categories
                this.currentCategory = null;
                this.updateCategories(query);

            } else {
                // No category selected yet
                // Check for colon
                 const parts = query.split(":");
                 if (parts.length > 1) {
                     // Maybe user typed "style:" manually?
                     const catName = parts[0];
                     let key = Object.keys(this.snippetsCache).find(k => k.replace(/\.(csv|json)$/, "") === catName);
                     if (key) {
                         this.currentCategory = key;
                         this.updateItems(parts.slice(1).join(":"));
                         return;
                     }
                 }

                this.updateCategories(query);
            }
        }
    },

    handleKeydown(e, input, widget) {
        if (!this.active) return;

        if (e.key === "ArrowUp") {
            e.preventDefault();
            this.selectedIndex = Math.max(0, this.selectedIndex - 1);
            this.renderPopup();
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            this.selectedIndex = Math.min(this.filteredItems.length - 1, this.selectedIndex + 1);
            this.renderPopup();
        } else if (e.key === "Enter" || e.key === "Tab") {
            e.preventDefault();
            this.selectItem(input);
        } else if (e.key === "Escape") {
            e.preventDefault();
            this.closePopup();
        }
    },

    showPopup(input, cursor) {
        if (this.popup) document.body.removeChild(this.popup);

        this.popup = document.createElement("div");
        this.popup.className = "sata-autocomplete-popup";
        Object.assign(this.popup.style, {
            position: "absolute",
            zIndex: "9999",
            backgroundColor: "#222",
            border: "1px solid #555",
            maxHeight: "300px",
            overflowY: "auto",
            width: "200px",
            color: "#ddd",
            fontFamily: "monospace",
            fontSize: "12px",
            boxShadow: "0 4px 6px rgba(0,0,0,0.3)"
        });

        // Position popup near cursor (approximate)
        const rect = input.getBoundingClientRect();
        // This is tricky for textarea cursor position. 
        // For now, just place it under the textarea or at bottom left of it.
        // To do it properly requires a library or complex calculation.
        // Let's put it at the bottom-left of the input for now.
        this.popup.style.left = `${rect.left}px`;
        this.popup.style.top = `${rect.bottom}px`;

        document.body.appendChild(this.popup);
        this.active = true;
        this.currentCategory = null;
        this.updateCategories("");
    },

    closePopup() {
        if (this.popup) {
            document.body.removeChild(this.popup);
            this.popup = null;
        }
        this.active = false;
        this.currentCategory = null;
    },

    updateCategories(query) {
        const files = Object.keys(this.snippetsCache || {});
        // Filter by query
        // We display stripped names (no extension)
        this.filteredItems = files.map(f => ({
            type: "category",
            value: f,
            display: f.replace(/\.(csv|json)$/, "")
        })).filter(item => item.display.toLowerCase().includes(query.toLowerCase()));

        this.selectedIndex = 0;
        this.renderPopup();
    },

    updateItems(query) {
        if (!this.currentCategory) return;
        const items = this.snippetsCache[this.currentCategory] || [];
        
        // Filter
        let matches = items.filter(i => i.toLowerCase().includes(query.toLowerCase()));
        
        // Add "Random" option at top
        this.filteredItems = [
            { type: "random", value: "RANDOM", display: "🎲 Random" },
            ...matches.map(i => ({ type: "item", value: i, display: i }))
        ];

        this.selectedIndex = 0;
        this.renderPopup();
    },

    renderPopup() {
        if (!this.popup) return;
        this.popup.innerHTML = "";

        if (this.filteredItems.length === 0) {
            const div = document.createElement("div");
            div.textContent = "No matches";
            div.style.padding = "4px";
            div.style.color = "#888";
            this.popup.appendChild(div);
            return;
        }

        this.filteredItems.forEach((item, idx) => {
            const div = document.createElement("div");
            div.textContent = item.display;
            div.style.padding = "4px 8px";
            div.style.cursor = "pointer";
            div.style.whiteSpace = "nowrap";
            div.style.overflow = "hidden";
            div.style.textOverflow = "ellipsis";

            if (idx === this.selectedIndex) {
                div.style.backgroundColor = "#444";
                div.style.color = "#fff";
                
                // Show preview if it's a long item
                if (item.type === "item" && item.value.length > 30) {
                    this.showPreview(item.value);
                } else {
                    this.hidePreview();
                }
            }

            div.onclick = () => {
                this.selectedIndex = idx;
                this.selectItem(this.activeInput); // We need reference to input
            };
            
            this.popup.appendChild(div);
        });
        
        // Keep active input ref
        const activeElement = document.activeElement;
        if (activeElement && activeElement.tagName === "TEXTAREA") {
            this.activeInput = activeElement;
        }
    },

    previewBox: null,

    showPreview(text) {
        if (!this.previewBox) {
            this.previewBox = document.createElement("div");
            Object.assign(this.previewBox.style, {
                position: "absolute",
                zIndex: "10000",
                backgroundColor: "#333",
                border: "1px solid #666",
                padding: "8px",
                maxWidth: "300px",
                color: "#eee",
                fontSize: "11px",
                pointerEvents: "none"
            });
            document.body.appendChild(this.previewBox);
        }
        
        this.previewBox.textContent = text;
        const rect = this.popup.getBoundingClientRect();
        this.previewBox.style.left = `${rect.right + 5}px`;
        this.previewBox.style.top = `${rect.top}px`;
        this.previewBox.style.display = "block";
    },

    hidePreview() {
        if (this.previewBox) {
            this.previewBox.style.display = "none";
        }
    },

    selectItem(input) {
        const item = this.filteredItems[this.selectedIndex];
        if (!item) return;

        const val = input.value;
        const cursor = input.selectionStart;
        const trigger = this.triggerChar;
        const lastTriggerIndex = val.lastIndexOf(trigger, cursor - 1);

        let textToInsert = "";

        if (item.type === "category") {
            // Insert category name + colon
            // e.g. #style:
            textToInsert = item.display + ":";
            this.currentCategory = item.value;
            // Don't close popup, just update to items
            // We need to update the input value first
            
             // Replace everything from trigger to cursor with trigger + textToInsert
            const before = val.substring(0, lastTriggerIndex + 1); // includes trigger
            const after = val.substring(cursor);
            input.value = before + textToInsert + after;
            
            // Move cursor
            const newCursor = lastTriggerIndex + 1 + textToInsert.length;
            input.setSelectionRange(newCursor, newCursor);
            
            // Trigger input event manually to update state
            this.handleInput({ data: null }, input, null);
            return;

        } else if (item.type === "random") {
            // Pick random item from current category
            const items = this.snippetsCache[this.currentCategory] || [];
            if (items.length > 0) {
                textToInsert = items[Math.floor(Math.random() * items.length)];
            }
        } else {
            // Normal item
            textToInsert = item.value;
        }

        // Replace
        const before = val.substring(0, lastTriggerIndex); // remove trigger
        const after = val.substring(cursor);
        
        // If we are replacing a category query like #style:something, we need to find the start of #
        // Actually, if we are in item mode, the text is "#style:query".
        // We want to replace the whole "#style:query" with "textToInsert".
        
        input.value = before + textToInsert + after;
        
        // Move cursor
        const newCursor = before.length + textToInsert.length;
        input.setSelectionRange(newCursor, newCursor);

        this.closePopup();
        this.hidePreview();
    }
});
