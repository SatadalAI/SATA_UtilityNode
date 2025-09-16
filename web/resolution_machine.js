// resolution_machine.js
import { app } from "../../../scripts/app.js";

async function fetchConfig() {
  try {
    const resp = await fetch("/sata/resolution_machine/config");
    if (!resp.ok) {
      console.warn("ResolutionMachine: fetch failed", resp.status);
      return null;
    }
    const json = await resp.json();
    return json;
  } catch (e) {
    console.warn("ResolutionMachine: fetch exception", e);
    return null;
  }
}

/* cross-version widget helpers */
function setComboOptions(widget, options) {
  if (!widget) return;
  if (typeof widget.setOptions === "function") {
    widget.setOptions(options);
    return;
  }
  if (widget.options && Object.prototype.hasOwnProperty.call(widget.options, "values")) {
    widget.options.values = options;
    return;
  }
  widget.options = { values: options };
}
function setWidgetValue(widget, v) {
  if (!widget) return;
  if (typeof widget.setValue === "function") return widget.setValue(v);
  if (typeof widget.value === "function") return widget.value(v);
  widget.value = v;
}
function getWidgetValue(widget) {
  if (!widget) return undefined;
  if (typeof widget.value === "function") return widget.value();
  return widget.value;
}
function triggerWidgetChange(widget, value) {
  // call onChange or callback if present to simulate user selection
  if (!widget) return;
  if (typeof widget.onChange === "function") {
    try { widget.onChange(value); return; } catch (e) { /* continue */ }
  }
  if (typeof widget.callback === "function") {
    try { widget.callback(value); return; } catch (e) { /* continue */ }
  }
  // fallback: set value
  setWidgetValue(widget, value);
}

/* attach handler in tolerant way */
function attachHandler(widget, node, handler) {
  if (!widget) return;
  if (typeof widget.onChange === "function") {
    widget.onChange(handler);
    return;
  }
  // preserve existing callback if present
  const orig = widget.callback;
  widget.callback = function (v) {
    try { if (orig) orig.call(node, v); } catch (e) { /* ignore */ }
    try { handler(v); } catch (e) { console.warn("handler error", e); }
  };
}

app.registerExtension({
  name: "SATA_UtilityNode.ResolutionMachine",
  async nodeCreated(node) {
    if (node.comfyClass !== "Resolution_Machine") return;

    const modelW = node.widgets.find(w => w.name === "model");
    const resW = node.widgets.find(w => w.name === "resolution");
    const wW = node.widgets.find(w => w.name === "width");
    const hW = node.widgets.find(w => w.name === "height");

    console.log("ResolutionMachine nodeCreated widgets:", { modelW, resW, wW, hW });

    if (!modelW || !resW || !wW || !hW) {
      console.warn("ResolutionMachine: missing widgets - ensure backend's INPUT_TYPES exposes model,resolution,width,height");
      return;
    }

    const cfg = await fetchConfig();
    if (!cfg) {
      console.warn("ResolutionMachine: no config received from backend");
      return;
    }

    const models = cfg.models.map(m => m.model);
    if (models.length > 0) setComboOptions(modelW, models);

    // helper to get resolution list for a model (ensures Custom present)
    function getResNamesForModel(modelName) {
      const m = cfg.models.find(x => x.model === modelName);
      if (!m) return ["Custom (manual)"];
      const names = m.resolutions.map(r => r.name.slice()); // copy
      if (!names.includes("Custom (manual)")) names.push("Custom (manual)");
      return names;
    }

    // helper to find resolution object
    function findResObj(modelName, resName) {
      const m = cfg.models.find(x => x.model === modelName);
      if (!m) return null;
      return m.resolutions.find(r => r.name === resName) || null;
    }

    // guard to avoid manual-edit handler firing during programmatic updates
    let suppressManualWH = false;
    function programmaticSetWH(wVal, hVal) {
      suppressManualWH = true;
      setWidgetValue(wW, wVal);
      setWidgetValue(hW, hVal);
      if (wW.inputEl) wW.inputEl.value = wVal;
      if (hW.inputEl) hW.inputEl.value = hVal;
      // clear suppression on next tick
      setTimeout(() => { suppressManualWH = false; }, 0);
    }

    // Model change handler: update resolution options and pick first preset
    const onModelChange = (newModel) => {
      try {
        const names = getResNamesForModel(newModel);
        setComboOptions(resW, names);

        // pick first non-custom if available
        const pick = names[0] || "Custom (manual)";
        setWidgetValue(resW, pick);
        // call resolution handler (simulate user selection)
        triggerWidgetChange(resW, pick);

        // ensure node re-validation / UI update
        try { node.setDirtyCanvas(true, true); } catch (e) { try { node.setDirtyCanvas(true); } catch(e){} }
      } catch (e) {
        console.warn("ResolutionMachine: onModelChange error", e);
      }
    };

    // Resolution change handler: set width/height for presets, lock/unlock inputs accordingly
    const onResolutionChange = (newRes) => {
      try {
        const modelName = getWidgetValue(modelW);
        const resObj = findResObj(modelName, newRes);
        if (resObj && newRes !== "Custom (manual)") {
          programmaticSetWH(resObj.width, resObj.height);
          // Lock width/height
          if (wW.inputEl) wW.inputEl.disabled = true;
          if (hW.inputEl) hW.inputEl.disabled = true;
        } else {
          // Custom: allow manual edits
          if (wW.inputEl) wW.inputEl.disabled = false;
          if (hW.inputEl) hW.inputEl.disabled = false;
        }
        try { node.setDirtyCanvas(true, true); } catch (e) { try { node.setDirtyCanvas(true); } catch(e){} }
      } catch (e) {
        console.warn("ResolutionMachine: onResolutionChange error", e);
      }
    };

    // Manual width/height change handler: set resolution to Custom (manual)
    const onManualWH = (_newVal) => {
      if (suppressManualWH) return;
      try {
        const cur = getWidgetValue(resW);
        if (cur !== "Custom (manual)") {
          const names = getResNamesForModel(getWidgetValue(modelW));
          if (!names.includes("Custom (manual)")) {
            names.push("Custom (manual)");
            setComboOptions(resW, names);
          }
          setWidgetValue(resW, "Custom (manual)");
          try { triggerWidgetChange(resW, "Custom (manual)"); } catch(e){}
          try { node.setDirtyCanvas(true, true); } catch (e) { try { node.setDirtyCanvas(true); } catch(e){} }
        }
      } catch (e) {
        console.warn("ResolutionMachine: onManualWH error", e);
      }
    };

    // Attach handlers (tolerant)
    attachHandler(modelW, node, onModelChange);
    attachHandler(resW, node, onResolutionChange);
    attachHandler(wW, node, onManualWH);
    attachHandler(hW, node, onManualWH);

    // Initialize model + resolution UI
    const initialModel = getWidgetValue(modelW) || (models.length ? models[0] : undefined);
    if (initialModel) {
      setWidgetValue(modelW, initialModel);
      // ensure options & width/height set for initial model
      onModelChange(initialModel);
    }
  }
});