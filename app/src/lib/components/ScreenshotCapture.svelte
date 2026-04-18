<script>
  import { createEventDispatcher } from 'svelte';

  export let targetCanvas = null; // CSS selector or element ref
  export let backendUrl = '';
  export let suggestedLabel = ''; // pre-filled from agent suggestion

  const dispatch = createEventDispatcher();

  let capturing = false;
  let previewUrl = '';
  let previewBlob = null;
  let label = '';
  let sending = false;

  $: label = suggestedLabel || label;
  $: canSend = label.trim().length >= 3 && previewBlob && !sending;

  function getCanvas() {
    if (targetCanvas instanceof HTMLElement) return targetCanvas;
    if (typeof targetCanvas === 'string') return document.querySelector(targetCanvas);
    // Check main document first
    let c = document.querySelector('canvas');
    if (c) return c;
    // Check inside same-origin iframes
    try {
      const iframe = document.querySelector('iframe.game-frame');
      if (iframe?.contentDocument) {
        c = iframe.contentDocument.querySelector('canvas');
        if (c) return c;
      }
    } catch (e) { /* cross-origin, skip */ }
    return null;
  }

  function capture() {
    const canvas = getCanvas();
    if (canvas) {
      previewUrl = canvas.toDataURL('image/png');
      canvas.toBlob(blob => { previewBlob = blob; }, 'image/png');
      capturing = true;
      return;
    }
    // No canvas — try to capture iframe body via offscreen canvas
    try {
      const iframe = document.querySelector('iframe.game-frame');
      const iframeDoc = iframe?.contentDocument;
      if (iframeDoc) {
        captureIframeBody(iframe);
        return;
      }
    } catch (e) { /* cross-origin */ }
    previewUrl = '';
    previewBlob = null;
    capturing = true;
  }

  function captureIframeBody(iframe) {
    const rect = iframe.getBoundingClientRect();
    const offscreen = document.createElement('canvas');
    offscreen.width = rect.width;
    offscreen.height = rect.height;
    const octx = offscreen.getContext('2d');
    // Draw iframe content via foreignObject SVG
    const data = new XMLSerializer().serializeToString(iframe.contentDocument.documentElement);
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${rect.width}" height="${rect.height}">
      <foreignObject width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml">${data}</div>
      </foreignObject>
    </svg>`;
    const img = new Image();
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    img.onload = () => {
      octx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      previewUrl = offscreen.toDataURL('image/png');
      offscreen.toBlob(b => { previewBlob = b; }, 'image/png');
      capturing = true;
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      previewUrl = '';
      previewBlob = null;
      capturing = true;
    };
    img.src = url;
  }

  function dismiss() {
    capturing = false;
    previewUrl = '';
    previewBlob = null;
    label = '';
    suggestedLabel = '';
  }

  async function send() {
    if (!canSend) return;
    sending = true;

    try {
      // Convert blob to base64
      const reader = new FileReader();
      const b64 = await new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(previewBlob);
      });

      // Create artifact via backend API
      const resp = await fetch(`${backendUrl}/api/artifacts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          kind: 'screenshot',
          label: label,
          image_b64: b64,
          image_filename: `screenshot_${Date.now()}.png`,
        }),
      });
      const data = await resp.json();
      const artifact = data.result?.artifact || {};

      dispatch('captured', {
        label,
        id: artifact.id || '',
        path: artifact.path || '',
      });

      dismiss();
    } catch (e) {
      console.error('Screenshot upload failed:', e);
    }
    sending = false;
  }
</script>

<div class="screenshot-capture">
  {#if !capturing}
    <button class="capture-btn" on:click={capture} title="Take screenshot">
      📷
    </button>
  {:else}
    <div class="capture-modal">
      {#if previewUrl}
        <img class="preview" src={previewUrl} alt="Screenshot preview" />
      {:else}
        <div class="preview placeholder">No canvas found — capture not available</div>
      {/if}

      <div class="label-input">
        <input
          type="text"
          bind:value={label}
          placeholder="Describe what this shows... (required)"
          autofocus
          on:keydown={(e) => { if (e.key === 'Enter' && canSend) send(); }}
        />
        <span class="char-count" class:ok={label.trim().length >= 3}>
          {label.trim().length}/3+
        </span>
      </div>

      <div class="capture-actions">
        <button class="dismiss" on:click={dismiss}>Cancel</button>
        <button class="send" on:click={send} disabled={!canSend}>
          {sending ? '...' : 'Send'}
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .screenshot-capture {
    flex-shrink: 0;
  }

  .capture-btn {
    background: none;
    border: none;
    color: var(--text-dim, #888);
    padding: 4px 6px;
    cursor: pointer;
    font-size: 1.1em;
    flex-shrink: 0;
  }
  .capture-btn:hover { color: var(--accent, #4a9eff); }

  .capture-modal {
    padding: 8px;
    border: 1px solid var(--border, #2a2a2a);
    border-radius: 8px;
    margin: 4px 8px;
    background: var(--bg, #0f0f0f);
  }

  .preview {
    width: 100%;
    max-height: 150px;
    object-fit: contain;
    border-radius: 4px;
    border: 1px solid var(--border, #2a2a2a);
    margin-bottom: 6px;
  }
  .preview.placeholder {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-dim, #888);
    font-size: 0.8em;
  }

  .label-input {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
  }
  .label-input input {
    flex: 1;
    background: var(--surface, #1a1a1a);
    border: 1px solid var(--border, #2a2a2a);
    color: var(--text, #e8e8e8);
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 0.85em;
    font-family: inherit;
    outline: none;
  }
  .label-input input:focus { border-color: var(--accent, #4a9eff); }
  .char-count { font-size: 0.7em; color: var(--text-dim, #888); }
  .char-count.ok { color: var(--accent, #4a9eff); }

  .capture-actions {
    display: flex;
    justify-content: flex-end;
    gap: 6px;
  }
  .capture-actions button {
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.85em;
    cursor: pointer;
    font-family: inherit;
  }
  .dismiss {
    background: none;
    border: 1px solid var(--border, #2a2a2a);
    color: var(--text-dim, #888);
  }
  .send {
    background: var(--accent, #4a9eff);
    border: none;
    color: #fff;
  }
  .send:disabled { opacity: 0.4; cursor: default; }
</style>
