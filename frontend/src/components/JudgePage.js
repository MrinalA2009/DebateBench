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
  const [judgePrompt, setJudgePrompt] = useState('p0');
  const [judgment, setJudgment] = useState(null);
  const [isJudging, setIsJudging] = useState(false);
  const [loading, setLoading] = useState(true);
  const [rawMode, setRawMode] = useState(false);
  const [judgeRawMode, setJudgeRawMode] = useState(false);
  const [showFullJudgment, setShowFullJudgment] = useState(false);
  const [expandedGroupId, setExpandedGroupId] = useState(null);

  useEffect(() => {
    fetchDebates();
  }, []);

  const fetchDebates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/debates`);
      const allDebates = response.data.debates || [];

      // Only show completed debates
      const completedDebates = allDebates.filter(d => d.status === 'complete' && d.speeches?.length > 0);

      // Group debates by pair_id
      const debateGroups = new Map();

      completedDebates.forEach(debate => {
        if (debate.pair_id) {
          // This debate is part of a pair
          const groupKey = [debate.id, debate.pair_id].sort().join('-');
          if (!debateGroups.has(groupKey)) {
            debateGroups.set(groupKey, {
              original: null,
              flipped: null,
              created_at: debate.created_at || 0,
              resolution: debate.resolution,
              status: debate.status
            });
          }

          const group = debateGroups.get(groupKey);
          if (debate.model_assignment === 'original') {
            group.original = debate;
          } else {
            group.flipped = debate;
          }
        } else {
          // Old debate without pairing - show individually
          const groupKey = debate.id;
          debateGroups.set(groupKey, {
            original: debate,
            flipped: null,
            created_at: debate.created_at || 0,
            resolution: debate.resolution,
            status: debate.status
          });
        }
      });

      // Convert to array and sort by created_at (newest first)
      const sortedGroups = Array.from(debateGroups.values()).sort((a, b) => {
        return (b.created_at || 0) - (a.created_at || 0);
      });

      setDebates(sortedGroups);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching debates:', error);
      setLoading(false);
    }
  };

  const handleDebateSelect = (debate) => {
    setSelectedDebate(debate);
    setJudgment(null);
    setShowFullJudgment(false);
  };

  const toggleGroup = (groupId) => {
    setExpandedGroupId(expandedGroupId === groupId ? null : groupId);
  };

  const handleJudge = async () => {
    if (!selectedDebate) return;

    setIsJudging(true);
    try {
      const response = await axios.post(`${API_URL}/api/judge`, {
        debate_id: selectedDebate.id,
        judge_model: judgeModel,
        judge_prompt: judgePrompt
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

          <div className="config-item">
            <label htmlFor="judge-prompt">Judge Prompt</label>
            <select
              id="judge-prompt"
              value={judgePrompt}
              onChange={(e) => setJudgePrompt(e.target.value)}
              disabled={isJudging}
            >
              <option value="p0">P0 - Main Prompt (Baseline)</option>
              <option value="p1">P1 - Procedural (Two-Stage)</option>
              <option value="p2">P2 - Weighing Emphasis</option>
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
              {debates.map((group, idx) => {
                const original = group.original;
                const flipped = group.flipped;
                const groupId = original?.id || flipped?.id || idx;
                const isPaired = original && flipped;
                const isExpanded = expandedGroupId === groupId;

                // Get models from both debates
                const model1 = original?.pro_model || flipped?.con_model || 'N/A';
                const model2 = original?.con_model || flipped?.pro_model || 'N/A';

                if (isPaired) {
                  // Paired debates - expandable group
                  return (
                    <div key={groupId} className="debate-group">
                      <div
                        className="debate-group-header"
                        onClick={() => toggleGroup(groupId)}
                      >
                        <div className="debate-group-header-left">
                          <h4>{group.resolution}</h4>
                          <span className="debate-models">
                            <strong>Paired Debates:</strong> {model1} vs {model2}
                          </span>
                        </div>
                        <div className="debate-group-header-right">
                          <span className="status-badge status-complete">{group.status}</span>
                          <span className="expand-indicator">{isExpanded ? '▼' : '▶'}</span>
                        </div>
                      </div>
                      {isExpanded && (
                        <div className="debate-group-content">
                          <div
                            className="debate-card-nested"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDebateSelect(original);
                            }}
                          >
                            <div className="debate-card-header-nested">
                              <div className="debate-assignment-badge">Original Assignment</div>
                              <div className="debate-models-nested">
                                <span className="model-badge model-pro">PRO: {original.pro_model}</span>
                                <span className="model-badge model-con">CON: {original.con_model}</span>
                              </div>
                            </div>
                          </div>
                          <div
                            className="debate-card-nested"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDebateSelect(flipped);
                            }}
                          >
                            <div className="debate-card-header-nested">
                              <div className="debate-assignment-badge">Flipped Assignment</div>
                              <div className="debate-models-nested">
                                <span className="model-badge model-pro">PRO: {flipped.pro_model}</span>
                                <span className="model-badge model-con">CON: {flipped.con_model}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                } else {
                  // Non-paired debate - direct selection
                  return (
                    <div
                      key={groupId}
                      className="debate-card"
                      onClick={() => handleDebateSelect(original || flipped)}
                    >
                      <div className="debate-card-header">
                        <h4>{group.resolution}</h4>
                        <span className="status-badge status-complete">{group.status}</span>
                      </div>
                      <div className="debate-card-meta">
                        <span className="debate-id">ID: <code>{groupId.substring(0, 8)}...</code></span>
                        <span className="debate-models">
                          PRO: {original?.pro_model || 'N/A'} vs CON: {original?.con_model || 'N/A'}
                        </span>
                      </div>
                    </div>
                  );
                }
              })}
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
            <div className="debate-models-info">
              <span className="model-info model-pro">
                <strong>PRO:</strong> {selectedDebate.pro_model}
              </span>
              <span className="model-divider">vs</span>
              <span className="model-info model-con">
                <strong>CON:</strong> {selectedDebate.con_model}
              </span>
            </div>
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

                          <div className="full-output-toggle">
                            <button
                              className="btn-toggle-output"
                              onClick={() => setShowFullJudgment(!showFullJudgment)}
                            >
                              {showFullJudgment ? '▼ Hide Full Output' : '▶ Show Full Output'}
                            </button>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()}
                  {showFullJudgment && (
                    <pre className={judgeRawMode ? "judgment-content-raw" : "judgment-content"}>
                      {judgment}
                    </pre>
                  )}
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
