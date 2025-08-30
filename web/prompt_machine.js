import { app } from "/scripts/app.js";

const CSV_ENDPOINTS = [
  "/sata/prompt_machine/csvs",
  "/custom/SATA_UtilityNode/prompt_machine/csvs",
  "/custom/SATA_UtilityNode/list_csv"
];

const NAMES_ENDPOINTS = [
  "/sata/prompt_machine/names",
  "/custom/SATA_UtilityNode/prompt_machine/names",
  "/custom/SATA_UtilityNode/list_names"
];

async function tryFetchJson(endpoints, query = "") {
  for (const ep of endpoints) {
    try {
      const url = query ? `${ep}?${query}` : ep;
      const res = await fetch(url, { cache: "no-cache" });
      if (!res.ok) continue;
      const json = await res.json();
      // Accept either {"items": [...]} or plain [...]
      if (Array.isArray(json)) {
        return json;
      }
      if (json && Array.isArray(json.items)) {
        return json.items;
      }
    } catch (e) {
      // try next endpoint
    }
  }
  return [];
}

app.registerExtension({
  name: "SATA_PromptMachine_AutoRefresh",
  nodeCreated(node) {
    if (node.comfyClass !== "Prompt_Machine") return;

    const csvWidget = node.widgets?.find(w => w.name === "csv_file");
    const nameWidget = node.widgets?.find(w => w.name === "name");
    if (!csvWidget || !nameWidget) return;

    // initial load of CSV filenames, then names for first CSV
    (async () => {
      const csvs = await tryFetchJson(CSV_ENDPOINTS);
      if (csvs.length > 0) {
        csvWidget.options = csvs;
        if (!csvs.includes(csvWidget.value)) csvWidget.value = csvs[0];
        const names = await tryFetchJson(NAMES_ENDPOINTS, `csv=${encodeURIComponent(csvWidget.value)}`);
        nameWidget.options = names.length ? names : ["None"];
        if (!nameWidget.options.includes(nameWidget.value)) nameWidget.value = nameWidget.options[0];
        app.graph.setDirtyCanvas(true, true);
      }
    })();

    // when CSV selection changes -> refresh names
    const prev = csvWidget.callback;
    csvWidget.callback = function() {
      if (prev) prev.apply(this, arguments);
      // small delay so value is updated in widget
      setTimeout(async () => {
        const names = await tryFetchJson(NAMES_ENDPOINTS, `csv=${encodeURIComponent(csvWidget.value)}`);
        nameWidget.options = names.length ? names : ["None"];
        if (!nameWidget.options.includes(nameWidget.value)) nameWidget.value = nameWidget.options[0];
        app.graph.setDirtyCanvas(true, true);
      }, 20);
    };
  }
});