// prompt_machine_frontend.js
import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "SATA_UtilityNode.PromptMachineFrontend",
    async nodeCreated(node) {
        if (node.comfyClass !== "Prompt_Style_Machine") return;

        // Widgets
        const csvWidget = node.widgets.find(w => w.name === "csv_file");
        const oldNameWidget = node.widgets.find(w => w.name === "name");

        if (!csvWidget || !oldNameWidget) {
            console.warn("[PromptMachineFrontend] Missing widgets, check backend definition.");
            return;
        }

        // Remove the old text input for 'name'
        const index = node.widgets.indexOf(oldNameWidget);
        node.widgets.splice(index, 1);

        // Add proper dropdown (this appends to the end)
        const nameWidget = node.addWidget("combo", "name", "None", () => { }, {
            values: ["None"]
        });
        
        // Move the new widget back to the original position
        // Remove from the end (where addWidget put it)
        node.widgets.splice(node.widgets.indexOf(nameWidget), 1);
        // Insert at the correct index
        node.widgets.splice(index, 0, nameWidget);

        // Store available names
        let namesConfig = [];

        // Fetch names from backend for a given CSV
        async function loadNames(csvValue) {
            if (!csvValue) return;
            try {
                const resp = await fetch(`/sata/prompt_machine/names?csv=${encodeURIComponent(csvValue)}`);
                const data = await resp.json();
                namesConfig = data.names || ["None"];

                refreshNames();
            } catch (err) {
                console.error("[PromptMachineFrontend] Failed to load names:", err);
            }
        }

        // Refresh dropdown with available names
        function refreshNames() {
            const available = namesConfig.length > 0 ? namesConfig : ["None"];
            nameWidget.options.values = available;

            if (!available.includes(nameWidget.value)) {
                nameWidget.value = available[0]; // safe fallback
            }

            // Force update previews for the new name
            updatePreviews(nameWidget.value);

            app.graph.change();
        }

        // Hook CSV change
        const oldCsvCallback = csvWidget.callback;
        csvWidget.callback = function (value) {
            if (oldCsvCallback) oldCsvCallback(value);
            loadNames(value); // refresh dynamically
        };

        // --- Preview Logic ---
        const previewEl = document.createElement("div");
        Object.assign(previewEl.style, {
            marginTop: "10px",
            padding: "8px",
            background: "rgba(0,0,0,0.4)",
            borderRadius: "4px",
            fontSize: "14px",
            lineHeight: "1.5",
            color: "#ddd",
            wordBreak: "break-word",
            maxHeight: "400px",
            overflowY: "auto"
        });
        
        node.addDOMWidget("preview_text", "html", previewEl, {
            getValue: () => previewEl.innerHTML,
            setValue: (v) => { previewEl.innerHTML = v; }
        });

        async function updatePreviews(name) {
            const csv = csvWidget.value;
            if (!csv || !name || name === "None") return;

            try {
                const resp = await fetch(`/sata/prompt_machine/get?csv=${encodeURIComponent(csv)}&name=${encodeURIComponent(name)}`);
                const data = await resp.json();
                let html = "";
                if (data.positive) html += `${data.positive}`;
                
                previewEl.innerHTML = html || "<i>No preview available</i>";
                
                // Adjust node size to fit content
                node.setSize(node.computeSize());

                app.graph.change();
            } catch (err) {
                console.error("[PromptMachineFrontend] Failed to load preview:", err);
            }
        }

        // Hook Name change
        const oldNameCallback = nameWidget.callback;
        nameWidget.callback = function (value) {
            if (oldNameCallback) oldNameCallback(value);
            updatePreviews(value);
        };

        // Initial sync
        loadNames(csvWidget.value).then(() => {
            updatePreviews(nameWidget.value);
        });
    }
});