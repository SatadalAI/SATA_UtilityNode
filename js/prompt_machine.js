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
        const nameWidget = node.addWidget("combo", "name", "None", () => { }, {
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
        const posPreview = node.widgets.find(w => w.name === "positive_preview");
        const negPreview = node.widgets.find(w => w.name === "negative_preview");
        const notePreview = node.widgets.find(w => w.name === "note_preview");

        async function updatePreviews(name) {
            const csv = csvWidget.value;
            if (!csv || !name || name === "None") return;

            try {
                const resp = await fetch(`/sata/prompt_machine/get?csv=${encodeURIComponent(csv)}&name=${encodeURIComponent(name)}`);
                const data = await resp.json();

                if (posPreview) posPreview.value = data.positive || "";
                if (negPreview) negPreview.value = data.negative || "";
                if (notePreview) notePreview.value = data.note || "";

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