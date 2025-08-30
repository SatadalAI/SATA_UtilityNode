/**
 * Enhanced smooth scrolling and zooming for touchpad gestures
 * Overrides LGraphCanvas.prototype.processMouseWheel
 */
LGraphCanvas.prototype.processMouseWheel = function (/** @type {WheelEvent} */ event) {
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