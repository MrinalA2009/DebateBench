import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './JudgeBenchDebatesPage.css';

const API_URL = 'http://localhost:8001';

function JudgeBenchDebatesPage() {
  const [debates, setDebates] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 25 });
  const [temperature, setTemperature] = useState(1.0);
  const [expandedDebates, setExpandedDebates] = useState(new Set());

  useEffect(() => {
    loadDebates();
    // Auto-refresh every 5 seconds when generating
    const interval = setInterval(() => {
      if (generating) {
        loadDebates();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [generating]);

  const loadDebates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/judgebench/debates`);
      setDebates(response.data.debates || []);
    } catch (error) {
      console.error('Error loading debates:', error);
    }
  };

  const toggleDebate = (debateId) => {
    const newExpanded = new Set(expandedDebates);
    if (newExpanded.has(debateId)) {
      newExpanded.delete(debateId);
    } else {
      newExpanded.add(debateId);
    }
    setExpandedDebates(newExpanded);
  };

  const generateDebates = async () => {
    setGenerating(true);
    setProgress({ current: 0, total: 25 });

    try {
      const response = await axios.post(`${API_URL}/api/judgebench/debates/generate`, {
        temperature: temperature,
        prompt_style: 'analytical'
      });

      const debatePairs = response.data.debate_ids;

      // Collect all debate IDs (both original and flipped)
      const allDebateIds = [];
      debatePairs.forEach(pair => {
        allDebateIds.push(pair.original);
        allDebateIds.push(pair.flipped);
      });

      // Save these as JudgeBench debates
      await axios.post(`${API_URL}/api/judgebench/debates/select`, {
        debate_ids: allDebateIds
      });

      alert(`Successfully generated ${debatePairs.length} debate pairs (${allDebateIds.length} total debates)`);
      await loadDebates();
    } catch (error) {
      console.error('Error generating debates:', error);
      alert('Failed to generate debates');
    } finally {
      setGenerating(false);
    }
  };

  const clearDebates = async () => {
    if (!window.confirm('Are you sure you want to clear all JudgeBench debates? This cannot be undone.')) {
      return;
    }

    try {
      // Delete all debates from JudgeBench directory
      await axios.delete(`${API_URL}/api/judgebench/debates/clear`);
      setDebates([]);
      alert('All JudgeBench debates cleared');
    } catch (error) {
      console.error('Error clearing debates:', error);
      alert('Failed to clear debates');
    }
  };

  const debatePairs = debates.length / 2;

  return (
    <div className="judgebench-debates-page">
      <div className="header">
        <h1>JudgeBench Debates</h1>
        <p>Generate the 25 paired debates for JudgeBench evaluation</p>
      </div>

      <div className="config-section">
        <h2>Debate Configuration</h2>
        <div className="config-info">
          <div className="model-pairs">
            <h3>Model Pairs</h3>
            <div>• GPT-4o-mini vs LLaMA-70B: 8 debates</div>
            <div>• GPT-4o-mini vs Gemini-2.5-Flash: 8 debates</div>
            <div>• LLaMA-70B vs Gemini-2.5-Flash: 9 debates</div>
            <div style={{ marginTop: '0.5rem', fontWeight: 'bold' }}>
              Total: 25 topics × 2 (paired) = 50 debate instances
            </div>
          </div>

          <div className="temp-control">
            <label>Debate Temperature:</label>
            <input
              type="number"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              min="0.0"
              max="2.0"
            />
          </div>
        </div>
      </div>

      <div className="status-section">
        <h2>Current Status</h2>
        {debates.length === 0 ? (
          <div className="no-debates">
            <p>No JudgeBench debates generated yet.</p>
            <p>Click "Generate Debates" to create 25 paired debates from the topic list.</p>
          </div>
        ) : (
          <div className="debates-status">
            <div className="status-card">
              <div className="status-label">Debate Pairs</div>
              <div className="status-value">{debatePairs}</div>
            </div>
            <div className="status-card">
              <div className="status-label">Total Instances</div>
              <div className="status-value">{debates.length}</div>
            </div>
            <div className="status-card">
              <div className="status-label">Status</div>
              <div className="status-value">
                {debates.filter(d => d.status === 'complete').length} Complete
              </div>
            </div>
          </div>
        )}
      </div>

      {generating && (
        <div className="progress-section">
          <h3>Generating Debates...</h3>
          <p>This will take several minutes as each debate is run with both model configurations.</p>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            ></div>
          </div>
          <p>{progress.current} / {progress.total} debate pairs started</p>
        </div>
      )}

      <div className="actions">
        <button
          className="btn-primary"
          onClick={generateDebates}
          disabled={generating}
        >
          {generating ? 'Generating...' : 'Generate Debates'}
        </button>

        {debates.length > 0 && (
          <button
            className="btn-danger"
            onClick={clearDebates}
            disabled={generating}
          >
            Clear All Debates
          </button>
        )}
      </div>

      {debates.length > 0 && (
        <div className="debates-list-section">
          <h2>Generated Debates ({debates.length})</h2>
          <div className="debates-list">
            {debates.map((debate, index) => {
              const isExpanded = expandedDebates.has(debate.id);
              const speeches = debate.speeches || [];
              const speechCount = speeches.length;

              return (
                <div key={debate.id} className={`debate-card-full ${debate.status}`}>
                  <div className="debate-header" onClick={() => toggleDebate(debate.id)}>
                    <div className="debate-header-left">
                      <div className="debate-number">#{index + 1}</div>
                      <div className="debate-resolution">{debate.resolution}</div>
                    </div>
                    <div className="debate-header-right">
                      <div className="debate-models">
                        <span className="pro">{debate.pro_model}</span>
                        <span className="vs">vs</span>
                        <span className="con">{debate.con_model}</span>
                      </div>
                      <div className="debate-meta">
                        <span className={`debate-status ${debate.status}`}>{debate.status}</span>
                        <span className="speech-count">{speechCount} speeches</span>
                      </div>
                      <div className="expand-icon">{isExpanded ? '▼' : '▶'}</div>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="debate-transcript">
                      <div className="transcript-header">
                        <h3>Debate Transcript</h3>
                        <div className="debate-info-line">
                          <strong>Resolution:</strong> {debate.resolution}
                        </div>
                        <div className="debate-info-line">
                          <strong>PRO:</strong> {debate.pro_model} | <strong>CON:</strong> {debate.con_model}
                        </div>
                        <div className="debate-info-line">
                          <strong>Temperature:</strong> {debate.temperature} | <strong>Prompt Style:</strong> {debate.prompt_style}
                        </div>
                      </div>

                      {speeches.length === 0 ? (
                        <div className="no-speeches">
                          <p>No speeches yet. Debate is {debate.status}.</p>
                        </div>
                      ) : (
                        <div className="speeches-container">
                          {speeches.map((speech, idx) => (
                            <div key={idx} className={`speech-block ${speech.side?.toLowerCase()}`}>
                              <div className="speech-header">
                                <span className={`speech-side ${speech.side?.toLowerCase()}`}>
                                  {speech.side}
                                </span>
                                <span className="speech-type">
                                  {speech.speech_type?.replace(/_/g, ' ').toUpperCase()}
                                </span>
                              </div>
                              <div className="speech-content">
                                {speech.content}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default JudgeBenchDebatesPage;
