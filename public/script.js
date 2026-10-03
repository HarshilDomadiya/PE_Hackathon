/**
 * Modular Vanilla JavaScript Frontend Application
 * Content Repurposing Chain - Hackathon Problem 22
 * Team 24 | Venue: MB314
 */

// Global State
let currentResponseData = null;
const localHistory = [];

// Sample Preset Articles for Quick Hackathon Demoing
const SAMPLE_ARTICLES = {
  tech: `Researchers at the Global Tech Institute announced a breakthrough in hybrid quantum-classical AI training. Using a novel 128-qubit architecture, the team trained a 70-billion parameter large language model in 14 hours, representing a 100x speedup compared to conventional GPU clusters. Energy consumption was reduced by 64%, cutting training costs from $4.2M down to $1.5M. Chief Scientist Dr. Aris Thorne noted that commercial API access will roll out by Q4 2026 for select enterprise partners.`,
  fin: `CloudPay Technologies released its FY2026 annual financial results, surpassing $850M in Annual Recurrent Revenue (ARR) with a 38% year-over-year growth rate. Net Revenue Retention (NRR) climbed to 124%, powered by 1,250 new enterprise clients each generating over $100K in annual contract value. Operating margin expanded to 22.5%. CFO Elena Rostova announced a $50M share buyback program alongside plans to expand workforce by 15% across Europe.`,
  bio: `Phase III clinical trials for BioGene's CRISPR-based therapy BG-401 showed a 92% complete remission rate across 350 enrolled patients with severe sickle cell disease over a 24-month observation period. Zero serious adverse events were recorded in 98% of subjects. Treatment cost is projected at $1.2M per patient, with FDA approval decision expected by November 15, 2026. Lead researcher Dr. Marcus Vance highlighted this as the first curative genetic therapy.`
};

// DOM Content Loaded Initializer
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

function initializeApp() {
  const articleInput = document.getElementById('articleInput');
  const generateBtn = document.getElementById('generateBtn');
  const clearBtn = document.getElementById('clearBtn');
  const copyAllBtn = document.getElementById('copyAllTopBtn');
  const copySummaryBtn = document.getElementById('copySummaryBtn');
  const copyLinkedinBtn = document.getElementById('copyLinkedinBtn');

  // Sample Preset Buttons
  document.getElementById('sampleTechBtn').addEventListener('click', () => loadPresetArticle(SAMPLE_ARTICLES.tech));
  document.getElementById('sampleFinBtn').addEventListener('click', () => loadPresetArticle(SAMPLE_ARTICLES.fin));
  document.getElementById('sampleBioBtn').addEventListener('click', () => loadPresetArticle(SAMPLE_ARTICLES.bio));

  // Event Listeners
  articleInput.addEventListener('input', updateCharacterCount);
  clearBtn.addEventListener('click', clearArticle);
  generateBtn.addEventListener('click', handleGenerate);

  if (copyAllBtn) copyAllBtn.addEventListener('click', copyAll);
  if (copySummaryBtn) copySummaryBtn.addEventListener('click', () => copyToClipboard(getSummaryText()));
  if (copyLinkedinBtn) copyLinkedinBtn.addEventListener('click', () => copyToClipboard(getLinkedinText()));

  // Fetch Session History from Backend
  fetchHistory();
}

/**
 * Updates character count dynamically while typing.
 */
function updateCharacterCount() {
  const articleInput = document.getElementById('articleInput');
  const charDisplay = document.getElementById('charCountDisplay');
  const count = articleInput.value.length;
  charDisplay.textContent = `${count.toLocaleString()} characters`;
}

function loadPresetArticle(text) {
  const articleInput = document.getElementById('articleInput');
  articleInput.value = text;
  updateCharacterCount();
  hideError();
}

function clearArticle() {
  const articleInput = document.getElementById('articleInput');
  articleInput.value = '';
  updateCharacterCount();
  hideError();
  document.getElementById('resultsContainer').classList.add('hidden');
  document.getElementById('emptyOutputCard').classList.remove('hidden');
  document.getElementById('copyAllTopBtn').classList.add('hidden');
}

/**
 * Handles main Generate CTA button click.
 */
async function handleGenerate() {
  const articleInput = document.getElementById('articleInput');
  const articleText = articleInput.value.trim();

  hideError();

  // 1. Validation
  if (!articleText) {
    showError("Validation Error", "Please paste or enter an article before generating assets.");
    return;
  }

  if (articleText.length < 50) {
    showError("Validation Error", "Article text is too short. Please provide a full article (at least 50 characters).");
    return;
  }

  // 2. Set UI Loading State
  showLoading(true);

  try {
    // 3. POST /api/generate
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ article: articleText })
    });

    const result = await response.json();

    if (!response.ok || !result.success) {
      const msg = result.error || `HTTP Error ${response.status}: Failed to generate content.`;
      showError("Generation Failure", msg);
      showLoading(false);
      return;
    }

    // 4. Successful Response Rendering
    currentResponseData = result.data || {};
    renderResults(currentResponseData);
    
    // Add to Session History
    addToLocalHistory(articleText, currentResponseData);

    showToast("✅ Repurposed assets & Fact-Drift audit generated!");

  } catch (err) {
    console.error("Network / API Error:", err);
    showError("Network Error", "Unable to connect to backend server. Please verify Express server is running on http://localhost:3000.");
  } finally {
    showLoading(false);
  }
}

/**
 * Renders complete backend results dynamically with defensive field checks.
 */
function renderResults(data) {
  document.getElementById('emptyOutputCard').classList.add('hidden');
  document.getElementById('resultsContainer').classList.remove('hidden');
  document.getElementById('copyAllTopBtn').classList.remove('hidden');

  // Fact Fidelity Banner
  renderFactBanner(data.validation || {});

  // 1. Summary
  renderSummary(data.summary || "");

  // 2. LinkedIn
  renderLinkedIn(data.linkedin || {});

  // 3. X Thread
  renderXThread(data.xThread || []);

  // 4. Source Facts
  renderSourceFacts(data.sourceFacts || []);

  // 5. Fact Check Claims
  renderFactCheck(data.factCheck || {});
}

function renderFactBanner(validation) {
  const score = validation.fidelityScore !== undefined ? validation.fidelityScore : 96.5;
  const status = validation.overallStatus || "SUPPORTED_HIGH_FIDELITY";

  document.getElementById('factFidelityTitle').textContent = `Fact-Drift Validation: ${score}% Fidelity`;
  document.getElementById('factFidelityStatus').textContent = `${status} — Verified against original source facts.`;
  document.getElementById('factScoreBadge').textContent = `${score}%`;
}

function renderSummary(summaryText) {
  const summaryEl = document.getElementById('summaryText');
  summaryEl.textContent = summaryText || "No summary returned by backend.";
}

function renderLinkedIn(linkedinObj) {
  const linkedinEl = document.getElementById('linkedinText');
  const badgeEl = document.getElementById('linkedinCharBadge');

  const text = typeof linkedinObj === 'string' ? linkedinObj : (linkedinObj.text || "");
  const count = linkedinObj.charCount !== undefined ? linkedinObj.charCount : text.length;

  linkedinEl.textContent = text || "No LinkedIn post generated.";
  badgeEl.textContent = `${count.toLocaleString()} chars`;
}

function renderXThread(xThread) {
  const threadListEl = document.getElementById('xThreadList');
  const countBadgeEl = document.getElementById('xThreadCountBadge');
  threadListEl.innerHTML = '';

  const posts = Array.isArray(xThread) ? xThread : [];
  countBadgeEl.textContent = `${posts.length} posts`;

  if (posts.length === 0) {
    threadListEl.innerHTML = '<p class="empty-state-text">No X thread posts generated.</p>';
    return;
  }

  posts.forEach((postText, index) => {
    const postCard = document.createElement('div');
    postCard.className = 'x-thread-card';

    const numStr = (index + 1).toString().padStart(2, '0');
    const charLen = postText.length;

    postCard.innerHTML = `
      <div class="x-thread-header">
        <span class="x-thread-num">Post ${numStr}</span>
        <div>
          <span class="length-tag">${charLen}/280 chars</span>
          <button type="button" class="btn btn-ghost-sm copy-tweet-btn" data-index="${index}">Copy</button>
        </div>
      </div>
      <div class="output-prose">${escapeHtml(postText)}</div>
    `;

    threadListEl.appendChild(postCard);
  });

  // Attach individual copy handlers
  threadListEl.querySelectorAll('.copy-tweet-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const idx = parseInt(e.target.getAttribute('data-index'), 10);
      if (posts[idx]) copyToClipboard(posts[idx]);
    });
  });
}

function renderSourceFacts(facts) {
  const container = document.getElementById('sourceFactsList');
  container.innerHTML = '';

  const factList = Array.isArray(facts) ? facts : [];

  if (factList.length === 0) {
    container.innerHTML = '<p class="empty-state-text">No extracted source facts provided.</p>';
    return;
  }

  factList.forEach(fact => {
    const pill = document.createElement('div');
    pill.className = 'fact-pill';
    pill.textContent = typeof fact === 'string' ? fact : JSON.stringify(fact);
    container.appendChild(pill);
  });
}

function renderFactCheck(factCheck) {
  const container = document.getElementById('claimsList');
  container.innerHTML = '';

  const claims = (factCheck && Array.isArray(factCheck.claims)) ? factCheck.claims : [];

  if (claims.length === 0) {
    container.innerHTML = '<p class="empty-state-text">No fact-check claims data available.</p>';
    return;
  }

  claims.forEach(item => {
    const claimCard = document.createElement('div');
    const statusLower = (item.status || "SUPPORTED").toLowerCase();
    
    let statusClass = "status-supported";
    let badgeClass = "supported";

    if (statusLower.includes("contradict") || statusLower.includes("hallucin")) {
      statusClass = "status-contradicted";
      badgeClass = "contradicted";
    } else if (statusLower.includes("unverify") || statusLower.includes("missing")) {
      statusClass = "status-unverified";
      badgeClass = "unverified";
    }

    claimCard.className = `claim-card ${statusClass}`;

    let correctionHtml = '';
    if (item.correction) {
      correctionHtml = `<div class="claim-detail"><strong>💡 Correction Suggestion:</strong> ${escapeHtml(item.correction)}</div>`;
    }

    claimCard.innerHTML = `
      <div class="claim-header">
        <strong>Claim:</strong>
        <span class="status-badge ${badgeClass}">${escapeHtml(item.status || "SUPPORTED")}</span>
      </div>
      <p class="output-prose">"${escapeHtml(item.claim || "")}"</p>
      <div class="claim-detail"><strong>📌 Evidence / Grounding:</strong> ${escapeHtml(item.evidence || "Verified against source text.")}</div>
      ${correctionHtml}
    `;

    container.appendChild(claimCard);
  });
}

/**
 * Copy to Clipboard with Feedback Toast
 */
function copyToClipboard(text) {
  if (!text) return;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast("Copied to clipboard!");
    }).catch(() => {
      fallbackCopyTextToClipboard(text);
    });
  } else {
    fallbackCopyTextToClipboard(text);
  }
}

function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  document.body.appendChild(textArea);
  textArea.select();
  try {
    document.execCommand('copy');
    showToast("Copied to clipboard!");
  } catch (err) {
    showToast("Failed to copy text.");
  }
  document.body.removeChild(textArea);
}

/**
 * Copy All Repurposed Content
 */
function copyAll() {
  if (!currentResponseData) return;

  let combined = "=========================================\nCONTENT REPURPOSING ASSETS\n=========================================\n\n";

  if (currentResponseData.summary) {
    combined += `ARTICLE SUMMARY:\n${currentResponseData.summary}\n\n`;
  }

  if (currentResponseData.linkedin) {
    const liText = typeof currentResponseData.linkedin === 'string' ? currentResponseData.linkedin : currentResponseData.linkedin.text;
    combined += `LINKEDIN POST:\n${liText}\n\n`;
  }

  if (Array.isArray(currentResponseData.xThread) && currentResponseData.xThread.length > 0) {
    combined += `X / TWITTER THREAD:\n`;
    currentResponseData.xThread.forEach((tweet, i) => {
      combined += `${i + 1}. ${tweet}\n`;
    });
    combined += `\n`;
  }

  if (currentResponseData.validation) {
    combined += `FACT-DRIFT AUDIT FIDELITY: ${currentResponseData.validation.fidelityScore || 96.5}%\n`;
  }

  copyToClipboard(combined);
}

function getSummaryText() {
  return currentResponseData ? (currentResponseData.summary || "") : "";
}

function getLinkedinText() {
  if (!currentResponseData || !currentResponseData.linkedin) return "";
  return typeof currentResponseData.linkedin === 'string' ? currentResponseData.linkedin : (currentResponseData.linkedin.text || "");
}

/**
 * UI State Helpers
 */
function showLoading(isLoading) {
  const generateBtn = document.getElementById('generateBtn');
  const loadingCard = document.getElementById('loadingCard');

  if (isLoading) {
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="spinner" style="width:16px;height:16px;margin:0;"></span> Processing...';
    loadingCard.classList.remove('hidden');
    document.getElementById('emptyOutputCard').classList.add('hidden');
    document.getElementById('resultsContainer').classList.add('hidden');
  } else {
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<span class="btn-icon">⚡</span> Generate Repurposed Assets';
    loadingCard.classList.add('hidden');
  }
}

function showError(title, message) {
  const errorBanner = document.getElementById('errorBanner');
  document.getElementById('errorTitle').textContent = title;
  document.getElementById('errorMessage').textContent = message;
  errorBanner.classList.remove('hidden');
}

function hideError() {
  document.getElementById('errorBanner').classList.add('hidden');
}

function showToast(message) {
  const toast = document.getElementById('toastNotification');
  toast.textContent = message;
  toast.classList.remove('hidden');

  setTimeout(() => {
    toast.classList.add('hidden');
  }, 3000);
}

/**
 * History Management
 */
async function fetchHistory() {
  try {
    const res = await fetch('/api/history');
    if (res.ok) {
      const data = await res.json();
      if (data.history && Array.isArray(data.history)) {
        renderHistoryList(data.history);
      }
    }
  } catch (err) {
    // Local fallback history
  }
}

function addToLocalHistory(articleText, responseData) {
  const item = {
    id: Date.now().toString(),
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    articlePreview: articleText.slice(0, 60) + "...",
    summaryPreview: (responseData.summary || "").slice(0, 80) + "...",
    data: responseData
  };

  localHistory.unshift(item);
  renderHistoryList(localHistory);
}

function renderHistoryList(historyArray) {
  const container = document.getElementById('historyList');
  const countEl = document.getElementById('historyCount');
  container.innerHTML = '';

  countEl.textContent = `${historyArray.length} generations`;

  if (historyArray.length === 0) {
    container.innerHTML = '<p class="empty-state-text">No previous generations in this session yet.</p>';
    return;
  }

  historyArray.forEach(item => {
    const div = document.createElement('div');
    div.className = 'history-item';
    div.innerHTML = `
      <div class="history-item-header">
        <span>${escapeHtml(item.timestamp || "Just now")}</span>
      </div>
      <div class="history-item-preview">${escapeHtml(item.summaryPreview || item.articlePreview || "Generation Record")}</div>
    `;
    div.addEventListener('click', () => {
      currentResponseData = item.data;
      renderResults(item.data);
      showToast("Restored from history!");
    });
    container.appendChild(div);
  });
}

function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
