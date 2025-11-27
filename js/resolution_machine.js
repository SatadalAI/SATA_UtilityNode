import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "SATA_UtilityNode.Resolution_Machine",

    async nodeCreated(node) {
        if (node.comfyClass !== "Resolution_Machine") return;

        // Find widgets
        const modelWidget = node.widgets.find(w => w.name === "model");
        const resolutionWidget = node.widgets.find(w => w.name === "resolution");
        const widthWidget = node.widgets.find(w => w.name === "custom_width");
        const heightWidget = node.widgets.find(w => w.name === "custom_height");

        if (!modelWidget || !resolutionWidget || !widthWidget || !heightWidget) {
            console.warn("[Resolution_Machine] Missing widgets, check backend definition.");
            return;
        }

        // Store resolution config
        let resolutionsConfig = {};

        // Fetch resolution config from backend
        async function loadConfig() {
            try {
                const resp = await fetch("/SATA_UtilityNode/resolutions_config");
                resolutionsConfig = await resp.json();
                console.log("[Resolution_Machine] Loaded config:", resolutionsConfig);
            } catch (err) {
                console.error("[Resolution_Machine] Failed to load config:", err);
            }
        }

        await loadConfig();

        // --- Utility: refresh resolution dropdown when model changes ---
        function refreshResolutions(selectedModel) {
            const available = resolutionsConfig[selectedModel]
                ? Object.keys(resolutionsConfig[selectedModel])
                : ["Custom (manual)"];

            resolutionWidget.options.values = available;

            // Pick safe default if current value is not valid
            if (!available.includes(resolutionWidget.value)) {
                resolutionWidget.value = available[0];
            }

            console.log(`[Resolution_Machine] Resolutions for ${selectedModel}:`, available);
            app.graph.change();
            applyResolution(); // auto-apply width/height on refresh
        }

        // --- Utility: apply resolution to width/height ---
        function applyResolution() {
            const selectedModel = modelWidget.value;
            const selectedResolution = resolutionWidget.value;

            if (!resolutionsConfig[selectedModel]) return;

            const resolutionData = resolutionsConfig[selectedModel][selectedResolution];

            if (selectedResolution !== "Custom (manual)" && resolutionData) {
                // Auto-set width/height
                widthWidget.value = resolutionData.width;
                heightWidget.value = resolutionData.height;

                // Lock fields
                widthWidget.disabled = true;
                heightWidget.disabled = true;
            } else {
                // Allow manual editing
                widthWidget.disabled = false;
                heightWidget.disabled = false;
            }

            app.graph.change();
        }

        // --- Preview Logic ---
        const previewWidget = node.widgets.find(w => w.name === "dimension_preview");

        function updatePreview() {
            if (!previewWidget) return;
            const w = widthWidget.value;
            const h = heightWidget.value;
            previewWidget.value = `${w} x ${h}`;
        }

        // --- Hook model change ---
        const oldModelCallback = modelWidget.callback;
        modelWidget.callback = function (value) {
            if (oldModelCallback) oldModelCallback(value);
            refreshResolutions(value);
        };

        // --- Hook resolution change ---
        const oldResolutionCallback = resolutionWidget.callback;
        resolutionWidget.callback = function (value) {
            if (oldResolutionCallback) oldResolutionCallback(value);
            applyResolution();
        };

        // Hook width/height changes for preview
        const oldWidthCallback = widthWidget.callback;
        widthWidget.callback = function (value) {
            if (oldWidthCallback) oldWidthCallback(value);
            updatePreview();
        };
        const oldHeightCallback = heightWidget.callback;
        heightWidget.callback = function (value) {
            if (oldHeightCallback) oldHeightCallback(value);
            updatePreview();
        };

        // --- Add Swap Button ---
        node.addWidget("button", "Swap Dimensions", null, () => {
            const w = widthWidget.value;
            const h = heightWidget.value;

            // Swap values
            widthWidget.value = h;
            heightWidget.value = w;

            // Force "Custom (manual)" to prevent preset overwrite
            if (resolutionWidget.value !== "Custom (manual)") {
                // Check if "Custom (manual)" exists in options
                if (!resolutionWidget.options.values.includes("Custom (manual)")) {
                    resolutionWidget.options.values.push("Custom (manual)");
                }
                resolutionWidget.value = "Custom (manual)";

                // Unlock widgets since we are now in custom mode
                widthWidget.disabled = false;
                heightWidget.disabled = false;
            }

            updatePreview();
            app.graph.change();
        });

        // --- Initial sync ---
        refreshResolutions(modelWidget.value);
        updatePreview();
    }
});