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

        // --- Hook model change ---
        const oldModelCallback = modelWidget.callback;
        modelWidget.callback = function(value) {
            if (oldModelCallback) oldModelCallback(value);
            refreshResolutions(value);
        };

        // --- Hook resolution change ---
        const oldResolutionCallback = resolutionWidget.callback;
        resolutionWidget.callback = function(value) {
            if (oldResolutionCallback) oldResolutionCallback(value);
            applyResolution();
        };

        // --- Initial sync ---
        refreshResolutions(modelWidget.value);
    }
});