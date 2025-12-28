import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './JudgePage.css';

const API_URL = 'http://localhost:8001';

const WORD_LIMITS = {
  pro_constructive: 300,
  con_constructive: 300,
  pro_rebuttal: 250,
  con_rebuttal: 250,
  pro_summary: 200,
  con_summary: 200,
};

const JUDGE_MODELS = [
  'openai/gpt-4o-mini',
  'anthropic/claude-sonnet-4.5',
  'google/gemini-2.5-flash',
  'meta-llama/llama-3.3-70b-instruct',
  'qwen/qwen3-235b-a22b-2507',
  'x-ai/grok-4.1-fast'
];

function JudgePage() {
  const [debates, setDebates] = useState([]);
  const [selectedDebate, setSelectedDebate] = useState(null);
  const [judgeModel, setJudgeModel] = useState('anthropic/claude-sonnet-4.5');
  const [judgment, setJudgment] = useState(null);
  const [isJudging, setIsJudging] = useState(false);
  const [loading, setLoading] = useState(true);
  const [rawMode, setRawMode] = useState(false);
  const [judgeRawMode, setJudgeRawMode] = useState(false);

  useEffect(() => {
    fetchDebates();
  }, []);

  const fetchDebates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/debates`);
      const allDebates = response.data.debates || [];
      // Only show completed debates
      const completedDebates = allDebates.filter(d => d.status === 'complete' && d.speeches?.length > 0);
      setDebates(completedDebates);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching debates:', error);
      setLoading(false);
    }
  };

  const handleDebateSelect = (debate) => {
    setSelectedDebate(debate);
    setJudgment(null);
  };

  const handleJudge = async () => {
    if (!selectedDebate) return;

    setIsJudging(true);
    try {
      const response = await axios.post(`${API_URL}/api/judge`, {
        debate_id: selectedDebate.id,
        judge_model: judgeModel,
        judge_prompt: 'curated' // Single curated prompt
      });
      setJudgment(response.data.judgment);
    } catch (error) {
      console.error('Error judging debate:', error);
      alert(`Failed to judge debate: ${error.message}`);
    } finally {
      setIsJudging(false);
    }
  };

  const parseJudgment = (judgmentText) => {
    try {
      // Try to extract JSON from the judgment text
      const jsonMatch = judgmentText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (e) {
      console.error('Failed to parse judgment as JSON:', e);
    }
    return null;
  };

  const renderDebateTranscript = (debate) => {
    if (!debate.speeches || debate.speeches.length === 0) {
      return <div className="no-transcript">No speeches available</div>;
    }

    let transcript = `RESOLUTION: ${debate.resolution}\n\n`;
    transcript += `PRO: ${debate.pro_model}\n`;
    transcript += `CON: ${debate.con_model}\n`;
    transcript += `\n${'='.repeat(80)}\n\n`;

    debate.speeches.forEach((speech, idx) => {
      const side = speech.side || (speech.speech_type.includes('pro') ? 'PRO' : 'CON');
      transcript += `[${side}] ${speech.speech_type.toUpperCase().replace(/_/g, ' ')}\n`;
      transcript += `${'-'.repeat(80)}\n`;
      transcript += `${speech.content}\n\n`;
      if (idx < debate.speeches.length - 1) {
        transcript += `${'='.repeat(80)}\n\n`;
      }
    });

    return transcript;
  };

  return (
    <div className="judge-page">
      <div className="judge-config">
        <h2>Judge Configuration</h2>
        <div className="config-row">
          <div className="config-item">
            <label htmlFor="judge-model">Judge Model</label>
            <select
              id="judge-model"
              value={judgeModel}
              onChange={(e) => setJudgeModel(e.target.value)}
              disabled={isJudging}
            >
              {JUDGE_MODELS.map(model => (
                <option key={model} value={model}>{model}</option>
              ))}
            </select>
          </div>

          <button
            className="btn btn-judge"
            onClick={handleJudge}
            disabled={!selectedDebate || isJudging}
          >
            {isJudging ? 'Judging...' : 'Judge Debate'}
          </button>
        </div>
      </div>

      {!selectedDebate ? (
        <div className="debate-catalog">
          <h3>Select a Debate to Judge</h3>
          {loading ? (
            <div className="loading">Loading debates...</div>
          ) : debates.length === 0 ? (
            <div className="empty-state">No completed debates found</div>
          ) : (
            <div className="debates-list">
              {debates.map((debate) => (
                <div
                  key={debate.id}
                  className="debate-card"
                  onClick={() => handleDebateSelect(debate)}
                >
                  <div className="debate-card-header">
                    <h4>{debate.resolution}</h4>
                    <span className="status-badge status-complete">{debate.status}</span>
                  </div>
                  <div className="debate-card-meta">
                    <span className="debate-id">ID: <code>{debate.id?.substring(0, 8)}</code></span>
                    <span className="debate-models">
                      PRO: {debate.pro_model} vs CON: {debate.con_model}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="judge-view">
          <div className="judge-view-header">
            <button className="btn-back" onClick={() => setSelectedDebate(null)}>
              ← Back to Catalog
            </button>
            <h3>{selectedDebate.resolution}</h3>
          </div>

          <div className="judge-content">
            <div className="transcript-panel">
              <div className="transcript-panel-header">
                <h4>Debate Transcript</h4>
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={rawMode}
                    onChange={(e) => setRawMode(e.target.checked)}
                    className="toggle-checkbox"
                  />
                  <span className="toggle-text">Raw Output Mode</span>
                </label>
              </div>
              {selectedDebate.speeches && selectedDebate.speeches.length > 0 ? (
                <div className="speeches-container">
                  {selectedDebate.speeches.map((speech, index) => {
                    const isPro = speech.speech_type?.startsWith('pro');
                    const side = isPro ? 'PRO' : 'CON';
                    const sideColor = side === 'PRO' ? '#00aa00' : '#aa0000';
                    const speechName = speech.speech_type
                      .replace(/_/g, ' ')
                      .replace(/\b\w/g, l => l.toUpperCase());
                    const wordLimit = WORD_LIMITS[speech.speech_type] || 0;

                    return (
                      <div key={index} className="speech-item">
                        <div 
                          className="speech-header"
                          style={{ borderLeftColor: sideColor }}
                        >
                          <div className="speech-title">
                            <span 
                              className="side-badge"
                              style={{ 
                                backgroundColor: sideColor,
                                color: '#ffffff'
                              }}
                            >
                              {side}
                            </span>
                            <span className="speech-type">{speechName}</span>
                          </div>
                          <span className="word-count">
                            {speech.word_count || 0}/{wordLimit} words
                          </span>
                        </div>
                        <pre className={rawMode ? "speech-content-raw" : "speech-content"}>
                          {speech.content}
                        </pre>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="no-transcript">No speeches available</div>
              )}
            </div>

            <div className="judgment-panel">
              <div className="judgment-panel-header">
                <h4>Judge's Analysis</h4>
                {judgment && (
                  <label className="toggle-label">
                    <input
                      type="checkbox"
                      checked={judgeRawMode}
                      onChange={(e) => setJudgeRawMode(e.target.checked)}
                      className="toggle-checkbox"
                    />
                    <span className="toggle-text">Raw Output Mode</span>
                  </label>
                )}
              </div>
              {!judgment && !isJudging && (
                <div className="no-judgment">
                  <p>Click "Judge Debate" to generate an AI analysis</p>
                </div>
              )}
              {isJudging && (
                <div className="judging-indicator">
                  <div className="spinner"></div>
                  <p>Analyzing debate...</p>
                </div>
              )}
              {judgment && (
                <>
                  {(() => {
                    const parsedJudgment = parseJudgment(judgment);
                    if (parsedJudgment) {
                      return (
                        <div className="judgment-summary">
                          <div className="judgment-header">
                            <div className="winner-section">
                              <span className="label">Winner:</span>
                              <span className={`winner-badge winner-${parsedJudgment.winner?.toLowerCase()}`}>
                                {parsedJudgment.winner}
                              </span>
                            </div>
                            <div className="confidence-section">
                              <span className="label">Confidence:</span>
                              <span className="confidence-value">
                                {(parsedJudgment.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>

                          <div className="scores-grid">
                            <div className="score-category">
                              <div className="category-name">Argument Quality</div>
                              <div className="score-row">
                                <span className="score-label">PRO:</span>
                                <span className="score-value">{parsedJudgment.scores?.argument_quality?.PRO || 0}/5</span>
                              </div>
                              <div className="score-row">
                                <span className="score-label">CON:</span>
                                <span className="score-value">{parsedJudgment.scores?.argument_quality?.CON || 0}/5</span>
                              </div>
                            </div>

                            <div className="score-category">
                              <div className="category-name">Evidence</div>
                              <div className="score-row">
                                <span className="score-label">PRO:</span>
                                <span className="score-value">{parsedJudgment.scores?.evidence?.PRO || 0}/5</span>
                              </div>
                              <div className="score-row">
                                <span className="score-label">CON:</span>
                                <span className="score-value">{parsedJudgment.scores?.evidence?.CON || 0}/5</span>
                              </div>
                            </div>

                            <div className="score-category">
                              <div className="category-name">Clash & Refutation</div>
                              <div className="score-row">
                                <span className="score-label">PRO:</span>
                                <span className="score-value">{parsedJudgment.scores?.clash?.PRO || 0}/5</span>
                              </div>
                              <div className="score-row">
                                <span className="score-label">CON:</span>
                                <span className="score-value">{parsedJudgment.scores?.clash?.CON || 0}/5</span>
                              </div>
                            </div>

                            <div className="score-category">
                              <div className="category-name">Impact Weighing</div>
                              <div className="score-row">
                                <span className="score-label">PRO:</span>
                                <span className="score-value">{parsedJudgment.scores?.weighing?.PRO || 0}/5</span>
                              </div>
                              <div className="score-row">
                                <span className="score-label">CON:</span>
                                <span className="score-value">{parsedJudgment.scores?.weighing?.CON || 0}/5</span>
                              </div>
                            </div>
                          </div>

                          <div className="reasoning-section">
                            <div className="reasoning-label">Reasoning:</div>
                            <div className="reasoning-text">{parsedJudgment.short_reason}</div>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()}
                  <pre className={judgeRawMode ? "judgment-content-raw" : "judgment-content"}>
                    {judgment}
                  </pre>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default JudgePage;
