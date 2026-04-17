<script>
  import { onMount, onDestroy } from 'svelte';

  export let backendUrl = '';
  export let project = '';

  let reports = [];
  let activeReport = null;
  let visible = false;
  let refreshTimer;

  async function loadReports() {
    try {
      const q = project ? `?projectSlug=${encodeURIComponent(project)}` : '';
      const resp = await fetch(`${backendUrl}/api/reports${q}`);
      if (resp.ok) {
        const data = await resp.json();
        reports = data.result?.reports || [];
        if (reports.length > 0 && !activeReport) {
          activeReport = reports[reports.length - 1];
        }
      }
    } catch (e) { /* backend may not be ready */ }
  }

  async function refreshActiveReport() {
    if (!activeReport?.id) return;
    try {
      const resp = await fetch(`${backendUrl}/api/reports/${activeReport.id}`);
      if (resp.ok) {
        const data = await resp.json();
        activeReport = data.result?.report || activeReport;
      }
    } catch (e) { /* ignore */ }
  }

  function toggleVisible() {
    visible = !visible;
    if (visible && reports.length === 0) loadReports();
  }

  onMount(() => {
    refreshTimer = setInterval(() => {
      if (visible && activeReport) refreshActiveReport();
    }, 5000);
  });

  onDestroy(() => {
    if (refreshTimer) clearInterval(refreshTimer);
  });
</script>

{#if visible}
  <div class="report-viewer">
    <div class="report-header">
      <select class="report-select" on:change={(e) => {
        activeReport = reports.find(r => r.id === e.target.value) || null;
      }}>
        {#each reports as r}
          <option value={r.id} selected={r.id === activeReport?.id}>{r.title}</option>
        {/each}
      </select>
      <button class="refresh-btn" on:click={refreshActiveReport}>↻</button>
      <button class="close-btn" on:click={() => visible = false}>×</button>
    </div>
    <div class="report-body">
      {#if activeReport?.markdown}
        <pre class="report-markdown">{activeReport.markdown}</pre>
      {:else if reports.length === 0}
        <p class="empty">No reports yet. Ask the agent to generate one.</p>
      {:else}
        <p class="empty">Select a report above.</p>
      {/if}
    </div>
  </div>
{:else}
  <button class="report-toggle" on:click={toggleVisible}>
    📄 Report {reports.length > 0 ? `(${reports.length})` : ''}
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
    display: flex;
    flex-direction: column;
  }
  .report-header {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-bottom: 1px solid var(--border, #2a2a2a);
    flex-shrink: 0;
  }
  .report-select {
    flex: 1;
    background: var(--bg, #0f0f0f);
    color: var(--text, #e8e8e8);
    border: 1px solid var(--border, #2a2a2a);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.8em;
    font-family: inherit;
  }
  .refresh-btn, .close-btn {
    background: none;
    border: none;
    color: var(--text-dim, #888);
    cursor: pointer;
    font-size: 1em;
    padding: 2px 4px;
  }
  .report-body {
    padding: 8px;
    font-size: 0.8em;
    line-height: 1.6;
    overflow-y: auto;
    flex: 1;
  }
  .report-markdown {
    white-space: pre-wrap;
    font-family: inherit;
    color: var(--text, #e8e8e8);
    margin: 0;
  }
  .empty {
    color: var(--text-dim, #888);
    font-style: italic;
  }
</style>
