<script>
  export let status = 'idle'; // 'idle' | 'busy' | 'error'
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
