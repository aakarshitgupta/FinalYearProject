const root = document.getElementById("root");

const state = {
  config: null,
  history: { enabled: false, items: [] },
  analysis: null,
  batchResult: null,
  loadingConfig: true,
  analyzing: false,
  runningBatch: false,
  error: "",
  text:
    "A viral post claims that researchers have secretly hidden a miracle cure from the public for years.",
  method: "lime",
  topK: 10,
  saveHistory: true,
  batchText: "",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderMetricCard(label, value, accent) {
  return `
    <div class="metric-card">
      <span class="metric-label">${escapeHtml(label)}</span>
      <strong class="metric-value" style="color: ${accent};">${escapeHtml(value)}</strong>
    </div>
  `;
}

function renderProbabilityRows(probabilities = {}) {
  return Object.entries(probabilities)
    .map(([label, probability]) => {
      const percent = Number(probability || 0) * 100;
      return `
        <div class="probability-row">
          <span>${escapeHtml(label)}</span>
          <div class="probability-track">
            <div class="probability-fill" style="width: ${Math.max(percent, 3)}%"></div>
          </div>
          <strong>${percent.toFixed(1)}%</strong>
        </div>
      `;
    })
    .join("");
}

function renderExplanationRows(items = []) {
  return items
    .map(
      (item) => `
        <div class="feature-row">
          <div>
            <strong>${escapeHtml(item.feature)}</strong>
            <span>${item.importance >= 0 ? "Supports fake" : "Supports real"}</span>
          </div>
          <em>${Number(item.importance || 0).toFixed(4)}</em>
        </div>
      `
    )
    .join("");
}

function renderBatchRows(items = []) {
  return items
    .map(
      (item) => `
        <tr>
          <td>${escapeHtml(item.text)}</td>
          <td>${escapeHtml(item.prediction?.label_name || "")}</td>
          <td>${((item.prediction?.confidence || 0) * 100).toFixed(1)}%</td>
        </tr>
      `
    )
    .join("");
}

function renderHistoryRows(items = []) {
  return items
    .map(
      (item) => `
        <article class="history-card">
          <div class="history-topline">
            <strong>${escapeHtml((item.prediction?.label_name || "").toUpperCase())}</strong>
            <span>${escapeHtml(new Date(item.createdAt).toLocaleString())}</span>
          </div>
          <p>${escapeHtml(item.inputText)}</p>
        </article>
      `
    )
    .join("");
}

function renderDatasetRows(preview = []) {
  return preview
    .map(
      (row) => `
        <tr>
          <td>${escapeHtml(row.text)}</td>
          <td>${escapeHtml(row.label)}</td>
        </tr>
      `
    )
    .join("");
}

function render() {
  const summary = state.config?.trainingSummary || {};
  const metrics = summary.metrics || {};
  const dataset = state.config?.dataset || {};
  const prediction = state.analysis?.prediction || null;
  const explanation = state.analysis?.explanation || [];

  root.innerHTML = `
    <div class="app-shell">
      <header class="hero">
        <div class="hero-copy">
          <span class="eyebrow">MERN rebuild</span>
          <h1>Fake News XAI Studio</h1>
          <p>
            Browser-safe frontend, Express API, Python BERT inference, and optional Mongo history.
          </p>
        </div>
        <div class="hero-status">
          <div class="status-pill">${state.loadingConfig ? "Loading model..." : "API ready"}</div>
          <div class="status-grid">
            ${renderMetricCard("Model", state.config?.modelReady ? "Loaded" : "Missing", "#f97316")}
            ${renderMetricCard(
              "Eval F1",
              metrics.eval_f1 ? `${(metrics.eval_f1 * 100).toFixed(1)}%` : "N/A",
              "#22c55e"
            )}
            ${renderMetricCard("Dataset rows", dataset.totalRows ?? "N/A", "#38bdf8")}
          </div>
        </div>
      </header>

      ${state.error ? `<div class="error-banner">${escapeHtml(state.error)}</div>` : ""}

      <main class="content-grid">
        <section class="panel">
          <div class="panel-heading">
            <div>
              <h2>Model workspace</h2>
              <p>This section reads your model summary and dataset preview from the API.</p>
            </div>
          </div>

          <div class="details-grid">
            <div class="detail-box">
              <span>Model directory</span>
              <strong>${escapeHtml(state.config?.modelDir || "Not configured")}</strong>
            </div>
            <div class="detail-box">
              <span>Explanation methods</span>
              <strong>LIME and SHAP</strong>
            </div>
            <div class="detail-box">
              <span>Mongo history</span>
              <strong>${state.history.enabled ? "Enabled" : "Optional / off"}</strong>
            </div>
            <div class="detail-box">
              <span>Training epochs</span>
              <strong>${escapeHtml(summary.epochs ?? "N/A")}</strong>
            </div>
          </div>

          <div class="preview-table">
            <div class="table-header">
              <h3>Dataset preview</h3>
              <span>${escapeHtml(dataset.totalRows ?? 0)} rows available</span>
            </div>
            <div class="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Text</th>
                    <th>Label</th>
                  </tr>
                </thead>
                <tbody>${renderDatasetRows(dataset.preview || [])}</tbody>
              </table>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-heading">
            <div>
              <h2>Single analysis</h2>
              <p>Score a claim, inspect confidence, and review explanation weights.</p>
            </div>
          </div>

          <form id="analysis-form" class="analysis-form">
            <label>
              News text
              <textarea id="text-input" rows="8">${escapeHtml(state.text)}</textarea>
            </label>

            <div class="form-row">
              <label>
                Method
                <select id="method-input">
                  <option value="lime" ${state.method === "lime" ? "selected" : ""}>LIME</option>
                  <option value="shap" ${state.method === "shap" ? "selected" : ""}>SHAP</option>
                </select>
              </label>

              <label>
                Top features
                <input id="topk-input" type="number" min="5" max="20" value="${escapeHtml(state.topK)}" />
              </label>
            </div>

            <label class="checkbox-row">
              <input id="save-history-input" type="checkbox" ${state.saveHistory ? "checked" : ""} />
              Save this result when MongoDB is connected
            </label>

            <button class="primary-button" type="submit" ${state.analyzing ? "disabled" : ""}>
              ${state.analyzing ? "Analyzing..." : "Analyze article"}
            </button>
          </form>

          ${
            prediction
              ? `
                <div class="analysis-output">
                  <div class="verdict-card">
                    <span>Predicted verdict</span>
                    <strong class="${prediction.label_name === "fake" ? "fake-text" : "real-text"}">
                      ${escapeHtml(prediction.label_name.toUpperCase())}
                    </strong>
                    <p>Confidence ${Math.round((prediction.confidence || 0) * 100)}%</p>
                  </div>

                  <div class="probability-list">
                    ${renderProbabilityRows(prediction.probabilities)}
                  </div>

                  <div class="feature-list">
                    <div class="table-header">
                      <h3>${escapeHtml(state.method.toUpperCase())} explanation</h3>
                      <span>${escapeHtml(explanation.length)} features</span>
                    </div>
                    ${renderExplanationRows(explanation)}
                  </div>
                </div>
              `
              : ""
          }
        </section>

        <section class="panel">
          <div class="panel-heading">
            <div>
              <h2>Batch screening</h2>
              <p>Paste one text per line to run multiple predictions in one request.</p>
            </div>
          </div>

          <textarea id="batch-input" rows="8" placeholder="Paste one claim or headline per line">${escapeHtml(
            state.batchText
          )}</textarea>
          <button id="batch-button" class="secondary-button" type="button" ${
            state.runningBatch ? "disabled" : ""
          }>
            ${state.runningBatch ? "Running batch..." : "Run batch analysis"}
          </button>

          ${
            state.batchResult
              ? `
                <div class="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Text</th>
                        <th>Label</th>
                        <th>Confidence</th>
                      </tr>
                    </thead>
                    <tbody>${renderBatchRows(state.batchResult.items || [])}</tbody>
                  </table>
                </div>
              `
              : ""
          }
        </section>

        <section class="panel">
          <div class="panel-heading">
            <div>
              <h2>Recent history</h2>
              <p>These records appear only when MongoDB is connected.</p>
            </div>
          </div>

          ${
            state.history.enabled && state.history.items.length
              ? `<div class="history-list">${renderHistoryRows(state.history.items)}</div>`
              : `<p class="muted-copy">Connect MongoDB to persist analysis history. Without it, the app still supports full inference and explanation.</p>`
          }
        </section>
      </main>
    </div>
  `;

  attachEvents();
}

function attachEvents() {
  const analysisForm = document.getElementById("analysis-form");
  const batchButton = document.getElementById("batch-button");
  const textInput = document.getElementById("text-input");
  const methodInput = document.getElementById("method-input");
  const topkInput = document.getElementById("topk-input");
  const saveHistoryInput = document.getElementById("save-history-input");
  const batchInput = document.getElementById("batch-input");

  if (textInput) {
    textInput.addEventListener("input", (event) => {
      state.text = event.target.value;
    });
  }

  if (methodInput) {
    methodInput.addEventListener("change", (event) => {
      state.method = event.target.value;
    });
  }

  if (topkInput) {
    topkInput.addEventListener("input", (event) => {
      state.topK = Number(event.target.value || 10);
    });
  }

  if (saveHistoryInput) {
    saveHistoryInput.addEventListener("change", (event) => {
      state.saveHistory = event.target.checked;
    });
  }

  if (batchInput) {
    batchInput.addEventListener("input", (event) => {
      state.batchText = event.target.value;
    });
  }

  if (analysisForm) {
    analysisForm.addEventListener("submit", handleAnalyze);
  }

  if (batchButton) {
    batchButton.addEventListener("click", handleBatchAnalyze);
  }
}

async function loadHistory() {
  const response = await fetch("/api/history");
  const data = await response.json();
  state.history = {
    enabled: Boolean(data?.enabled),
    items: Array.isArray(data?.items) ? data.items : [],
  };
}

async function loadConfig() {
  try {
    const response = await fetch("/api/config");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Failed to load API config.");
    }
    state.config = data;
    await loadHistory();
  } catch (error) {
    state.error = error.message;
  } finally {
    state.loadingConfig = false;
    render();
  }
}

async function handleAnalyze(event) {
  event.preventDefault();
  state.error = "";
  state.analyzing = true;
  render();

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: state.text,
        method: state.method,
        topK: state.topK,
        saveHistory: state.saveHistory,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Analysis request failed.");
    }

    state.analysis = data;
    if (state.saveHistory) {
      await loadHistory();
    }
  } catch (error) {
    state.error = error.message;
  } finally {
    state.analyzing = false;
    render();
  }
}

async function handleBatchAnalyze() {
  const texts = state.batchText
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

  if (!texts.length) {
    state.error = "Enter at least one line of text for batch analysis.";
    render();
    return;
  }

  state.error = "";
  state.runningBatch = true;
  render();

  try {
    const response = await fetch("/api/batch", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ texts }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Batch analysis failed.");
    }

    state.batchResult = data;
  } catch (error) {
    state.error = error.message;
  } finally {
    state.runningBatch = false;
    render();
  }
}

render();
loadConfig();
