<script>
  import { onMount, onDestroy, afterUpdate } from 'svelte';
  import { marked } from 'marked';

  export let backendUrl = '';
  export let project = '';

  let reports = [];
  let activeReport = null;
  let visible = false;
  let refreshTimer;
  let lastProject = project;

  // Reload reports when project prop changes while viewer is open
  $: if (project !== lastProject) {
    lastProject = project;
    if (visible) {
      activeReport = null;
      loadReports();
    }
  }

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
        <div class="report-markdown">{@html marked(activeReport.markdown || '')}</div>
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
    color: var(--text, #e8e8e8);
    margin: 0;
  }
  .report-markdown :global(h1),
  .report-markdown :global(h2),
  .report-markdown :global(h3) {
    margin: 0.6em 0 0.3em;
    font-weight: 600;
  }
  .report-markdown :global(h1) { font-size: 1.2em; }
  .report-markdown :global(h2) { font-size: 1.05em; }
  .report-markdown :global(h3) { font-size: 0.95em; }
  .report-markdown :global(ul),
  .report-markdown :global(ol) {
    padding-left: 1.4em;
    margin: 0.4em 0;
  }
  .report-markdown :global(p) {
    margin: 0.4em 0;
  }
  .report-markdown :global(img) {
    max-width: 100%;
    border-radius: 4px;
    margin: 0.4em 0;
  }
  .report-markdown :global(code) {
    background: rgba(255,255,255,0.08);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 0.9em;
  }
  .report-markdown :global(pre) {
    background: rgba(255,255,255,0.06);
    padding: 8px;
    border-radius: 4px;
    overflow-x: auto;
    margin: 0.4em 0;
  }
  .empty {
    color: var(--text-dim, #888);
    font-style: italic;
  }
</style>
