import { app } from "../../../scripts/app.js";

const SETTING_ID = "SATA.EnableTouchpadPanZoom";

app.registerExtension({
    name: "SATA_UtilityNode.TouchpadPanZoom",
    settings: [
        {
            id: SETTING_ID,
            name: "Enable Touchpad Pan/Zoom (SATA UtilityNode)",
            type: "boolean",
            defaultValue: true,
            onChange: (value) => {
                const btn = document.getElementById("sata-touchpad-toggle-btn");
                if (btn) {
                    btn.textContent = value ? "Touchpad: ON" : "Touchpad: OFF";
                    btn.style.opacity = value ? "1.0" : "0.5";
                }
            }
        }
    ],
    async setup() {
        // Create a toggle button in the ComfyUI menu
        const menu = document.querySelector(".comfy-menu");
        if (menu) {
            const toggleBtn = document.createElement("button");
            toggleBtn.id = "sata-touchpad-toggle-btn";
            
            // Function to get current value securely
            const getVal = () => {
                if (app.extensionManager && app.extensionManager.setting) {
                    const val = app.extensionManager.setting.get(SETTING_ID);
                    return val !== undefined ? val : true;
                } else if (app.ui && app.ui.settings) {
                    return app.ui.settings.getSettingValue(SETTING_ID, true);
                }
                return true;
            };

            // Function to set value
            const setVal = (newVal) => {
                if (app.extensionManager && app.extensionManager.setting) {
                    app.extensionManager.setting.set(SETTING_ID, newVal);
                } else if (app.ui && app.ui.settings) {
                    app.ui.settings.setSettingValue(SETTING_ID, newVal);
                }
                // Update button visuals
                toggleBtn.textContent = newVal ? "Touchpad: ON" : "Touchpad: OFF";
                toggleBtn.style.opacity = newVal ? "1.0" : "0.5";
            };

            const initialVal = getVal();
            toggleBtn.textContent = initialVal ? "Touchpad: ON" : "Touchpad: OFF";
            toggleBtn.style.opacity = initialVal ? "1.0" : "0.5";

            // Basic styling to match comfy UI buttons if classes aren't enough
            toggleBtn.className = "comfy-settings-btn"; 
            
            toggleBtn.onclick = () => {
                const currentVal = getVal();
                setVal(!currentVal);
            };

            // Try to place it nicely in the menu
            const settingsBtn = document.getElementById("comfy-settings-button");
            if (settingsBtn && settingsBtn.parentNode === menu) {
                menu.insertBefore(toggleBtn, settingsBtn);
            } else {
                menu.appendChild(toggleBtn);
            }
        }
    }
});

/**
 * Enhanced smooth scrolling and zooming for touchpad gestures
 * Overrides LGraphCanvas.prototype.processMouseWheel
 */
const originalProcessMouseWheel = LGraphCanvas.prototype.processMouseWheel;

LGraphCanvas.prototype.processMouseWheel = function (/** @type {WheelEvent} */ event) {
  let isEnabled = true;
  
  if (app.extensionManager && app.extensionManager.setting) {
      const val = app.extensionManager.setting.get(SETTING_ID);
      if (val !== undefined) isEnabled = val;
  } else if (app.ui && app.ui.settings) {
      isEnabled = app.ui.settings.getSettingValue(SETTING_ID, true);
  }

  if (isEnabled === false) {
      if (originalProcessMouseWheel) {
          return originalProcessMouseWheel.apply(this, arguments);
      }
      return false;
  }

  if (!this.graph || !this.allow_dragcanvas) return;

  const { clientX: x, clientY: y, deltaX, deltaY, ctrlKey, metaKey } = event;

  // Check if the event occurred inside the canvas viewport
  if (this.viewport) {
    const [vx, vy, vw, vh] = this.viewport;
    const insideX = x >= vx && x < vx + vw;
    const insideY = y >= vy && y < vy + vh;
    if (!(insideX && insideY)) return;
  }

  const currentScale = this.ds.scale;

  // Configurable sensitivity
  const ZOOM_SENSITIVITY = this.zoomSensitivity || 0.005;
  const PAN_SENSITIVITY = this.panSensitivity || 1.0;
  const MIN_SCALE = 0.1;
  const MAX_SCALE = 4.0;

  if (ctrlKey || metaKey) {
    // Zoom mode
    const zoomDirection = Math.sign(deltaY);
    const zoomAmount = zoomDirection * Math.abs(deltaY) * ZOOM_SENSITIVITY;
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, currentScale - zoomAmount));
    this.ds.changeScale(newScale, [x, y]);
  } else {
    // Pan mode
    this.ds.mouseDrag(-deltaX * PAN_SENSITIVITY, -deltaY * PAN_SENSITIVITY);
  }

  this.graph.change();
  event.preventDefault();
  return false;
};