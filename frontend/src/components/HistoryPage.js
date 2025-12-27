import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './HistoryPage.css';

const API_URL = 'http://localhost:8001';

function HistoryPage() {
  const [debates, setDebates] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDebates();
    // Refresh every 3 seconds
    const interval = setInterval(fetchDebates, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchDebates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/debates`);
      setDebates(response.data.debates || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching debates:', error);
      setLoading(false);
    }
  };

  const toggleExpand = (debateId) => {
    setExpandedId(expandedId === debateId ? null : debateId);
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
          {debates.map((debate) => {
            const isExpanded = expandedId === debate.id;
            const hasTranscript = debate.debate && debate.debate.speeches && debate.debate.speeches.length > 0;

            return (
              <div key={debate.id} className="debate-item">
                <div 
                  className="debate-summary"
                  onClick={() => toggleExpand(debate.id)}
                >
                  <div className="debate-summary-left">
                    <div className="debate-title">{debate.resolution}</div>
                    <div className="debate-meta-row">
                      <span className="debate-id">ID: <code>{debate.id}</code></span>
                      <span className={`status-badge status-${debate.status}`}>
                        {debate.status}
                      </span>
                      <span className="debate-models">
                        PRO: {debate.pro_model || 'N/A'} | CON: {debate.con_model || 'N/A'}
                      </span>
                    </div>
                  </div>
                  <div className="debate-summary-right">
                    {hasTranscript && (
                      <span className="speech-count">
                        {debate.debate.speeches.length} speeches
                      </span>
                    )}
                    <span className="expand-indicator">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="debate-expanded">
                    {hasTranscript ? (
                      <div className="transcript-container">
                        <pre className="transcript">{formatTranscript(debate)}</pre>
                        <button
                          className="btn-copy"
                          onClick={() => {
                            navigator.clipboard.writeText(formatTranscript(debate));
                            alert('Transcript copied to clipboard!');
                          }}
                        >
                          Copy Transcript
                        </button>
                      </div>
                    ) : (
                      <div className="no-transcript">
                        {debate.status === 'complete' 
                          ? 'No transcript available for this debate.'
                          : `Debate is ${debate.status}. Transcript will appear when complete.`}
                      </div>
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


