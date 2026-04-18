<script>
  import { onMount } from 'svelte';
  import DevPanel from './lib/components/DevPanel.svelte';
  import ChatPanel from './lib/components/ChatPanel.svelte';
  import ArtifactTray from './lib/components/ArtifactTray.svelte';
  import TriggerControl from './lib/components/TriggerControl.svelte';
  import ProjectSelector from './lib/components/ProjectSelector.svelte';
  import ReportViewer from './lib/components/ReportViewer.svelte';
  import StatusDot from './lib/components/StatusDot.svelte';
  import ScreenshotCapture from './lib/components/ScreenshotCapture.svelte';
  import ScreenshotSuggestion from './lib/components/ScreenshotSuggestion.svelte';

  const BACKEND = import.meta.env.VITE_BACKEND_URL || window.location.origin;

  let devPanelOpen = true;
  let activeTab = 'chat'; // 'chat' | 'screenshots' | 'files'
  let activeProject = '';
  let triggerMode = 'auto';
  let agentStatus = 'idle';
  let screenshotSuggestion = '';
  let showSuggestion = false;
  let artifacts = [];

  let session = import.meta.env.VITE_DEFAULT_SESSION || '';
  let user = 'Will';

  const gameUrls = {
    'platformer': '/games/platformer/index.html',
    'tic-tac-toe': '/games/tic-tac-toe/index.html',
  };
  $: gameSrc = gameUrls[activeProject] || Object.values(gameUrls)[0] || '';

  // Bootstrap from backend prefs
  async function bootstrap() {
    try {
      const resp = await fetch(`${BACKEND}/api/bootstrap?userId=${encodeURIComponent(user)}`);
      if (resp.ok) {
        const data = await resp.json();
        const prefs = data.result?.prefs || data.prefs || {};
        if (prefs.activeProject) activeProject = prefs.activeProject;
        if (prefs.triggerMode) triggerMode = prefs.triggerMode;
      }
    } catch (e) { /* backend may not be ready yet */ }
    // Discover default session if not set
    if (!session) {
      try {
        const sResp = await fetch(`${BACKEND}/sessions`);
        if (sResp.ok) {
          const sData = await sResp.json();
          session = sData.default || (sData.sessions && sData.sessions[0]) || '';
        }
      } catch (e) { /* ignore */ }
    }
    await loadArtifacts();
  }

  async function loadArtifacts() {
    try {
      const q = activeProject ? `?projectSlug=${encodeURIComponent(activeProject)}` : '';
      const resp = await fetch(`${BACKEND}/api/artifacts${q}`);
      if (resp.ok) {
        const data = await resp.json();
        artifacts = (data.result?.artifacts || []).map(a => ({
          id: a.id, label: a.label, path: a.path, url: a.url || '',
          filename: a.path?.split('/').pop() || '',
          status: a.status, kind: a.kind,
        }));
      }
    } catch (e) { /* backend may not be ready */ }
  }

  function handleScreenshotCaptured(e) {
    // Reload artifacts from backend after capture
    loadArtifacts();
  }

  function handleSuggestionAccept(e) {
    screenshotSuggestion = e.detail.label;
    // The ScreenshotCapture component will pick up suggestedLabel
  }

  onMount(bootstrap);
</script>

<div class="app" class:panel-open={devPanelOpen}>
  <main class="content-area">
    <iframe
      src={gameSrc}
      title="Game"
      class="game-frame"
    ></iframe>
  </main>

  {#if !devPanelOpen}
    <button class="dev-edge" on:click={() => devPanelOpen = true}>
      <StatusDot bind:status={agentStatus} backendUrl={BACKEND} {session} />
      <span class="dev-edge-label">DEV</span>
    </button>
  {/if}

  {#if devPanelOpen}
    <DevPanel>
      <div class="dev-panel-content">
        <div class="dev-panel-header">
          <div class="dev-tabs">
            <button class:active={activeTab === 'chat'} on:click={() => activeTab = 'chat'}>
              Chat <StatusDot bind:status={agentStatus} backendUrl={BACKEND} {session} />
            </button>
            <button class:active={activeTab === 'screenshots'} on:click={() => activeTab = 'screenshots'}>Screenshots</button>
            <button class:active={activeTab === 'files'} on:click={() => activeTab = 'files'}>Files</button>
          </div>
          <button class="close-panel" on:click={() => devPanelOpen = false}>×</button>
        </div>

        {#if activeTab === 'chat'}
          <ScreenshotSuggestion
            label={screenshotSuggestion}
            visible={showSuggestion}
            on:accept={handleSuggestionAccept}
            on:dismiss={() => showSuggestion = false}
          />
          <div class="chat-section">
            <ChatPanel
              backendUrl={BACKEND}
              {session}
              {user}
              agentLabel="agent"
              {triggerMode}
              on:suggest-screenshot={(e) => { screenshotSuggestion = e.detail.label; showSuggestion = true; }}
              on:save-report={async (e) => {
                try {
                  await fetch(`${BACKEND}/api/reports`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ markdown: e.detail.markdown, projectSlug: activeProject, title: `Session ${new Date().toISOString().slice(0,10)}` }),
                  });
                } catch (err) { console.error('Report save failed:', err); }
              }}
            >
              <ScreenshotCapture
                slot="input-actions"
                backendUrl={BACKEND}
                suggestedLabel={screenshotSuggestion}
                on:captured={(e) => { handleScreenshotCaptured(e); activeTab = 'screenshots'; }}
              />
            </ChatPanel>
            <div class="composer-controls">
              <TriggerControl bind:mode={triggerMode} backendUrl={BACKEND} userId={user} />
            </div>
          </div>

        {:else if activeTab === 'screenshots'}
          <div class="tab-body">
            <div class="tab-toolbar">
              <ProjectSelector bind:activeProject backendUrl={BACKEND} userId={user} on:change={() => { loadArtifacts(); }} />
              <ScreenshotCapture
                backendUrl={BACKEND}
                suggestedLabel=""
                on:captured={handleScreenshotCaptured}
              />
            </div>
            <div class="screenshot-grid">
              {#each artifacts.filter(a => a.kind === 'screenshot') as art}
                <div class="screenshot-card">
                  {#if art.path?.startsWith('/uploads/')}
                    <img src="{BACKEND}{art.path}" alt={art.label} />
                  {:else}
                    <div class="screenshot-placeholder">📷</div>
                  {/if}
                  <span class="screenshot-label">{art.label}</span>
                </div>
              {:else}
                <p class="empty-tab">No screenshots yet. Use 📷 to capture one.</p>
              {/each}
            </div>
          </div>

        {:else if activeTab === 'files'}
          <div class="tab-body">
            <div class="tab-toolbar">
              <ProjectSelector bind:activeProject backendUrl={BACKEND} userId={user} on:change={() => { loadArtifacts(); }} />
            </div>
            <div class="file-list">
              {#each artifacts as art}
                <div class="file-row">
                  <span class="file-icon">{art.kind === 'screenshot' ? '📷' : art.kind === 'code' ? '💻' : '📄'}</span>
                  <span class="file-name">{art.label}</span>
                  <span class="file-status">{art.status}</span>
                </div>
              {:else}
                <p class="empty-tab">No files or assets yet.</p>
              {/each}
            </div>
            <ReportViewer backendUrl={BACKEND} project={activeProject} />
          </div>
        {/if}
      </div>
    </DevPanel>
  {/if}
</div>

<style>
  :root {
    --bg: #0f0f0f;
    --surface: #1a1a1a;
    --border: #2a2a2a;
    --text: #e8e8e8;
    --text-dim: #888;
    --accent: #4a9eff;
    --panel-width: auto;
  }

  :global(body) {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
    font-size: 15px;
    height: 100vh;
    overflow: hidden;
  }

  .app {
    display: flex;
    height: 100vh;
    position: relative;
  }

  .app.panel-open {
    display: grid;
    grid-template-columns: 1fr auto;
  }

  .content-area {
    flex: 1;
    overflow: hidden;
    min-width: 0;
  }

  .game-frame {
    width: 100%;
    height: 100%;
    border: none;
    background: #000;
  }

  /* Edge indicator when panel is closed */
  .dev-edge {
    position: fixed;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    background: var(--surface, #1a1a1a);
    border: 1px solid var(--border, #2a2a2a);
    border-right: none;
    border-radius: 6px 0 0 6px;
    padding: 12px 6px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    z-index: 10;
    transition: background 0.15s;
  }
  .dev-edge:hover {
    background: var(--border, #2a2a2a);
  }
  .dev-edge-label {
    writing-mode: vertical-rl;
    font-size: 0.65em;
    letter-spacing: 0.15em;
    color: var(--text-dim, #888);
    font-weight: 600;
    text-transform: uppercase;
  }

  /* Panel header with tabs */
  .dev-panel-header {
    display: flex;
    align-items: center;
    border-bottom: 1px solid var(--border, #2a2a2a);
    flex-shrink: 0;
  }
  .dev-tabs {
    display: flex;
    flex: 1;
    gap: 0;
  }
  .dev-tabs button {
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-dim, #888);
    padding: 8px 12px;
    font-size: 0.8em;
    font-family: inherit;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
  }
  .dev-tabs button:hover { color: var(--text, #e8e8e8); }
  .dev-tabs button.active {
    color: var(--accent, #4a9eff);
    border-bottom-color: var(--accent, #4a9eff);
  }
  .close-panel {
    background: none;
    border: none;
    color: var(--text-dim, #888);
    font-size: 1.2em;
    cursor: pointer;
    padding: 2px 8px;
    flex-shrink: 0;
  }
  .close-panel:hover { color: var(--text, #e8e8e8); }

  .dev-panel-content {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .chat-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .composer-controls {
    padding: 4px 8px;
    border-top: 1px solid var(--border);
    flex-shrink: 0;
  }

  /* Tab body */
  .tab-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    min-height: 0;
  }
  .tab-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border, #2a2a2a);
    flex-shrink: 0;
  }
  .empty-tab {
    color: var(--text-dim, #888);
    font-style: italic;
    font-size: 0.85em;
    padding: 16px;
    text-align: center;
  }

  /* Screenshots tab */
  .screenshot-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 8px;
    padding: 8px;
  }
  .screenshot-card {
    text-align: center;
  }
  .screenshot-card img {
    width: 100%;
    aspect-ratio: 4/3;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid var(--border, #2a2a2a);
  }
  .screenshot-placeholder {
    width: 100%;
    aspect-ratio: 4/3;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6em;
    background: var(--surface, #1a1a1a);
    border-radius: 4px;
    border: 1px solid var(--border, #2a2a2a);
  }
  .screenshot-label {
    display: block;
    font-size: 0.7em;
    color: var(--text-dim, #888);
    margin-top: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Files tab */
  .file-list {
    padding: 4px 0;
  }
  .file-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    font-size: 0.85em;
    border-bottom: 1px solid var(--border, #2a2a2a);
  }
  .file-row:hover { background: rgba(255,255,255,0.03); }
  .file-icon { flex-shrink: 0; }
  .file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file-status { color: var(--text-dim, #888); font-size: 0.8em; flex-shrink: 0; }

  @media (max-width: 768px) {
    .app.panel-open {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr 40vh;
    }
  }
</style>
