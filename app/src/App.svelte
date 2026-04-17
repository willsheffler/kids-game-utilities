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
  let activeProject = '';
  let triggerMode = 'auto';
  let agentStatus = 'idle';
  let screenshotSuggestion = '';
  let showSuggestion = false;
  let artifacts = [];

  let session = import.meta.env.VITE_DEFAULT_SESSION || '';
  let user = 'Will';

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
          id: a.id, label: a.label, path: a.path, filename: a.path?.split('/').pop() || '',
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
  <header class="app-header">
    <div class="header-left">
      <ProjectSelector bind:activeProject backendUrl={BACKEND} />
      <StatusDot bind:status={agentStatus} backendUrl={BACKEND} {session} />
    </div>
    <button class="toggle-panel" on:click={() => devPanelOpen = !devPanelOpen}>
      {devPanelOpen ? '→' : '←'} Dev
    </button>
  </header>

  <main class="content-area">
    <div class="placeholder-content">
      <p>Game / app content goes here</p>
      <p style="color: var(--text-dim); font-size: 0.85em;">Replace this with your app component</p>
    </div>
  </main>

  {#if devPanelOpen}
    <DevPanel>
      <div class="dev-panel-content">
        <ScreenshotSuggestion
          label={screenshotSuggestion}
          visible={showSuggestion}
          on:accept={handleSuggestionAccept}
          on:dismiss={() => showSuggestion = false}
        />
        <ArtifactTray backendUrl={BACKEND} project={activeProject} {artifacts} />

        <div class="chat-section">
          <ChatPanel
            backendUrl={BACKEND}
            {session}
            {user}
            agentLabel="agent"
          />
          <div class="composer-controls">
            <ScreenshotCapture
              backendUrl={BACKEND}
              suggestedLabel={screenshotSuggestion}
              on:captured={handleScreenshotCaptured}
            />
            <TriggerControl bind:mode={triggerMode} backendUrl={BACKEND} userId={user} />
          </div>
        </div>

        <ReportViewer backendUrl={BACKEND} project={activeProject} />
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
    --panel-width: 380px;
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
    flex-direction: column;
    height: 100vh;
  }

  .app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 16px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
    background: var(--surface);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .toggle-panel {
    background: none;
    border: 1px solid var(--border);
    color: var(--text-dim);
    padding: 4px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85em;
  }
  .toggle-panel:hover {
    border-color: var(--accent);
    color: var(--text);
  }

  .app.panel-open {
    display: grid;
    grid-template-columns: 1fr var(--panel-width);
    grid-template-rows: auto 1fr;
  }
  .app.panel-open .app-header {
    grid-column: 1 / -1;
  }

  .content-area {
    flex: 1;
    overflow: auto;
    padding: 16px;
  }

  .placeholder-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-dim);
    gap: 8px;
  }

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

  @media (max-width: 768px) {
    .app.panel-open {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr 40vh;
    }
  }
</style>
