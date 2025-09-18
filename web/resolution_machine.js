// resolution_machine.js
import { app } from "../../../scripts/app.js";

async function fetchConfig() {
  try {
    const resp = await fetch("/sata/resolution_machine/config");
    if (!resp.ok) {
      console.warn("ResolutionMachine: fetch failed", resp.status);
      return null;
    }
    return await resp.json();
  } catch (e) {
    console.warn("ResolutionMachine: fetch exception", e);
    return null;
  }
}

app.registerExtension({
  name: "SATA_UtilityNode.ResolutionMachine",
  async nodeCreated(node) {
    if (node.comfyClass !== "Resolution_Machine") return;

    const cfg = await fetchConfig();
    if (!cfg) return;

    // find widgets
    let modelW = node.widgets.find(w => w.name === "model");
    let resW   = node.widgets.find(w => w.name === "resolution");
    let wW     = node.widgets.find(w => w.name === "width");
    let hW     = node.widgets.find(w => w.name === "height");

    if (!modelW || !resW || !wW || !hW) {
      console.warn("ResolutionMachine: widgets missing, check INPUT_TYPES");
      return;
    }

    // --- rebuild widgets as dropdowns to force combo type ---
    const idxModel = node.widgets.indexOf(modelW);
    node.widgets.splice(idxModel, 1);
    modelW = node.addWidget("combo", "model", "None", () => {}, {
      values: cfg.models.map(m => m.model)
    });

    const idxRes = node.widgets.indexOf(resW);
    node.widgets.splice(idxRes, 1);
    resW = node.addWidget("combo", "resolution", "Custom (manual)", () => {}, {
      values: ["Custom (manual)"]
    });

    // helper lookups
    function getResNamesForModel(modelName) {
      const m = cfg.models.find(x => x.model === modelName);
      if (!m) return ["Custom (manual)"];
      const names = m.resolutions.map(r => r.name);
      if (!names.includes("Custom (manual)")) names.push("Custom (manual)");
      return names;
    }
    function findResObj(modelName, resName) {
      const m = cfg.models.find(x => x.model === modelName);
      if (!m) return null;
      return m.resolutions.find(r => r.name === resName) || null;
    }

    let suppressWH = false;
    function programmaticSetWH(wVal, hVal) {
      suppressWH = true;
      wW.value = wVal;
      hW.value = hVal;
      if (wW.inputEl) wW.inputEl.value = wVal;
      if (hW.inputEl) hW.inputEl.value = hVal;
      setTimeout(() => { suppressWH = false; }, 0);
    }

    // model handler
    modelW.callback = (newModel) => {
      const names = getResNamesForModel(newModel);
      resW.options.values = names;
      if (!names.includes(resW.value)) {
        resW.value = names[0];
      }
      resW.callback(resW.value); // trigger res change
      node.graph?.setDirtyCanvas(true);
    };

    // resolution handler
    resW.callback = (newRes) => {
      const modelName = modelW.value;
      const resObj = findResObj(modelName, newRes);
      if (resObj && newRes !== "Custom (manual)") {
        programmaticSetWH(resObj.width, resObj.height);
        if (wW.inputEl) wW.inputEl.disabled = true;
        if (hW.inputEl) hW.inputEl.disabled = true;
      } else {
        if (wW.inputEl) wW.inputEl.disabled = false;
        if (hW.inputEl) hW.inputEl.disabled = false;
      }
      node.graph?.setDirtyCanvas(true);
    };

    // manual WH handler
    function onManualWH() {
      if (suppressWH) return;
      if (resW.value !== "Custom (manual)") {
        const names = getResNamesForModel(modelW.value);
        if (!names.includes("Custom (manual)")) {
          names.push("Custom (manual)");
          resW.options.values = names;
        }
        resW.value = "Custom (manual)";
        resW.callback("Custom (manual)");
      }
    }
    wW.callback = onManualWH;
    hW.callback = onManualWH;

    // --- initialize ---
    const firstModel = cfg.models[0]?.model;
    if (firstModel) {
      modelW.value = firstModel;
      modelW.callback(firstModel);
    }
  }
});