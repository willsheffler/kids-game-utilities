<script>
  import { createEventDispatcher } from 'svelte';

  export let label = '';
  export let visible = false;

  const dispatch = createEventDispatcher();

  function accept() {
    dispatch('accept', { label });
    visible = false;
  }

  function dismiss() {
    dispatch('dismiss', { label });
    visible = false;
  }
</script>

{#if visible}
  <div class="suggestion-toast">
    <span class="suggestion-icon">📷</span>
    <span class="suggestion-text">Screenshot: {label}</span>
    <button class="accept" on:click={accept}>✓ Capture</button>
    <button class="dismiss" on:click={dismiss}>✕</button>
  </div>
{/if}

<style>
  .suggestion-toast {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    margin: 4px 8px;
    background: rgba(74, 158, 255, 0.1);
    border: 1px solid var(--accent, #4a9eff);
    border-radius: 8px;
    font-size: 0.85em;
    animation: slideIn 0.2s ease-out;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .suggestion-icon { font-size: 1.2em; }
  .suggestion-text { flex: 1; color: var(--text, #e8e8e8); }

  .accept {
    background: var(--accent, #4a9eff);
    color: #fff;
    border: none;
    padding: 3px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9em;
  }
  .dismiss {
    background: none;
    border: none;
    color: var(--text-dim, #888);
    cursor: pointer;
    font-size: 1em;
    padding: 2px 6px;
  }
</style>
