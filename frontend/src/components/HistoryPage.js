import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './HistoryPage.css';

const API_URL = 'http://localhost:8001';

const WORD_LIMITS = {
  pro_constructive: 300,
  con_constructive: 300,
  pro_rebuttal: 250,
  con_rebuttal: 250,
  pro_summary: 200,
  con_summary: 200,
};

function HistoryPage() {
  const [debates, setDebates] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [expandedDebateId, setExpandedDebateId] = useState(null);
  const [expandedSection, setExpandedSection] = useState({}); // Track which section is expanded per debate
  const [loading, setLoading] = useState(true);
  const [rawMode, setRawMode] = useState(false);

  useEffect(() => {
    fetchDebates();
    // Refresh every 3 seconds
    const interval = setInterval(fetchDebates, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchDebates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/debates`);
      const allDebates = response.data.debates || [];

      // Group debates by pair_id
      const debateGroups = new Map();

      allDebates.forEach(debate => {
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

  const toggleExpand = (debateId) => {
    setExpandedId(expandedId === debateId ? null : debateId);
    // Reset expanded debate card when collapsing group
    if (expandedId === debateId) {
      setExpandedDebateId(null);
      setExpandedSection({});
    }
  };

  const toggleDebateExpand = (debateId) => {
    setExpandedDebateId(expandedDebateId === debateId ? null : debateId);
    // Reset expanded sections when collapsing debate
    if (expandedDebateId === debateId) {
      setExpandedSection(prev => {
        const updated = { ...prev };
        delete updated[debateId];
        return updated;
      });
    }
  };

  const toggleSection = (debateId, sectionKey) => {
    setExpandedSection(prev => {
      const currentExpanded = prev[debateId];
      return {
        ...prev,
        [debateId]: currentExpanded === sectionKey ? null : sectionKey
      };
    });
  };

  const formatTranscript = (debate) => {
    if (!debate.debate || !debate.debate.speeches) {
      return 'No transcript available';
    }

    let transcript = `Resolution: ${debate.resolution}\n`;
    transcript += `Pro: ${debate.pro_model || 'N/A'} | Con: ${debate.con_model || 'N/A'}\n`;
    transcript += `${'='.repeat(80)}\n\n`;

    debate.debate.speeches.forEach((speech, index) => {
      const speechName = speech.speech_type
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
      transcript += `[${speechName.toUpperCase()}]\n`;
      transcript += `Word count: ${speech.word_count || 0}\n`;
      transcript += `${speech.content}\n\n`;
      transcript += `${'-'.repeat(80)}\n\n`;
    });

    return transcript;
  };

  const renderDebateCard = (debate, debateNumber) => {
    if (!debate) return null;

    const isDebateExpanded = expandedDebateId === debate.id;
    const judges = debate.judges || [];
    const expandedSectionKey = expandedSection[debate.id];

    return (
      <div key={debate.id} className="debate-card">
        <div
          className="debate-card-header"
          onClick={() => toggleDebateExpand(debate.id)}
        >
          <div className="debate-card-title">
            <strong>Debate {debateNumber}:</strong> {debate.pro_model} (PRO) vs {debate.con_model} (CON)
          </div>
          <div className="debate-card-meta">
            <span className="debate-card-info">
              {debate.debate?.speeches?.length || 0} speeches
            </span>
            {judges.length > 0 && (
              <span className="debate-card-info">
                {judges.length} judge{judges.length !== 1 ? 's' : ''}
              </span>
            )}
            <span className="expand-indicator">
              {isDebateExpanded ? '▼' : '▶'}
            </span>
          </div>
        </div>

        {isDebateExpanded && (
          <div className="debate-card-content">
            <div className="debate-branches">
              {/* Transcript Branch */}
              <div className="debate-branch">
                <div
                  className="branch-header"
                  onClick={() => toggleSection(debate.id, 'transcript')}
                >
                  <div className="branch-title">
                    <span className="branch-icon">📄</span>
                    <span>Transcript</span>
                  </div>
                  <span className="expand-indicator">
                    {expandedSectionKey === 'transcript' ? '▼' : '▶'}
                  </span>
                </div>

                {expandedSectionKey === 'transcript' && (
                  <div className="branch-content">
                    {debate.debate?.speeches?.length > 0 ? (
                      <div className="speeches-container">
                        {debate.debate.speeches.map((speech, index) => {
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
                      <div className="no-content">No speeches available</div>
                    )}
                  </div>
                )}
              </div>

              {/* Judge Branches */}
              {judges.map((judge, idx) => (
                <div key={idx} className="debate-branch">
                  <div
                    className="branch-header"
                    onClick={() => toggleSection(debate.id, `judge-${idx}`)}
                  >
                    <div className="branch-title">
                      <span className="branch-icon">⚖️</span>
                      <span>Judge {idx + 1}: {judge.judge_model}</span>
                    </div>
                    <span className="expand-indicator">
                      {expandedSectionKey === `judge-${idx}` ? '▼' : '▶'}
                    </span>
                  </div>

                  {expandedSectionKey === `judge-${idx}` && (
                    <div className="branch-content">
                      <div className="judge-info">
                        <div className="judge-meta-item">
                          <strong>Model:</strong> {judge.judge_model}
                        </div>
                        <div className="judge-meta-item">
                          <strong>Prompt:</strong> {judge.judge_prompt}
                        </div>
                      </div>
                      <pre className="judge-content">
                        {judge.judgment}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="history-page">
      <div className="history-header">
        <h1>Debate History</h1>
        <p>All previous debates</p>
      </div>

      {loading ? (
        <div className="loading">Loading debates...</div>
      ) : debates.length === 0 ? (
        <div className="empty-history">No debates yet. Start a debate to see it here.</div>
      ) : (
        <div className="debates-list">
          {debates.map((group, idx) => {
            const groupId = group.original?.id || group.flipped?.id || idx;
            const isExpanded = expandedId === groupId;
            const original = group.original;
            const flipped = group.flipped;

            // Get models from both debates
            const model1 = original?.pro_model || flipped?.con_model || 'N/A';
            const model2 = original?.con_model || flipped?.pro_model || 'N/A';

            return (
              <div key={groupId} className="debate-item">
                <div
                  className="debate-summary"
                  onClick={() => toggleExpand(groupId)}
                >
                  <div className="debate-summary-left">
                    <div className="debate-title">
                      {group.resolution}
                    </div>
                    <div className="debate-meta-row">
                      {original && flipped && (
                        <span className="debate-pair-info">
                          <strong>Paired Debates:</strong> {model1} vs {model2}
                        </span>
                      )}
                      {(!original || !flipped) && (
                        <>
                          <span className="debate-id">ID: <code>{groupId.substring(0, 8)}...</code></span>
                          <span className="debate-models">
                            PRO: {original?.pro_model || 'N/A'} | CON: {original?.con_model || 'N/A'}
                          </span>
                        </>
                      )}
                      <span className={`status-badge status-${group.status}`}>
                        {group.status}
                      </span>
                    </div>
                  </div>
                  <div className="debate-summary-right">
                    <span className="expand-indicator">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="debate-expanded-group">
                    {/* Show both debates as cards if paired */}
                    {original && flipped ? (
                      <div className="paired-debates-cards">
                        {renderDebateCard(original, 1)}
                        {renderDebateCard(flipped, 2)}
                      </div>
                    ) : (
                      /* Single debate (old format) */
                      original?.debate?.speeches?.length > 0 ? (
                      <div className="transcript-container">
                        <div className="transcript-controls">
                          <label className="toggle-label">
                            <input
                              type="checkbox"
                              checked={rawMode}
                              onChange={(e) => setRawMode(e.target.checked)}
                              className="toggle-checkbox"
                            />
                            <span className="toggle-text">Raw Output Mode</span>
                          </label>
                          <button
                            className="btn-copy"
                            onClick={() => {
                              navigator.clipboard.writeText(formatTranscript(original));
                              alert('Transcript copied to clipboard!');
                            }}
                          >
                            Copy Transcript
                          </button>
                        </div>
                        {original.debate && original.debate.speeches && original.debate.speeches.length > 0 ? (
                          <div className="speeches-container">
                            {original.debate.speeches.map((speech, index) => {
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
                      ) : (
                        <div className="no-transcript">
                          {group.status === 'complete'
                            ? 'No transcript available for this debate.'
                            : `Debate is ${group.status}. Transcript will appear when complete.`}
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default HistoryPage;


