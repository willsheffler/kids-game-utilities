<script>
  import { createEventDispatcher } from 'svelte';

  export let mode = 'auto'; // 'auto' | 'mention' | 'manual' (canonical backend values)
  export let backendUrl = '';
  export let userId = 'will';

  const dispatch = createEventDispatcher();

  const modes = [
    { value: 'auto', label: 'Auto' },
    { value: 'mention', label: '@mention' },
    { value: 'manual', label: 'Manual' },
  ];

  async function setMode(value) {
    mode = value;
    dispatch('change', { mode: value });
    // Persist to backend
    if (backendUrl) {
      try {
        await fetch(`${backendUrl}/api/prefs/trigger-mode`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ userId, mode: value }),
        });
      } catch (e) { /* ignore */ }
    }
  }
</script>

<div class="trigger-control">
  <span class="trigger-label">Trigger:</span>
  {#each modes as m}
    <button
      class:active={mode === m.value}
      on:click={() => setMode(m.value)}
    >{m.label}</button>
  {/each}
</div>

<style>
  .trigger-control {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75em;
  }
  .trigger-label {
    color: var(--text-dim, #888);
    margin-right: 4px;
  }
  button {
    background: none;
    border: 1px solid var(--border, #2a2a2a);
    color: var(--text-dim, #888);
    padding: 2px 8px;
    border-radius: 10px;
    cursor: pointer;
    font-size: 1em;
    font-family: inherit;
  }
  button.active {
    border-color: var(--accent, #4a9eff);
    color: var(--accent, #4a9eff);
  }
</style>
