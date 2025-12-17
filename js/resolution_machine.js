import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "SATA_UtilityNode.Resolution_Machine",

    async nodeCreated(node) {
        if (node.comfyClass !== "Resolution_Machine") return;

        // Find widgets
        const modelWidget = node.widgets.find(w => w.name === "model");
        const dimensionWidget = node.widgets.find(w => w.name === "dimension");
        const resolutionWidget = node.widgets.find(w => w.name === "resolution");
        const widthWidget = node.widgets.find(w => w.name === "custom_width");
        const heightWidget = node.widgets.find(w => w.name === "custom_height");

        if (!modelWidget || !dimensionWidget || !resolutionWidget || !widthWidget || !heightWidget) {
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

            } catch (err) {
                console.error("[Resolution_Machine] Failed to load config:", err);
            }
        }

        await loadConfig();

        // --- Utility: refresh resolution dropdown when model/dimension changes ---
        function refreshResolutions() {
            const selectedModel = modelWidget.value;
            const selectedDimension = dimensionWidget.value;

            let available = [];

            if (resolutionsConfig.models && resolutionsConfig.models[selectedModel]) {
                const buckets = resolutionsConfig.models[selectedModel];
                buckets.forEach(bucket => {
                    // Check if bucket exists and has the selected dimension
                    if (resolutionsConfig.resolutions && resolutionsConfig.resolutions[bucket] && resolutionsConfig.resolutions[bucket][selectedDimension]) {
                        available.push(...Object.keys(resolutionsConfig.resolutions[bucket][selectedDimension]));
                    }
                });
            }

            // Always add Custom? Or only via button? The plan implies button adds it or it is a fallback.
            // But if user wants to select custom again after selecting a preset?
            // "Custom" option should probably be always available or injected.
            // Let's keep it clean: presets only. Button forces custom mode.
            // BUT if we want to get out of custom mode, we select a preset.
            // If we are in custom mode, "Custom" should be in the list?

            if (available.length === 0) {
                available.push("Custom");
            }

            // Preserve "Custom" if it was already there/selected? 
            // Better to re-build list cleanly.

            resolutionWidget.options.values = available;

            // Pick safe default if current value is not valid
            if (!available.includes(resolutionWidget.value)) {
                resolutionWidget.value = available[0];
            }

            // If we switched to a preset (not Custom), lock fields
            // If we defaulted to Custom (e.g. empty available), unlock
            checkCustomMode();
        }

        function checkCustomMode() {
            if (resolutionWidget.value === "Custom") {
                widthWidget.disabled = false;
                heightWidget.disabled = false;
            } else {
                // Check if selected is actually a preset
                applyResolutionPreset();
            }
            app.graph.change();
        }

        // --- Utility: apply resolution preset to width/height ---
        function applyResolutionPreset() {
            const selectedModel = modelWidget.value;
            const selectedDimension = dimensionWidget.value;
            const selectedResolution = resolutionWidget.value;

            if (selectedResolution === "Custom") {
                widthWidget.disabled = false;
                heightWidget.disabled = false;
                return;
            }

            let resolutionData = null;

            // Lookup
            if (resolutionsConfig.models && resolutionsConfig.models[selectedModel]) {
                const buckets = resolutionsConfig.models[selectedModel];
                for (const bucket of buckets) {
                    if (resolutionsConfig.resolutions[bucket] &&
                        resolutionsConfig.resolutions[bucket][selectedDimension] &&
                        resolutionsConfig.resolutions[bucket][selectedDimension][selectedResolution]) {

                        resolutionData = resolutionsConfig.resolutions[bucket][selectedDimension][selectedResolution];
                        break;
                    }
                }
            }

            if (resolutionData) {
                widthWidget.value = resolutionData.width;
                heightWidget.value = resolutionData.height;
                widthWidget.disabled = true;
                heightWidget.disabled = true;
            } else {
                // Should not happen if list logic is correct, unless race condition
                // fallback
                widthWidget.disabled = false;
                heightWidget.disabled = false;
            }
        }

        // --- Hook model change ---
        const oldModelCallback = modelWidget.callback;
        modelWidget.callback = function (value) {
            if (oldModelCallback) oldModelCallback(value);
            refreshResolutions();
        };

        // --- Hook dimension change ---
        const oldDimensionCallback = dimensionWidget.callback;
        dimensionWidget.callback = function (value) {
            if (oldDimensionCallback) oldDimensionCallback(value);
            refreshResolutions();
        };

        // --- Hook resolution change ---
        const oldResolutionCallback = resolutionWidget.callback;
        resolutionWidget.callback = function (value) {
            if (oldResolutionCallback) oldResolutionCallback(value);
            checkCustomMode();
        };

        // --- Add Custom Button ---
        // Rename "Swap Dimensions" -> "Custom"
        // Note: Node logic adds this button. Previous JS added it. We are replacing previous JS logic.

        node.addWidget("button", "Custom", null, () => {
            // Unlock widgets
            widthWidget.disabled = false;
            heightWidget.disabled = false;

            // Ensure "Custom" option exists and is selected
            if (!resolutionWidget.options.values.includes("Custom")) {
                resolutionWidget.options.values.push("Custom");
            }
            resolutionWidget.value = "Custom";

            app.graph.change();
        });

        // --- Initial sync ---
        refreshResolutions();
    }
});