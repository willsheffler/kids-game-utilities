<script>
  import { onMount, createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let activeProject = '';
  export let backendUrl = '';
  export let userId = 'will';

  let projects = [];

  async function loadProjects() {
    try {
      const resp = await fetch(`${backendUrl}/api/projects`);
      if (resp.ok) {
        const data = await resp.json();
        projects = data.result?.projects || [];
      }
    } catch (e) { /* backend may not be ready */ }
  }

  async function setProject(slug) {
    activeProject = slug;
    try {
      await fetch(`${backendUrl}/api/prefs/active-project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, projectSlug: slug }),
      });
    } catch (e) { /* ignore */ }
    dispatch('change', { project: slug });
  }

  onMount(loadProjects);
</script>

<select class="project-selector" value={activeProject} on:change={(e) => setProject(e.target.value)}>
  <option value="">(all projects)</option>
  {#each projects as p}
    <option value={p.slug}>{p.label || p.slug}</option>
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
