<script>
  let panelWidth = parseInt(localStorage.getItem('devPanelWidth') || '380');
  let dragging = false;

  function onPointerDown(e) {
    dragging = true;
    e.target.setPointerCapture(e.pointerId);
  }

  function onPointerMove(e) {
    if (!dragging) return;
    const newWidth = window.innerWidth - e.clientX;
    panelWidth = Math.max(240, Math.min(newWidth, window.innerWidth * 0.7));
  }

  function onPointerUp() {
    if (!dragging) return;
    dragging = false;
    localStorage.setItem('devPanelWidth', String(Math.round(panelWidth)));
  }
</script>

<aside class="dev-panel" style="width: {panelWidth}px">
  <div
    class="resize-handle"
    class:active={dragging}
    on:pointerdown={onPointerDown}
    on:pointermove={onPointerMove}
    on:pointerup={onPointerUp}
  ></div>
  <div class="dev-panel-inner">
    <slot />
  </div>
</aside>

<style>
  .dev-panel {
    background: var(--surface, #1a1a1a);
    border-left: 1px solid var(--border, #2a2a2a);
    height: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: row;
    position: relative;
  }
  .dev-panel-inner {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    overflow: hidden;
  }
  .resize-handle {
    width: 5px;
    cursor: col-resize;
    flex-shrink: 0;
    background: transparent;
    transition: background 0.15s;
  }
  .resize-handle:hover,
  .resize-handle.active {
    background: var(--accent, #4a9eff);
  }
</style>
