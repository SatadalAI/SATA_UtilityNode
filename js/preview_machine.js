import { app } from "../../scripts/app.js";

// CONSTANTS
const GLOBAL_HIDE_SETTING_ID = "SATA_UtilityNode.GlobalPreviewHide";
const PREVIEW_MACHINE_CLASS = "Preview_Machine";
const SAVE_MACHINE_CLASS = "Save_Machine";

// Track hover state
const hoveredNodeIds = new Set();

app.registerExtension({
    name: "SATA_UtilityNode.Preview_Machine",

    async setup() {
        app.ui.settings.addSetting({
            id: GLOBAL_HIDE_SETTING_ID,
            name: "SATA Utility: Global Hide Previews",
            type: "boolean",
            defaultValue: false,
            onChange: (value) => {
                if (app.graph) app.graph.setDirtyCanvas(true, true);
            }
        });

        setupGlobalMouseTracker();
    },

    async nodeCreated(node) {
        if (isTargetNode(node)) {
            setupNodeHider(node);
        }
    },

    async loadedGraphNode(node) {
        if (isTargetNode(node)) {
            setupNodeHider(node);
        }
    }
});

function isTargetNode(node) {
    return node.comfyClass === "PreviewImage" ||
        node.comfyClass === "SaveImage" ||
        node.comfyClass === PREVIEW_MACHINE_CLASS ||
        node.comfyClass === SAVE_MACHINE_CLASS;
}

function shouldHideNode(node) {
    const globalHide = app.ui.settings.getSettingValue(GLOBAL_HIDE_SETTING_ID, false);

    if (node.comfyClass === PREVIEW_MACHINE_CLASS) {
        return true;
    }

    if (node.comfyClass === SAVE_MACHINE_CLASS) {
        const w = node.widgets?.find(w => w.name === "hide_preview");
        if (w) {
            if (w.value === true) return true;
            if (w.value === false && !globalHide) return false;
        }
        return true;
    }

    return globalHide;
}

function isMouseOverNode(node) {
    if (!app.canvas || !app.canvas.graph_mouse) return false;

    const mouse = app.canvas.graph_mouse;
    const x = mouse[0];
    const y = mouse[1];

    return x >= node.pos[0] &&
        x <= (node.pos[0] + node.size[0]) &&
        y >= node.pos[1] &&
        y <= (node.pos[1] + node.size[1]);
}

function setupGlobalMouseTracker() {
    let rafPending = false;

    const checkAndUpdate = () => {
        if (!app.graph || !app.graph._nodes) return;

        let changed = false;

        for (const node of app.graph._nodes) {
            if (!isTargetNode(node)) continue;

            const currentlyHovered = isMouseOverNode(node);
            const wasHovered = hoveredNodeIds.has(node.id);

            if (currentlyHovered !== wasHovered) {
                if (currentlyHovered) {
                    hoveredNodeIds.add(node.id);
                } else {
                    hoveredNodeIds.delete(node.id);
                }
                changed = true;
            }
        }

        if (changed) {
            app.graph.setDirtyCanvas(true, true);
        }
    };

    window.addEventListener("mousemove", () => {
        if (!rafPending) {
            rafPending = true;
            requestAnimationFrame(() => {
                rafPending = false;
                checkAndUpdate();
            });
        }
    });

    window.addEventListener("mouseout", (e) => {
        if (e.relatedTarget === null) {
            hoveredNodeIds.clear();
            if (app.graph) app.graph.setDirtyCanvas(true, true);
        }
    });
}

function setupNodeHider(node) {
    if (node._sata_hider_v6) return;
    node._sata_hider_v6 = true;

    // Function to check if node should be hidden right now
    const shouldHideNow = () => {
        const shouldHide = shouldHideNode(node);
        const hovered = hoveredNodeIds.has(node.id);
        return shouldHide && !hovered;
    };

    // Find and patch all image-related widgets on the node
    const patchWidgets = () => {
        if (!node.widgets) return;

        for (const widget of node.widgets) {
            // Check if this is an image widget (they typically have draw/drawWidget methods)
            if (widget._sata_patched) continue;

            // Patch the draw method if it exists
            if (widget.draw && typeof widget.draw === 'function') {
                const origDraw = widget.draw.bind(widget);
                widget.draw = function (ctx, node, widgetWidth, y, widgetHeight) {
                    if (shouldHideNow()) {
                        // Draw hidden placeholder instead
                        ctx.save();
                        ctx.fillStyle = "#1a1a1a";
                        ctx.fillRect(0, y, widgetWidth, widgetHeight);

                        ctx.fillStyle = "#888";
                        ctx.font = "12px Arial";
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        ctx.fillText("Hidden", widgetWidth / 2, y + widgetHeight / 2 - 8);
                        ctx.font = "9px Arial";
                        ctx.fillStyle = "#666";
                        ctx.fillText("(Hover to Reveal)", widgetWidth / 2, y + widgetHeight / 2 + 8);
                        ctx.restore();
                        return;
                    }
                    return origDraw(ctx, node, widgetWidth, y, widgetHeight);
                };
                widget._sata_patched = true;
            }

            // Also patch drawWidget if it exists (some widgets use this)
            if (widget.drawWidget && typeof widget.drawWidget === 'function') {
                const origDrawWidget = widget.drawWidget.bind(widget);
                widget.drawWidget = function (...args) {
                    if (shouldHideNow()) {
                        // Skip drawing - the onDrawForeground will handle the overlay
                        return;
                    }
                    return origDrawWidget(...args);
                };
                widget._sata_patched = true;
            }
        }
    };

    // Patch widgets initially and on any update
    patchWidgets();

    // Also intercept onDrawBackground to catch widget additions
    const origOnDrawBackground = node.onDrawBackground;
    node.onDrawBackground = function (ctx) {
        patchWidgets(); // Re-check for new widgets
        if (origOnDrawBackground) {
            origOnDrawBackground.apply(this, arguments);
        }
    };

    // Draw overlay in onDrawForeground as backup
    const origOnDrawForeground = node.onDrawForeground;
    node.onDrawForeground = function (ctx) {
        if (origOnDrawForeground) {
            origOnDrawForeground.apply(this, arguments);
        }

        if (shouldHideNow()) {
            ctx.save();
            ctx.fillStyle = "#1a1a1a";
            ctx.fillRect(0, 0, this.size[0], this.size[1]);

            ctx.fillStyle = "#888";
            ctx.font = "bold 14px Arial";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText("Hidden", this.size[0] / 2, this.size[1] / 2 - 10);

            ctx.font = "10px Arial";
            ctx.fillStyle = "#666";
            ctx.fillText("(Hover to Reveal)", this.size[0] / 2, this.size[1] / 2 + 10);
            ctx.restore();
        }
    };

    // Widget callback for Save_Machine
    if (node.comfyClass === SAVE_MACHINE_CLASS) {
        const hideWidget = node.widgets?.find(w => w.name === "hide_preview");
        if (hideWidget) {
            const origCallback = hideWidget.callback;
            hideWidget.callback = function (value) {
                if (origCallback) origCallback.call(this, value);
                if (app.graph) app.graph.setDirtyCanvas(true, true);
            };
        }
    }
}
