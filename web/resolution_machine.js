import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ResolutionMachine",
    async nodeCreated(node) {
        if (node.comfyClass !== "Resolution_Machine") return;

        console.log("ResolutionMachine nodeCreated widgets:", node.widgets);

        const resWidget = node.widgets.find(w => w.name === "resolution");
        const widthWidget = node.widgets.find(w => w.name === "width");
        const heightWidget = node.widgets.find(w => w.name === "height");

        if (!resWidget || !widthWidget || !heightWidget) {
            console.error("ResolutionMachine: missing widget(s)");
            return;
        }

        // Hook resolution dropdown change
        const origCallback = resWidget.callback;
        resWidget.callback = function(value) {
            if (origCallback) origCallback(value);

            if (value !== "Custom") {
                try {
                    const [w, h] = value.split("x").map(v => parseInt(v));
                    widthWidget.value = w;
                    heightWidget.value = h;
                    if (widthWidget.inputEl) widthWidget.inputEl.value = w;
                    if (heightWidget.inputEl) heightWidget.inputEl.value = h;
                } catch (e) {
                    console.warn("ResolutionMachine: parse error", e);
                }
            }
        };
    }
});
