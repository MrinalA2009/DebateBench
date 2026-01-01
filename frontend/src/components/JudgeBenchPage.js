import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './JudgeBenchPage.css';

const API_URL = 'http://localhost:8001';

const DEFAULT_JUDGE_MODELS = [
  'anthropic/claude-sonnet-4.5',
  'x-ai/grok-4.1-fast',
  'openai/gpt-4o-mini'
];

const JUDGE_PROMPTS = ['p0', 'p1', 'p2'];

function JudgeBenchPage() {
  const [step, setStep] = useState('config'); // config, run, results
  const [config, setConfig] = useState(null);
  const [selectedModels, setSelectedModels] = useState(DEFAULT_JUDGE_MODELS);
  const [runsPerDebate, setRunsPerDebate] = useState(3);
  const [temperature, setTemperature] = useState(0.1);
  const [judgebenchDebates, setJudgebenchDebates] = useState([]);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [results, setResults] = useState(null);

  useEffect(() => {
    loadConfig();
    loadJudgebenchDebates();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/judgebench/config`);
      if (response.data.config) {
        setConfig(response.data.config);
      }
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const loadJudgebenchDebates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/judgebench/debates`);
      setJudgebenchDebates(response.data.debates || []);
    } catch (error) {
      console.error('Error loading JudgeBench debates:', error);
    }
  };

  const saveConfig = async () => {
    try {
      await axios.post(`${API_URL}/api/judgebench/config`, {
        judge_models: selectedModels,
        judge_prompts: JUDGE_PROMPTS,
        num_debates: judgebenchDebates.length,
        runs_per_debate: runsPerDebate,
        temperature: temperature
      });
      await loadConfig();
      setStep('run');
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Failed to save configuration');
    }
  };

  const runExperiment = async () => {
    if (!config) return;

    setRunning(true);
    const totalConfigs = config.judge_models.length * config.judge_prompts.length;
    let completed = 0;

    setProgress({ current: 0, total: totalConfigs });

    try {
      for (const model of config.judge_models) {
        for (const prompt of config.judge_prompts) {
          try {
            await axios.post(`${API_URL}/api/judgebench/run`, {
              judge_model: model,
              judge_prompt: prompt,
              temperature: config.temperature
            });
            completed++;
            setProgress({ current: completed, total: totalConfigs });
          } catch (error) {
            console.error(`Error running ${model} with ${prompt}:`, error);
          }
        }
      }

      // Load results
      await loadResults();
      setStep('results');
    } catch (error) {
      console.error('Error running experiment:', error);
      alert('Experiment failed');
    } finally {
      setRunning(false);
    }
  };

  const loadResults = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/judgebench/results`);
      setResults(response.data);
    } catch (error) {
      console.error('Error loading results:', error);
    }
  };

  const toggleModel = (model) => {
    if (selectedModels.includes(model)) {
      setSelectedModels(selectedModels.filter(m => m !== model));
    } else {
      setSelectedModels([...selectedModels, model]);
    }
  };

  return (
    <div className="judgebench-page">
      <div className="judgebench-header">
        <h1>JudgeBench</h1>
        <p>Meta-Evaluation: Select the Most Stable Judge Configuration</p>
        <div className="step-indicator">
          <span className={step === 'config' ? 'active' : ''}>1. Configure</span>
          <span className={step === 'run' ? 'active' : ''}>2. Run Experiment</span>
          <span className={step === 'results' ? 'active' : ''}>3. Results</span>
        </div>
      </div>

      {step === 'config' && (
        <div className="config-section">
          <h2>Step 1: Lock JudgeBench Scope</h2>

          {judgebenchDebates.length === 0 ? (
            <div className="config-warning">
              <h3>⚠️ No JudgeBench Debates Found</h3>
              <p>Please go to the "JudgeBench Debates" tab first to generate the 25 paired debates.</p>
            </div>
          ) : (
            <>
              <div className="config-item">
                <h3>JudgeBench Debates</h3>
                <div className="prompts-info">
                  <div>✓ {judgebenchDebates.length} debate instances loaded</div>
                  <div>✓ Ready for judge evaluation</div>
                </div>
              </div>

              <div className="config-item">
                <h3>Judge Models ({selectedModels.length} selected)</h3>
                <div className="model-checkboxes">
                  {DEFAULT_JUDGE_MODELS.map(model => (
                    <label key={model} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={selectedModels.includes(model)}
                        onChange={() => toggleModel(model)}
                      />
                      <span>{model}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="config-item">
                <h3>Judge Prompts (All 3)</h3>
                <div className="prompts-info">
                  <div>P0 - Main Prompt (Baseline)</div>
                  <div>P1 - Procedural (Two-Stage Reasoning)</div>
                  <div>P2 - Weighing Emphasis Variant</div>
                </div>
              </div>

              <div className="config-row">
                <div className="config-field">
                  <label>Runs per Debate</label>
                  <input
                    type="number"
                    value={runsPerDebate}
                    onChange={(e) => setRunsPerDebate(parseInt(e.target.value))}
                    min="1"
                    max="10"
                  />
                </div>

                <div className="config-field">
                  <label>Judge Temperature</label>
                  <input
                    type="number"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    min="0.0"
                    max="1.0"
                  />
                </div>
              </div>

              <div className="config-summary">
                <h4>Experiment Size</h4>
                <div>Judge Configurations: {selectedModels.length} models × 3 prompts = <strong>{selectedModels.length * 3}</strong></div>
                <div>Total Judgments: {judgebenchDebates.length} debates × {runsPerDebate} runs × {selectedModels.length * 3} configs = <strong>{judgebenchDebates.length * runsPerDebate * selectedModels.length * 3}</strong></div>
              </div>

              <button
                className="btn-primary"
                onClick={saveConfig}
                disabled={selectedModels.length === 0}
              >
                Lock Configuration & Continue
              </button>
            </>
          )}
        </div>
      )}

      {step === 'run' && (
        <div className="run-section">
          <h2>Step 2: Run JudgeBench Experiment</h2>

          <div className="experiment-info">
            <h3>Experiment Configuration</h3>
            <div>Judge Configurations: {config?.judge_models?.length || 0} × 3 = {(config?.judge_models?.length || 0) * 3}</div>
            <div>Debates: {judgebenchDebates.length}</div>
            <div>Runs per Debate: {config?.runs_per_debate || 0}</div>
            <div>Total Judgments: {judgebenchDebates.length * (config?.runs_per_debate || 0) * ((config?.judge_models?.length || 0) * 3)}</div>
          </div>

          {running && (
            <div className="progress-section">
              <h4>Running Experiment...</h4>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                ></div>
              </div>
              <p>{progress.current} / {progress.total} configurations complete</p>
            </div>
          )}

          <button
            className="btn-primary"
            onClick={runExperiment}
            disabled={running}
          >
            {running ? 'Running...' : 'Run Full Experiment'}
          </button>

          {!running && (
            <button
              className="btn-secondary"
              onClick={loadResults}
            >
              View Results
            </button>
          )}
        </div>
      )}

      {step === 'results' && results && (
        <div className="results-section">
          <h2>JudgeBench Results</h2>

          <div className="rankings-table">
            <h3>Judge Configuration Rankings</h3>
            <p>Lower instability score is better</p>
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Judge Configuration</th>
                  <th>Instability Score</th>
                  <th>Flip Rate</th>
                  <th>Side Bias</th>
                </tr>
              </thead>
              <tbody>
                {results.rankings?.map((item, index) => {
                  const [config, score] = item;
                  const metrics = results.metrics[config];
                  return (
                    <tr key={config} className={index === 0 ? 'best-config' : ''}>
                      <td>{index + 1}</td>
                      <td>{config}</td>
                      <td>{score.toFixed(4)}</td>
                      <td>{(metrics.flip_rate * 100).toFixed(1)}%</td>
                      <td>{(metrics.side_bias * 100).toFixed(1)}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="metrics-details">
            <h3>Detailed Metrics</h3>
            {Object.entries(results.metrics).map(([config, metrics]) => (
              <div key={config} className="metric-card">
                <h4>{config}</h4>
                <div className="metric-grid">
                  <div className="metric-item">
                    <span className="metric-label">Winner Flip Rate:</span>
                    <span className="metric-value">{(metrics.flip_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Side Bias:</span>
                    <span className="metric-value">{(metrics.side_bias * 100).toFixed(1)}%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Confidence Variance:</span>
                    <span className="metric-value">{metrics.confidence_variance.toFixed(4)}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Total Judgments:</span>
                    <span className="metric-value">{metrics.total_judgments}</span>
                  </div>
                </div>
                <div className="score-variances">
                  <h5>Score Variances by Category</h5>
                  {Object.entries(metrics.score_variance).map(([category, variance]) => (
                    <div key={category} className="variance-item">
                      <span>{category}:</span>
                      <span>{variance.toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {results.rankings && results.rankings.length > 0 && (
            <div className="recommendation">
              <h3>Recommended Judge Configuration</h3>
              <div className="recommended-config">
                <strong>{results.rankings[0][0]}</strong>
                <p>This configuration showed the lowest instability and should be used for the main DebateBench.</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default JudgeBenchPage;
