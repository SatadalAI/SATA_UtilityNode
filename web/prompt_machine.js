// prompt_machine_frontend.js
import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "SATA_UtilityNode.PromptMachineFrontend",
    async nodeCreated(node) {
        if (node.comfyClass !== "Prompt_Machine") return;

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

        // Add proper dropdown
        const nameWidget = node.addWidget("combo", "name", "None", () => {}, {
            values: ["None"]
        });

        // Store available names
        let namesConfig = [];

        // Fetch names from backend for a given CSV
        async function loadNames(csvValue) {
            if (!csvValue) return;
            try {
                const resp = await fetch(`/sata/prompt_machine/names?csv=${encodeURIComponent(csvValue)}`);
                const data = await resp.json();
                namesConfig = data.names || ["None"];
                console.log("[PromptMachineFrontend] Loaded names:", namesConfig);
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

            app.graph.change();
        }

        // Hook CSV change
        const oldCsvCallback = csvWidget.callback;
        csvWidget.callback = function(value) {
            if (oldCsvCallback) oldCsvCallback(value);
            loadNames(value); // refresh dynamically
        };

        // Initial sync
        loadNames(csvWidget.value);
    }
});