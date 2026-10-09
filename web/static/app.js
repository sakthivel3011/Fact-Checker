// Fact-Checker & Daily News Digest — Frontend Application Logic
// Redesigned for Premium Light Theme UI

document.addEventListener('DOMContentLoaded', () => {
  // ── Navigation Tabs ──────────────────────────────────────────
  const navTabs   = document.querySelectorAll('.nav-tab');
  const tabPanels = document.querySelectorAll('.tab-panel');

  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-tab');
      navTabs.forEach(t   => t.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add('active');

      if (targetId === 'tab-digest')  loadNewsDigest();
      if (targetId === 'tab-history') loadHistory();
    });
  });

  // ── Benchmark Chips ──────────────────────────────────────────
  const claimTextarea = document.getElementById('claim-input');
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const claim = chip.getAttribute('data-claim');
      if (claim && claimTextarea) {
        claimTextarea.value = claim;
        triggerFactCheck();
      }
    });
  });

  // ── Fact Check Button ─────────────────────────────────────────
  const factCheckBtn = document.getElementById('btn-fact-check');
  if (factCheckBtn) factCheckBtn.addEventListener('click', triggerFactCheck);

  // ── Category Pills ────────────────────────────────────────────
  document.querySelectorAll('.cat-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      loadNewsDigest(pill.getAttribute('data-category'));
    });
  });

  // ── Export Buttons ────────────────────────────────────────────
  const exportMdBtn   = document.getElementById('btn-export-md');
  const exportJsonBtn = document.getElementById('btn-export-json');
  if (exportMdBtn) {
    exportMdBtn.addEventListener('click', () => {
      window.location.href = `/api/digest/export?category=${getActiveCategory()}&format=markdown`;
    });
  }
  if (exportJsonBtn) {
    exportJsonBtn.addEventListener('click', () => {
      window.location.href = `/api/digest/export?category=${getActiveCategory()}&format=json`;
    });
  }

  // ── MCP Run Button ────────────────────────────────────────────
  const mcpRunBtn = document.getElementById('btn-mcp-run');
  if (mcpRunBtn) mcpRunBtn.addEventListener('click', executeMcpTool);
});

function getActiveCategory() {
  const activePill = document.querySelector('.cat-pill.active');
  return activePill ? activePill.getAttribute('data-category') : 'World';
}

// ─────────────────────────────────────────────────────────────────────────────
// FACT-CHECK PIPELINE
// ─────────────────────────────────────────────────────────────────────────────
async function triggerFactCheck() {
  const input           = document.getElementById('claim-input');
  const btn             = document.getElementById('btn-fact-check');
  const resultContainer = document.getElementById('factcheck-result');

  const claim = input.value.trim();
  if (!claim) { alert('Please enter a claim or headline to verify.'); return; }

  // Loading State
  btn.disabled   = true;
  btn.innerHTML  = `<span class="spinner"></span> Running Agents…`;

  resultContainer.innerHTML = `
    <div class="card">
      <div class="loading-card">
        <div class="spinner spinner-lg" style="display:block; margin:0 auto;"></div>
        <p style="margin-top:1rem;">
          Orchestrating <strong>LangGraph StateGraph</strong>:<br>
          Input Guardrail → Clickbait Analysis → RAG Retrieval → ReAct Web Search → Synthesis…
        </p>
      </div>
    </div>
  `;

  try {
    const resp = await fetch('/api/fact-check', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ claim })
    });
    if (!resp.ok) throw new Error(`API responded with ${resp.status}`);
    const data = await resp.json();
    renderFactCheckResult(data);
  } catch (err) {
    resultContainer.innerHTML = `
      <div class="error-card">
        <h4>⚠️ Fact-Check Execution Error</h4>
        <p>${err.message}</p>
      </div>
    `;
  } finally {
    btn.disabled  = false;
    btn.innerHTML = `<span>⚡</span> Verify Claim with Agents`;
  }
}

function renderFactCheckResult(data) {
  const container = document.getElementById('factcheck-result');

  // Verdict classes
  let badgeClass = 'badge-unverified';
  let boxClass   = 'verdict-unverified';

  const v = (data.verdict || '').toUpperCase();
  if (v === 'TRUE' || v === 'LIKELY TRUE') {
    badgeClass = 'badge-true';   boxClass = 'verdict-true';
  } else if (v === 'FALSE') {
    badgeClass = 'badge-false';  boxClass = 'verdict-false';
  } else if (v === 'MISLEADING' || v === 'MIXTURE') {
    badgeClass = 'badge-misleading'; boxClass = 'verdict-misleading';
  }

  const verdictIcon =
    v === 'TRUE' ? '✅' :
    v === 'FALSE' ? '❌' :
    v === 'MISLEADING' ? '⚠️' : 'ℹ️';

  // ReAct Steps
  let reactHtml = '';
  if (data.react_steps && data.react_steps.length > 0) {
    reactHtml = data.react_steps.map((s, i) => `
      <div class="react-step">
        <p><span class="react-tag tag-thought">Thought ${s.iteration || i + 1}</span> ${s.thought}</p>
        <p style="margin-top:0.3rem;"><span class="react-tag tag-action">Action</span>
          <code style="font-size:0.83em; color:var(--indigo);">${s.action}("${s.action_input || ''}")</code></p>
        <p style="margin-top:0.3rem;"><span class="react-tag tag-obs">Observation</span> ${s.observation}</p>
      </div>
    `).join('');
  } else {
    reactHtml = `<p style="color:var(--text-muted); font-size:0.88rem;">ReAct reasoning concluded directly — no iterative steps required.</p>`;
  }

  // Sources
  let sourcesHtml = '';
  if (data.sources && data.sources.length > 0) {
    sourcesHtml = data.sources.map(src => `
      <div class="citation-item">
        <div class="citation-header">
          <span class="citation-title">
            <a href="${src.url}" target="_blank" rel="noopener">${src.title || src.domain}</a>
          </span>
          <span class="domain-pill">${src.domain} · ${src.credibility_rating}/100</span>
        </div>
        <p class="snippet-text">"${src.snippet}"</p>
      </div>
    `).join('');
  } else {
    sourcesHtml = `<p style="color:var(--text-muted); font-size:0.88rem; padding:0.75rem;">No external citations recorded.</p>`;
  }

  // Clickbait flags
  const clickbaitFlagsHtml = (data.clickbait_flags && data.clickbait_flags.length > 0) ? `
    <div class="clickbait-flags-box">
      <strong>🚩 Clickbait Flags Detected:</strong>
      <ul>${data.clickbait_flags.map(f => `<li>${f}</li>`).join('')}</ul>
    </div>
  ` : '';

  // Metric colour helpers
  const credColor  = data.credibility_score >= 60 ? 'var(--emerald)' : data.credibility_score >= 35 ? 'var(--amber)' : 'var(--rose)';
  const confColor  = 'var(--indigo)';
  const clickColor = data.clickbait_score > 40 ? 'var(--amber)' : 'var(--emerald)';

  container.innerHTML = `
    <div class="verdict-box ${boxClass}">

      <!-- Header Row -->
      <div class="verdict-header">
        <span class="verdict-badge ${badgeClass}">
          ${verdictIcon} ${data.verdict}
        </span>
        <span class="verdict-status-pill">
          ${data.is_safe ? '✅ Safe Input' : '🚫 Flagged Unsafe'} &nbsp;|&nbsp; Guardrail Verified
        </span>
      </div>

      <!-- Metrics -->
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Credibility Score</div>
          <div class="metric-value" style="color:${credColor}">${data.credibility_score}%</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:${data.credibility_score}%; background:${credColor};"></div>
          </div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Agent Confidence</div>
          <div class="metric-value" style="color:${confColor}">${data.confidence}%</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:${data.confidence}%; background:${confColor};"></div>
          </div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Clickbait / Sensationalism</div>
          <div class="metric-value" style="color:${clickColor}">${data.clickbait_score}%</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:${data.clickbait_score}%; background:${clickColor};"></div>
          </div>
        </div>
      </div>

      <div class="divider"></div>

      <!-- Summary -->
      <p class="section-title">📋 Executive Verdict Summary</p>
      <p class="verdict-summary-text">${data.summary}</p>

      <!-- Reasoning -->
      <p class="section-title">🔬 Forensic Analysis &amp; Reasoning</p>
      <div class="verdict-reasoning">${data.reasoning}</div>

      <!-- Clickbait Flags -->
      ${clickbaitFlagsHtml}

      <!-- ReAct Trace -->
      <details open>
        <summary>🔄 ReAct Agent Deliberation Trace (${data.react_steps ? data.react_steps.length : 0} Steps)</summary>
        <div class="react-trace-box">${reactHtml}</div>
      </details>

      <!-- Citations -->
      <details open>
        <summary>📚 Authoritative Citations &amp; Evidence (${data.sources ? data.sources.length : 0})</summary>
        <div class="citations-list">${sourcesHtml}</div>
      </details>
    </div>
  `;
}

// ─────────────────────────────────────────────────────────────────────────────
// DAILY NEWS DIGEST
// ─────────────────────────────────────────────────────────────────────────────
async function loadNewsDigest(category = 'World') {
  const container  = document.getElementById('digest-feed');
  const execSummary = document.getElementById('digest-exec-summary');
  if (!container) return;

  container.innerHTML = `
    <div class="loading-card">
      <div class="spinner spinner-lg" style="display:block; margin:0 auto;"></div>
      <p>Fetching live RSS feeds &amp; summarising via LangGraph…</p>
    </div>
  `;

  try {
    const resp = await fetch(`/api/digest?category=${encodeURIComponent(category)}&limit=6`);
    const data = await resp.json();

    if (execSummary) {
      execSummary.innerHTML = `
        <div class="digest-exec-card">
          <h4>📋 Daily Briefing — ${data.date}</h4>
          <p>${data.executive_summary}</p>
        </div>
      `;
    }

    if (data.articles && data.articles.length > 0) {
      container.innerHTML = data.articles.map(art => `
        <div class="article-digest-card">
          <div class="article-meta">
            <span class="source-badge">${art.source}</span>
            <span class="cred-badge">Credibility: ${art.credibility_score}/100</span>
            <span>${art.published}</span>
          </div>
          <h3 class="article-title">
            <a href="${art.url}" target="_blank" rel="noopener">${art.title}</a>
          </h3>
          <p class="article-summary">${art.summary}</p>
          ${art.key_points && art.key_points.length ? `
            <div class="article-bullets">
              <div class="article-bullets-label">Key Takeaways</div>
              ${art.key_points.map(pt => `<div class="article-bullet">${pt}</div>`).join('')}
            </div>
          ` : ''}
        </div>
      `).join('');
    } else {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">📭</div>
          <p>No stories found for this category right now. Try another category.</p>
        </div>
      `;
    }
  } catch (err) {
    container.innerHTML = `
      <div class="error-card">
        <h4>⚠️ Failed to Load News Digest</h4>
        <p>${err.message}</p>
      </div>
    `;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// MCP PROTOCOL TESTING
// ─────────────────────────────────────────────────────────────────────────────
async function executeMcpTool() {
  const toolSelect = document.getElementById('mcp-tool-select');
  const paramInput = document.getElementById('mcp-tool-param');
  const viewer     = document.getElementById('mcp-output-viewer');

  const toolName = toolSelect.value;
  let args = {};

  if (toolName === 'fact_check_claim')              args = { claim:         paramInput.value || '5G cell towers cause viral infection' };
  else if (toolName === 'get_daily_digest')         args = { category:      paramInput.value || 'Technology', limit: 3 };
  else if (toolName === 'verify_source_credibility') args = { domain_or_url: paramInput.value || 'reuters.com' };
  else if (toolName === 'analyze_headline_clickbait') args = { headline:     paramInput.value || "YOU WON'T BELIEVE THIS SHOCKING SECRET!" };
  else if (toolName === 'search_rag_knowledge_base') args = { query:        paramInput.value || 'exoplanet atmosphere biosignature', top_k: 2 };

  viewer.textContent = '⏳ Executing MCP tool call via JSON-RPC…';

  try {
    const resp = await fetch('/api/mcp/tool/call', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name: toolName, arguments: args })
    });
    const result = await resp.json();
    viewer.textContent = JSON.stringify(result, null, 2);
  } catch (err) {
    viewer.textContent = `❌ Error executing MCP tool: ${err.message}`;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// HISTORY
// ─────────────────────────────────────────────────────────────────────────────
async function loadHistory() {
  const container = document.getElementById('history-feed');
  if (!container) return;

  try {
    const resp = await fetch('/api/history');
    const data = await resp.json();

    if (data.fact_checks && data.fact_checks.length > 0) {
      container.innerHTML = data.fact_checks.map((fc, idx) => {
        const v = (fc.verdict || '').toUpperCase();
        const badgeClass = v === 'TRUE' ? 'badge-true' : v === 'FALSE' ? 'badge-false' : v === 'MISLEADING' ? 'badge-misleading' : 'badge-unverified';
        return `
          <div class="history-item">
            <div style="flex:1;">
              <div class="history-claim">#${idx + 1}: ${fc.claim}</div>
              <div class="history-summary">${fc.summary}</div>
            </div>
            <span class="verdict-badge ${badgeClass}" style="font-size:0.75rem; padding:0.3rem 0.85rem;">
              ${fc.verdict}
            </span>
          </div>
        `;
      }).join('');
    } else {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">🗂️</div>
          <p>No queries yet this session. Run a fact-check to populate history!</p>
        </div>
      `;
    }
  } catch (err) {
    container.innerHTML = `
      <div class="error-card">
        <h4>⚠️ Error fetching history</h4>
        <p>${err.message}</p>
      </div>
    `;
  }
}
