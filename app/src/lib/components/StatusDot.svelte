<script>
  import { onMount, onDestroy } from 'svelte';

  export let status = 'idle';
  export let backendUrl = '';
  export let session = '';
  export let pollInterval = 3000;

  let timer;

  async function poll() {
    if (!backendUrl || !session) return;
    try {
      const resp = await fetch(`${backendUrl}/agent-status/${encodeURIComponent(session)}`);
      if (resp.ok) {
        const data = await resp.json();
        const bs = data.busy_status || data.status || 'unknown';
        if (bs === 'busy' || bs === 'busy_tool_use' || bs === 'busy_generating') {
          status = 'busy';
        } else if (data.status === 'unknown' || data.dead) {
          status = 'error';
        } else {
          status = 'idle';
        }
      }
    } catch (e) { /* ignore */ }
  }

  onMount(() => {
    poll();
    timer = setInterval(poll, pollInterval);
  });

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });
</script>

<span class="status-dot {status}" title="Agent: {status}"></span>

<style>
  .status-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #555;
  }
  .status-dot.idle { background: #4dbb6e; }
  .status-dot.busy { background: #f0ad4e; }
  .status-dot.error { background: #e05555; }
</style>
