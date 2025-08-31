import { app } from "../../../scripts/app.js";

app.registerExtension({
    name: "SATA_UtilityNode.PromptMachine",
    async nodeCreated(node) {
        if (node.comfyClass === "Prompt_Machine") {
            // When csv_file changes, refresh names list
            const widget = node.widgets.find(w => w.name === "csv_file");
            if (widget) {
                widget.callback = async (value) => {
                    try {
                        const resp = await fetch(`/sata/prompt_machine/names?csv=${encodeURIComponent(value)}`);
                        const data = await resp.json();
                        const names = Array.isArray(data.names) && data.names.length > 0 ? data.names : ["None"];
                        const nameWidget = node.widgets.find(w => w.name === "name");
                        if (nameWidget) {
                            if (!nameWidget.options) nameWidget.options = {};
                            nameWidget.options.values = names;
                            nameWidget.value = names[0];
                            if (typeof node.setDirtyCanvas === "function") node.setDirtyCanvas(true);
                            if (typeof node.onWidgetChanged === "function") node.onWidgetChanged(nameWidget, nameWidget.value, null, 0);
                        }
                    } catch (e) {
                        console.error("[PromptMachine] Failed to fetch names:", e);
                    }
                };
            }
        }
    }
});