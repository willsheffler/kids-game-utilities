<script>
  // DevPanel: collapsible side panel container for dev tools
</script>

<aside class="dev-panel">
  <slot />
</aside>

<style>
  .dev-panel {
    background: var(--surface, #1a1a1a);
    border-left: 1px solid var(--border, #2a2a2a);
    height: 100%;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  }
</style>
