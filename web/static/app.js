// Fact-Checker & Daily News Digest Frontend Application Logic

document.addEventListener('DOMContentLoaded', () => {
  // Navigation Tabs Switching
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabPanels = document.querySelectorAll('.tab-panel');

  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-tab');
      navTabs.forEach(t => t.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add('active');

      if (targetId === 'tab-digest') {
        loadNewsDigest();
      } else if (targetId === 'tab-history') {
        loadHistory();
      }
    });
  });

  // Benchmark Claim Chips
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

  // Fact Check Submission
  const factCheckBtn = document.getElementById('btn-fact-check');
  if (factCheckBtn) {
    factCheckBtn.addEventListener('click', triggerFactCheck);
  }

  // Digest Category Pills
  document.querySelectorAll('.cat-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const cat = pill.getAttribute('data-category');
      loadNewsDigest(cat);
    });
  });

  // Export Buttons
  const exportMdBtn = document.getElementById('btn-export-md');
  const exportJsonBtn = document.getElementById('btn-export-json');
  if (exportMdBtn) {
    exportMdBtn.addEventListener('click', () => {
      const activeCat = getActiveCategory();
      window.location.href = `/api/digest/export?category=${activeCat}&format=markdown`;
    });
  }
  if (exportJsonBtn) {
    exportJsonBtn.addEventListener('click', () => {
      const activeCat = getActiveCategory();
      window.location.href = `/api/digest/export?category=${activeCat}&format=json`;
    });
  }

  // MCP Test Tool Trigger
  const mcpRunBtn = document.getElementById('btn-mcp-run');
  if (mcpRunBtn) {
    mcpRunBtn.addEventListener('click', executeMcpTool);
  }
});

function getActiveCategory() {
  const activePill = document.querySelector('.cat-pill.active');
  return activePill ? activePill.getAttribute('data-category') : 'World';
}

// -------------------------------------------------------------------------
// Fact-Check Pipeline Invocation
// -------------------------------------------------------------------------
async function triggerFactCheck() {
  const input = document.getElementById('claim-input');
  const btn = document.getElementById('btn-fact-check');
  const resultContainer = document.getElementById('factcheck-result');

  const claim = input.value.trim();
  if (!claim) {
    alert("Please enter a claim or headline to verify.");
    return;
  }

  // Set loading state
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Running LangGraph Agents...`;
  resultContainer.innerHTML = `
    <div class="card" style="text-align: center; padding: 2.5rem;">
      <span class="spinner" style="width: 2rem; height: 2rem; border-width: 3px;"></span>
      <p style="margin-top: 1rem; color: #9ca3af;">Orchestrating LangGraph StateGraph (Input Guardrail → Clickbait Analysis → RAG Retrieval → ReAct Web Search → Synthesis)...</p>
    </div>
  `;

  try {
    const resp = await fetch('/api/fact-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ claim: claim })
    });

    if (!resp.ok) {
      throw new Error(`API responded with ${resp.status}`);
    }

    const data = await resp.json();
    renderFactCheckResult(data);
  } catch (err) {
    resultContainer.innerHTML = `
      <div class="card" style="border-color: #ef4444; background: rgba(239, 68, 68, 0.1);">
        <h4 style="color: #ef4444;">Fact-Check Execution Error</h4>
        <p style="color: #d1d5db; margin-top: 0.5rem;">${err.message}</p>
      </div>
    `;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Verify Claim with Agents`;
  }
}

function renderFactCheckResult(data) {
  const container = document.getElementById('factcheck-result');
  const verdictClass = data.verdict.toLowerCase().replace(" ", "-");

  let badgeColorClass = "badge-unverified";
  let boxBorderClass = "verdict-unverified";
  if (data.verdict === "TRUE" || data.verdict === "LIKELY TRUE") {
    badgeColorClass = "badge-true";
    boxBorderClass = "verdict-true";
  } else if (data.verdict === "FALSE") {
    badgeColorClass = "badge-false";
    boxBorderClass = "verdict-false";
  } else if (data.verdict === "MISLEADING" || data.verdict === "MIXTURE") {
    badgeColorClass = "badge-misleading";
    boxBorderClass = "verdict-misleading";
  }

  // ReAct Steps HTML
  let reactStepsHtml = "";
  if (data.react_steps && data.react_steps.length > 0) {
    reactStepsHtml = data.react_steps.map((s, idx) => `
      <div class="react-step">
        <p><span class="react-tag tag-thought">Thought ${s.iteration || idx + 1}</span> ${s.thought}</p>
        <p style="margin-top: 0.25rem;"><span class="react-tag tag-action">Action</span> <code>${s.action}</code>("${s.action_input || ''}")</p>
        <p style="margin-top: 0.25rem;"><span class="react-tag tag-obs">Observation</span> ${s.observation}</p>
      </div>
    `).join("");
  } else {
    reactStepsHtml = `<p style="color: #9ca3af;">ReAct reasoning concluded directly.</p>`;
  }

  // Sources HTML
  let sourcesHtml = "";
  if (data.sources && data.sources.length > 0) {
    sourcesHtml = data.sources.map(src => `
      <div class="citation-item">
        <div class="citation-header">
          <span class="citation-title"><a href="${src.url}" target="_blank" rel="noopener">${src.title || src.domain}</a></span>
          <span class="domain-pill">${src.domain} • Credibility: ${src.credibility_rating}/100</span>
        </div>
        <p class="snippet-text">"${src.snippet}"</p>
      </div>
    `).join("");
  } else {
    sourcesHtml = `<p style="color: #9ca3af;">No external citations recorded.</p>`;
  }

  container.innerHTML = `
    <div class="verdict-box ${boxBorderClass}">
      <div class="verdict-header">
        <span class="verdict-badge ${badgeColorClass}">
          ${data.verdict === 'TRUE' ? '✅' : (data.verdict === 'FALSE' ? '❌' : (data.verdict === 'MISLEADING' ? '⚠️' : 'ℹ️'))} 
          ${data.verdict}
        </span>
        <div style="font-size: 0.85rem; color: #9ca3af;">
          Status: <strong>${data.is_safe ? 'Safe' : 'Flagged Unsafe'}</strong> | Guardrail Verified
        </div>
      </div>

      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-label">Credibility Score</div>
          <div class="metric-value" style="color: #06b6d4;">${data.credibility_score}%</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: ${data.credibility_score}%; background: #06b6d4;"></div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-label">Agent Confidence</div>
          <div class="metric-value" style="color: #6366f1;">${data.confidence}%</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: ${data.confidence}%; background: #6366f1;"></div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-label">Sensationalism / Clickbait</div>
          <div class="metric-value" style="color: ${data.clickbait_score > 40 ? '#f59e0b' : '#10b981'};">${data.clickbait_score}%</div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: ${data.clickbait_score}%; background: ${data.clickbait_score > 40 ? '#f59e0b' : '#10b981'};"></div>
          </div>
        </div>
      </div>

      <h4 style="margin-bottom: 0.35rem; color: #f3f4f6;">Executive Verdict Summary</h4>
      <p class="verdict-summary">${data.summary}</p>

      <h4 style="margin-bottom: 0.35rem; color: #f3f4f6;">Forensic Analysis & Reasoning</h4>
      <div class="verdict-reasoning">${data.reasoning}</div>

      ${data.clickbait_flags && data.clickbait_flags.length > 0 ? `
        <div style="margin-bottom: 1rem; padding: 0.75rem; background: rgba(245, 158, 11, 0.1); border-radius: 8px; border: 1px solid rgba(245, 158, 11, 0.3);">
          <strong style="color: #fbbf24; font-size: 0.85rem;">Clickbait Flags Detected:</strong>
          <ul style="margin-top: 0.25rem; padding-left: 1.25rem; font-size: 0.82rem; color: #f3f4f6;">
            ${data.clickbait_flags.map(f => `<li>${f}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      <details style="margin-bottom: 1rem;" open>
        <summary style="cursor: pointer; font-weight: 600; color: #818cf8; margin-bottom: 0.5rem;">
          🔄 ReAct Agent Deliberation Trace (${data.react_steps ? data.react_steps.length : 0} Steps)
        </summary>
        <div class="react-trace-box">
          ${reactStepsHtml}
        </div>
      </details>

      <details open>
        <summary style="cursor: pointer; font-weight: 600; color: #06b6d4; margin-bottom: 0.5rem;">
          📚 Authoritative Citations & Evidence (${data.sources ? data.sources.length : 0})
        </summary>
        <div class="citations-list">
          ${sourcesHtml}
        </div>
      </details>
    </div>
  `;
}

// -------------------------------------------------------------------------
// Daily News Digest Loading
// -------------------------------------------------------------------------
async function loadNewsDigest(category = 'World') {
  const container = document.getElementById('digest-feed');
  const execSummary = document.getElementById('digest-exec-summary');
  if (!container) return;

  container.innerHTML = `
    <div style="text-align: center; padding: 3rem; color: #9ca3af;">
      <span class="spinner"></span>
      <p style="margin-top: 0.75rem;">Fetching live RSS feeds & summarizing articles via LangGraph...</p>
    </div>
  `;

  try {
    const resp = await fetch(`/api/digest?category=${encodeURIComponent(category)}&limit=6`);
    const data = await resp.json();

    if (execSummary) {
      execSummary.innerHTML = `
        <div style="background: rgba(99, 102, 241, 0.08); border-left: 3px solid #6366f1; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
          <h4 style="color: #818cf8; margin-bottom: 0.35rem;">Daily Briefing - ${data.date}</h4>
          <p style="font-size: 0.95rem; color: #f3f4f6;">${data.executive_summary}</p>
        </div>
      `;
    }

    if (data.articles && data.articles.length > 0) {
      container.innerHTML = data.articles.map(art => `
        <div class="article-digest-card">
          <div class="article-meta">
            <span><strong>${art.source}</strong></span>
            <span>•</span>
            <span>Credibility: <strong style="color: #10b981;">${art.credibility_score}/100</strong></span>
            <span>•</span>
            <span>${art.published}</span>
          </div>
          <h3 class="article-title"><a href="${art.url}" target="_blank" rel="noopener">${art.title}</a></h3>
          <p style="margin-top: 0.5rem; font-size: 0.92rem; color: #d1d5db;">${art.summary}</p>
          <div style="margin-top: 0.75rem; background: rgba(0, 0, 0, 0.25); padding: 0.6rem 0.85rem; border-radius: 6px;">
            <strong style="font-size: 0.75rem; color: #9ca3af; text-transform: uppercase;">Key Takeaways:</strong>
            ${art.key_points ? art.key_points.map(pt => `<div class="article-bullet">${pt}</div>`).join('') : ''}
          </div>
        </div>
      `).join('');
    } else {
      container.innerHTML = `<p style="color: #9ca3af;">No stories found for this category.</p>`;
    }
  } catch (err) {
    container.innerHTML = `<p style="color: #ef4444;">Failed to load news digest: ${err.message}</p>`;
  }
}

// -------------------------------------------------------------------------
// MCP Protocol Testing
// -------------------------------------------------------------------------
async function executeMcpTool() {
  const toolSelect = document.getElementById('mcp-tool-select');
  const paramInput = document.getElementById('mcp-tool-param');
  const viewer = document.getElementById('mcp-output-viewer');

  const toolName = toolSelect.value;
  let args = {};

  if (toolName === 'fact_check_claim') {
    args = { claim: paramInput.value || "5G cell towers cause viral infection" };
  } else if (toolName === 'get_daily_digest') {
    args = { category: paramInput.value || "Technology", limit: 3 };
  } else if (toolName === 'verify_source_credibility') {
    args = { domain_or_url: paramInput.value || "reuters.com" };
  } else if (toolName === 'analyze_headline_clickbait') {
    args = { headline: paramInput.value || "YOU WON'T BELIEVE THIS SHOCKING SECRET!" };
  } else if (toolName === 'search_rag_knowledge_base') {
    args = { query: paramInput.value || "exoplanet atmosphere biosignature", top_k: 2 };
  }

  viewer.textContent = "Executing tool call via MCP protocol...";

  try {
    const resp = await fetch('/api/mcp/tool/call', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: toolName, arguments: args })
    });
    const result = await resp.json();
    viewer.textContent = JSON.stringify(result, null, 2);
  } catch (err) {
    viewer.textContent = `Error executing MCP tool: ${err.message}`;
  }
}

// -------------------------------------------------------------------------
// History Loading
// -------------------------------------------------------------------------
async function loadHistory() {
  const container = document.getElementById('history-feed');
  if (!container) return;

  try {
    const resp = await fetch('/api/history');
    const data = await resp.json();

    if (data.fact_checks && data.fact_checks.length > 0) {
      container.innerHTML = data.fact_checks.map((fc, idx) => `
        <div class="card" style="margin-bottom: 1rem; padding: 1.25rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <strong>#${idx + 1}: ${fc.claim}</strong>
            <span class="verdict-badge ${fc.verdict === 'TRUE' ? 'badge-true' : (fc.verdict === 'FALSE' ? 'badge-false' : 'badge-misleading')}" style="font-size: 0.8rem; padding: 0.2rem 0.6rem;">
              ${fc.verdict}
            </span>
          </div>
          <p style="font-size: 0.88rem; color: #9ca3af;">${fc.summary}</p>
        </div>
      `).join('');
    } else {
      container.innerHTML = `<p style="color: #9ca3af; padding: 1.5rem; text-align: center;">No queries performed yet in this session. Run a fact-check to view history!</p>`;
    }
  } catch (err) {
    container.innerHTML = `<p style="color: #ef4444;">Error fetching history: ${err.message}</p>`;
  }
}
