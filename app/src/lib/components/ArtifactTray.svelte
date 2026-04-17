<script>
  export let backendUrl = '';
  export let project = '';
  export let artifacts = [];
</script>

<div class="artifact-tray">
  {#if artifacts.length === 0}
    <div class="empty">No artifacts yet</div>
  {:else}
    {#each artifacts as art}
      <div class="artifact-thumb">
        <img src="{backendUrl}/uploads/{art.filename}" alt={art.label} />
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
  .artifact-label {
    display: block;
    font-size: 0.65em;
    color: var(--text-dim, #888);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
