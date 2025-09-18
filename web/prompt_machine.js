// prompt_machine_frontend.js
import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "SATA_UtilityNode.PromptMachineFrontend",
    async nodeCreated(node) {
        if (node.comfyClass !== "Prompt_Machine") return;

        let csvWidget = node.widgets.find(w => w.name === "csv_file");
        let oldNameWidget = node.widgets.find(w => w.name === "name");

        if (!csvWidget || !oldNameWidget) {
            console.warn("[PromptMachineFrontend] widgets not found");
            return;
        }

        // Remove the old STRING widget
        const index = node.widgets.indexOf(oldNameWidget);
        node.widgets.splice(index, 1);

        // Add a proper dropdown instead
        let nameWidget = node.addWidget("combo", "name", "None", () => {}, {
            values: ["None"]
        });

        async function refreshNames(csvValue) {
            try {
                const res = await fetch(`/sata/prompt_machine/names?csv=${encodeURIComponent(csvValue)}`);
                const data = await res.json();
                const names = data.names || ["None"];

                nameWidget.options.values = names;
                if (!names.includes(nameWidget.value)) {
                    nameWidget.value = names[0];
                }

                if (node.graph) node.graph.setDirtyCanvas(true);
                console.log("[PromptMachineFrontend] refreshed names:", names);
            } catch (err) {
                console.error("[PromptMachineFrontend] error fetching names:", err);
            }
        }

        // Initial load
        refreshNames(csvWidget.value);

        // Reload names when CSV changes
        const originalCsvCallback = csvWidget.callback;
        csvWidget.callback = (value) => {
            refreshNames(value);
            if (originalCsvCallback) originalCsvCallback(value);
        };
    }
});