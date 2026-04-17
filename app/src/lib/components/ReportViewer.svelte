<script>
  export let backendUrl = '';
  export let project = '';

  let reportContent = '';
  let visible = false;
  // Will load from backend later
</script>

{#if visible}
  <div class="report-viewer">
    <div class="report-header">
      <span>Session Report</span>
      <button on:click={() => visible = false}>×</button>
    </div>
    <div class="report-body">
      {#if reportContent}
        <div class="report-markdown">{reportContent}</div>
      {:else}
        <p class="empty">No report yet. Ask the agent to generate one.</p>
      {/if}
    </div>
  </div>
{:else}
  <button class="report-toggle" on:click={() => visible = true}>
    📄 Report
  </button>
{/if}

<style>
  .report-toggle {
    background: none;
    border: 1px solid var(--border, #2a2a2a);
    color: var(--text-dim, #888);
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8em;
    margin: 8px;
    flex-shrink: 0;
  }
  .report-viewer {
    border-top: 1px solid var(--border, #2a2a2a);
    flex-shrink: 0;
    max-height: 40%;
    overflow-y: auto;
  }
  .report-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 8px;
    font-size: 0.85em;
    color: var(--text-dim, #888);
    border-bottom: 1px solid var(--border, #2a2a2a);
  }
  .report-header button {
    background: none;
    border: none;
    color: var(--text-dim, #888);
    cursor: pointer;
    font-size: 1em;
  }
  .report-body {
    padding: 8px;
    font-size: 0.85em;
    line-height: 1.5;
  }
  .empty {
    color: var(--text-dim, #888);
    font-style: italic;
  }
</style>
