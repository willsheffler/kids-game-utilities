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
    // Fallback: find first canvas on page
    return document.querySelector('canvas');
  }

  function capture() {
    const canvas = getCanvas();
    if (!canvas) {
      // No canvas — capture the whole content area instead
      captureElement(document.querySelector('.content-area') || document.body);
      return;
    }
    previewUrl = canvas.toDataURL('image/png');
    canvas.toBlob(blob => { previewBlob = blob; }, 'image/png');
    capturing = true;
  }

  function captureElement(el) {
    // For non-canvas elements, use html2canvas-like approach
    // For v1, just screenshot the viewport via a placeholder
    // TODO: integrate proper element capture
    previewUrl = '';
    previewBlob = null;
    capturing = true;
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

      // Upload via chat-with-image
      const resp = await fetch(`${backendUrl}/chat-with-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: label,
          image_b64: b64,
          image_filename: `screenshot_${Date.now()}.png`,
        }),
      });
      const data = await resp.json();

      dispatch('captured', {
        label,
        path: data.image_path || '',
        reply: data.reply || '',
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
    border: 1px solid var(--border, #2a2a2a);
    color: var(--text-dim, #888);
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1em;
    margin: 4px 8px;
  }
  .capture-btn:hover { border-color: var(--accent, #4a9eff); }

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
