import React, { useEffect, useState } from "react";

const sampleText =
  "A viral post claims that researchers have secretly hidden a miracle cure from the public for years.";

function MetricCard({ label, value, accent }) {
  return (
    <div className="metric-card">
      <span className="metric-label">{label}</span>
      <strong className="metric-value" style={{ color: accent }}>
        {value}
      </strong>
    </div>
  );
}

function SectionCard({ title, children, subtitle }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || "Unexpected frontend error." };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="app-shell">
          <div className="error-banner">
            Frontend render error: {this.state.message}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function AppContent() {
  const [config, setConfig] = useState(null);
  const [text, setText] = useState(sampleText);
  const [method, setMethod] = useState("lime");
  const [topK, setTopK] = useState(10);
  const [saveHistory, setSaveHistory] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [batchText, setBatchText] = useState("");
  const [batchResult, setBatchResult] = useState(null);
  const [history, setHistory] = useState({ enabled: false, items: [] });
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [runningBatch, setRunningBatch] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [configResponse, historyResponse] = await Promise.all([
          fetch("/api/config"),
          fetch("/api/history"),
        ]);

        const configJson = await configResponse.json();
        const historyJson = await historyResponse.json();

        if (!configResponse.ok) {
          throw new Error(configJson.error || "Failed to load API config.");
        }

        setConfig(configJson);
        setHistory({
          enabled: Boolean(historyJson?.enabled),
          items: Array.isArray(historyJson?.items) ? historyJson.items : [],
        });
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoadingConfig(false);
      }
    }

    loadInitialData();
  }, []);

  async function handleAnalyze(event) {
    event.preventDefault();
    setError("");
    setAnalyzing(true);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text,
          method,
          topK,
          saveHistory,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Analysis request failed.");
      }

      setAnalysis(data);
      if (saveHistory) {
        const historyResponse = await fetch("/api/history");
        const historyJson = await historyResponse.json();
        setHistory({
          enabled: Boolean(historyJson?.enabled),
          items: Array.isArray(historyJson?.items) ? historyJson.items : [],
        });
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleBatchAnalyze() {
    const texts = batchText
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);

    if (!texts.length) {
      setError("Enter at least one line of text for batch analysis.");
      return;
    }

    setError("");
    setRunningBatch(true);

    try {
      const response = await fetch("/api/batch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          texts,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Batch analysis failed.");
      }

      setBatchResult(data);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setRunningBatch(false);
    }
  }

  const summary = config?.trainingSummary || {};
  const metrics = summary.metrics || {};
  const dataset = config?.dataset || {};

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <span className="eyebrow">MERN rebuild</span>
          <h1>Fake News XAI Studio</h1>
          <p>
            React drives the interface, Express exposes the API, Python keeps the
            BERT inference pipeline, and MongoDB can store analysis history when
            you connect a database.
          </p>
        </div>
        <div className="hero-status">
          <div className="status-pill">{loadingConfig ? "Loading model..." : "API ready"}</div>
          <div className="status-grid">
            <MetricCard label="Model" value={config?.modelReady ? "Loaded" : "Missing"} accent="#f97316" />
            <MetricCard
              label="Eval F1"
              value={metrics.eval_f1 ? `${(metrics.eval_f1 * 100).toFixed(1)}%` : "N/A"}
              accent="#22c55e"
            />
            <MetricCard
              label="Dataset rows"
              value={dataset.totalRows ?? "N/A"}
              accent="#38bdf8"
            />
          </div>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <main className="content-grid">
        <SectionCard
          title="Model workspace"
          subtitle="This section reads your current training summary and dataset preview from the API."
        >
          <div className="details-grid">
            <div className="detail-box">
              <span>Model directory</span>
              <strong>{config?.modelDir || "Not configured"}</strong>
            </div>
            <div className="detail-box">
              <span>Explanation methods</span>
              <strong>LIME and SHAP</strong>
            </div>
            <div className="detail-box">
              <span>Mongo history</span>
              <strong>{history.enabled ? "Enabled" : "Optional / off"}</strong>
            </div>
            <div className="detail-box">
              <span>Training epochs</span>
              <strong>{summary.epochs ?? "N/A"}</strong>
            </div>
          </div>

          <div className="preview-table">
            <div className="table-header">
              <h3>Dataset preview</h3>
              <span>{dataset.totalRows ?? 0} rows available</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Text</th>
                    <th>Label</th>
                  </tr>
                </thead>
                <tbody>
                  {(dataset.preview || []).map((row, index) => (
                    <tr key={`${row.text}-${index}`}>
                      <td>{row.text}</td>
                      <td>{row.label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          title="Single analysis"
          subtitle="Score a claim, inspect the model confidence, and review feature-level explanation weights."
        >
          <form className="analysis-form" onSubmit={handleAnalyze}>
            <label>
              News text
              <textarea value={text} onChange={(event) => setText(event.target.value)} rows={8} />
            </label>

            <div className="form-row">
              <label>
                Method
                <select value={method} onChange={(event) => setMethod(event.target.value)}>
                  <option value="lime">LIME</option>
                  <option value="shap">SHAP</option>
                </select>
              </label>

              <label>
                Top features
                <input
                  type="number"
                  min="5"
                  max="20"
                  value={topK}
                  onChange={(event) => setTopK(Number(event.target.value))}
                />
              </label>
            </div>

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={saveHistory}
                onChange={(event) => setSaveHistory(event.target.checked)}
              />
              Save this result when MongoDB is connected
            </label>

            <button className="primary-button" type="submit" disabled={analyzing}>
              {analyzing ? "Analyzing..." : "Analyze article"}
            </button>
          </form>

          {analysis ? (
            <div className="analysis-output">
              <div className="verdict-card">
                <span>Predicted verdict</span>
                <strong className={analysis.prediction.label_name === "fake" ? "fake-text" : "real-text"}>
                  {analysis.prediction.label_name.toUpperCase()}
                </strong>
                <p>Confidence {Math.round(analysis.prediction.confidence * 100)}%</p>
              </div>

              <div className="probability-list">
                {Object.entries(analysis.prediction.probabilities).map(([label, probability]) => (
                  <div key={label} className="probability-row">
                    <span>{label}</span>
                    <div className="probability-track">
                      <div
                        className="probability-fill"
                        style={{ width: `${Math.max(probability * 100, 3)}%` }}
                      />
                    </div>
                    <strong>{(probability * 100).toFixed(1)}%</strong>
                  </div>
                ))}
              </div>

              <div className="feature-list">
                <div className="table-header">
                  <h3>{method.toUpperCase()} explanation</h3>
                  <span>{analysis.explanation.length} features</span>
                </div>
                {analysis.explanation.map((item, index) => (
                  <div className="feature-row" key={`${item.feature}-${index}`}>
                    <div>
                      <strong>{item.feature}</strong>
                      <span>{item.importance >= 0 ? "Supports fake" : "Supports real"}</span>
                    </div>
                    <em>{item.importance.toFixed(4)}</em>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Batch screening"
          subtitle="Paste one text per line to run multiple predictions in a single request."
        >
          <textarea
            rows={8}
            value={batchText}
            onChange={(event) => setBatchText(event.target.value)}
            placeholder="Paste one claim or headline per line"
          />
          <button className="secondary-button" type="button" onClick={handleBatchAnalyze} disabled={runningBatch}>
            {runningBatch ? "Running batch..." : "Run batch analysis"}
          </button>

          {batchResult ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Text</th>
                    <th>Label</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {batchResult.items.map((item, index) => (
                    <tr key={`${item.text}-${index}`}>
                      <td>{item.text}</td>
                      <td>{item.prediction.label_name}</td>
                      <td>{(item.prediction.confidence * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </SectionCard>

        <SectionCard
          title="Recent history"
          subtitle="These records appear only when MongoDB is connected through MONGODB_URI."
        >
          {history.enabled && history.items.length ? (
            <div className="history-list">
              {history.items.map((item) => (
                <article className="history-card" key={item._id}>
                  <div className="history-topline">
                    <strong>{item.prediction.label_name.toUpperCase()}</strong>
                    <span>{new Date(item.createdAt).toLocaleString()}</span>
                  </div>
                  <p>{item.inputText}</p>
                </article>
              ))}
            </div>
          ) : (
            <p className="muted-copy">
              Connect MongoDB to persist analysis history. Without it, the app still supports full inference and explanation.
            </p>
          )}
        </SectionCard>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppErrorBoundary>
      <AppContent />
    </AppErrorBoundary>
  );
}
