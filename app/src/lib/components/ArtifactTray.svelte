<script>
  export let backendUrl = '';
  export let project = '';
  export let artifacts = [];

  const kindEmoji = { screenshot: '📷', file: '📄', code: '💻', asset: '🎨' };

  function imgSrc(art) {
    if (art.url) return art.url;
    if (art.path?.startsWith('/uploads/')) return backendUrl + art.path;
    return '';
  }
</script>

<div class="artifact-tray">
  {#if artifacts.length === 0}
    <div class="empty">No artifacts yet</div>
  {:else}
    {#each artifacts as art}
      <div class="artifact-thumb">
        {#if imgSrc(art)}
          <img
            src={imgSrc(art)}
            alt={art.label}
            on:error={(e) => { e.target.style.display = 'none'; e.target.nextElementSibling.style.display = 'flex'; }}
          />
          <div class="emoji-fallback" style="display:none">{kindEmoji[art.kind] || '📎'}</div>
        {:else}
          <div class="emoji-fallback">{kindEmoji[art.kind] || '📎'}</div>
        {/if}
        <span class="artifact-label">{art.label}</span>
      </div>
    {/each}
  {/if}
</div>

<style>
  .artifact-tray {
    padding: 8px;
    border-bottom: 1px solid var(--border, #2a2a2a);
    min-height: 48px;
    flex-shrink: 0;
    overflow-x: auto;
    display: flex;
    gap: 6px;
    align-items: center;
  }
  .empty {
    color: var(--text-dim, #888);
    font-size: 0.8em;
    font-style: italic;
  }
  .artifact-thumb {
    flex-shrink: 0;
    width: 60px;
    text-align: center;
  }
  .artifact-thumb img {
    width: 60px;
    height: 40px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid var(--border, #2a2a2a);
  }
  .emoji-fallback {
    width: 60px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4em;
    background: var(--surface, #1a1a1a);
    border-radius: 4px;
    border: 1px solid var(--border, #2a2a2a);
  }
  .artifact-label {
    display: block;
    font-size: 0.65em;
    color: var(--text-dim, #888);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
