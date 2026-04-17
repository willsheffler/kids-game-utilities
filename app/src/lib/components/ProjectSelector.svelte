<script>
  export let activeProject = '';
  export let backendUrl = '';

  // Placeholder — will load from backend prefs later
  let projects = ['(default)'];
</script>

<select class="project-selector" bind:value={activeProject}>
  {#each projects as p}
    <option value={p}>{p}</option>
  {/each}
</select>

<style>
  .project-selector {
    background: var(--bg, #0f0f0f);
    color: var(--text, #e8e8e8);
    border: 1px solid var(--border, #2a2a2a);
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 0.85em;
    font-family: inherit;
  }
</style>
