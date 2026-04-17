<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';

  export let backendUrl = '';
  export let session = '';
  export let user = '';
  export let agentLabel = 'agent';
  export let triggerMode = 'auto'; // 'auto' | 'mention' | 'manual'

  const dispatch = createEventDispatcher();

  let messages = [];
  let inputText = '';
  let processing = false;
  let chatEl;
  let pollTimer;

  const seenKeys = new Set();

  function msgKey(role, text) {
    const norm = (text || '').replace(/^\[[^\]]+\]:\s*/, '').trim().slice(0, 120);
    return `${role}|${norm}`;
  }

  function addMessage(role, text, sender, { fromHistory = false } = {}) {
    const key = msgKey(role, text);
    if (seenKeys.has(key)) return;
    seenKeys.add(key);
    // Strip [Name]: prefix for display
    let displayText = text || '';
    let label = sender || '';
    if (role === 'user' && !label) {
      const m = displayText.match(/^\[([^\]]+)\]:\s*/);
      if (m) { label = m[1]; displayText = displayText.slice(m[0].length); }
    }
    if (role === 'agent') {
      displayText = displayText.replace(/^\[[^\]]+\]:\s*/, '');
    }
    // Extract agent tags — only dispatch side effects for new messages, not history replay
    if (role === 'agent') {
      const ssMatch = displayText.match(/\[suggest-screenshot:\s*"([^"]+)"\]/);
      if (ssMatch) {
        if (!fromHistory) dispatch('suggest-screenshot', { label: ssMatch[1] });
        displayText = displayText.replace(ssMatch[0], '').trim();
      }
      const reportMatch = displayText.match(/\[save-report\]([\s\S]*?)\[\/save-report\]/);
      if (reportMatch) {
        if (!fromHistory) dispatch('save-report', { markdown: reportMatch[1].trim() });
        displayText = displayText.replace(reportMatch[0], '').trim();
        if (!displayText) displayText = '(Report saved)';
      }
    }
    messages = [...messages, { role, text: displayText, label: label || (role === 'agent' ? agentLabel : ''), raw: text }];
    scrollToBottom();
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      if (chatEl) chatEl.scrollTop = chatEl.scrollHeight;
    });
  }

  async function loadHistory() {
    if (!session) return;
    try {
      const resp = await fetch(`${backendUrl}/history/${encodeURIComponent(session)}`);
      const data = await resp.json();
      messages = [];
      seenKeys.clear();
      for (const m of (data.messages || [])) {
        addMessage(m.role, m.text, m.sender || '', { fromHistory: true });
      }
    } catch (e) { console.warn('History load failed:', e); }
  }

  function shouldSendToAgent(text) {
    if (triggerMode === 'auto') return true;
    if (triggerMode === 'mention') return /@\w+/.test(text);
    return false; // 'manual' — never send automatically
  }

  async function send() {
    const text = inputText.trim();
    if (!text || processing) return;
    inputText = '';
    addMessage('user', text, user);

    if (!shouldSendToAgent(text)) return;

    processing = true;
    try {
      const resp = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, session }),
      });
      const data = await resp.json();
      if (data.detail) throw new Error(data.detail);
      addMessage('agent', data.reply || '(no reply)', agentLabel);
    } catch (e) {
      addMessage('system', 'Error: ' + e.message, '');
    }
    processing = false;
  }

  async function poll() {
    if (!session) return;
    try {
      const resp = await fetch(`${backendUrl}/poll/${encodeURIComponent(session)}`);
      const data = await resp.json();
      for (const msg of (data.messages || [])) {
        addMessage(msg.role || 'agent', msg.text, msg.sender || agentLabel);
      }
    } catch (e) { /* ignore */ }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  onMount(() => {
    loadHistory();
    pollTimer = setInterval(poll, 3000);
  });

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
  });
</script>

<div class="chat-panel">
  <div class="chat-messages" bind:this={chatEl}>
    {#each messages as msg}
      <div class="msg {msg.role}">
        {#if msg.label}
          <span class="msg-label">{msg.label}</span>
        {/if}
        <span class="msg-text">{msg.text}</span>
      </div>
    {/each}
  </div>

  <div class="chat-input">
    <textarea
      bind:value={inputText}
      on:keydown={handleKeydown}
      placeholder="Type a message..."
      rows="1"
      disabled={processing}
    ></textarea>
    <button on:click={send} disabled={processing || !inputText.trim()}>↑</button>
  </div>
</div>

<style>
  .chat-panel {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .msg {
    padding: 8px 12px;
    border-radius: 10px;
    max-width: 90%;
    line-height: 1.4;
    font-size: 0.9em;
    word-wrap: break-word;
    white-space: pre-wrap;
  }
  .msg.user { align-self: flex-end; background: #1e3a5f; border-radius: 10px 10px 2px 10px; }
  .msg.agent { align-self: flex-start; background: var(--surface, #1a1a1a); border-left: 3px solid var(--accent, #4a9eff); border-radius: 10px 10px 10px 2px; }
  .msg.system { align-self: center; color: var(--text-dim, #888); font-size: 0.85em; font-style: italic; }

  .msg-label {
    display: block;
    font-size: 0.75em;
    opacity: 0.6;
    margin-bottom: 2px;
  }

  .chat-input {
    display: flex;
    gap: 6px;
    padding: 8px;
    border-top: 1px solid var(--border, #2a2a2a);
    flex-shrink: 0;
  }

  .chat-input textarea {
    flex: 1;
    background: var(--bg, #0f0f0f);
    border: 1px solid var(--border, #2a2a2a);
    color: var(--text, #e8e8e8);
    border-radius: 16px;
    padding: 8px 12px;
    font-size: 0.9em;
    font-family: inherit;
    resize: none;
    outline: none;
  }
  .chat-input textarea:focus { border-color: var(--accent, #4a9eff); }

  .chat-input button {
    background: var(--accent, #4a9eff);
    color: #fff;
    border: none;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    font-size: 1em;
    cursor: pointer;
    flex-shrink: 0;
  }
  .chat-input button:disabled { opacity: 0.4; cursor: default; }
</style>
