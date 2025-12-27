import React, { useState } from 'react';
import './DebateDisplay.css';

const WORD_LIMITS = {
  pro_constructive: 300,
  con_constructive: 300,
  pro_rebuttal: 250,
  con_rebuttal: 250,
  pro_summary: 200,
  con_summary: 200,
};

function DebateDisplay({ debate, status, debateId }) {
  const [rawMode, setRawMode] = useState(false);

  if (!debate) return null;

  const isPro = (speechType) => speechType?.startsWith('pro');

  return (
    <div className="debate-display">
      <div className="debate-header">
        <h2>{debate.resolution}</h2>
        <div className="debate-meta">
          <div className="meta-item">
            <span className="meta-label">PRO:</span>
            <span className="meta-value">{debate.pro_model || 'N/A'}</span>
          </div>
          <div className="meta-item">
            <span className="meta-label">CON:</span>
            <span className="meta-value">{debate.con_model || 'N/A'}</span>
          </div>
          <div className="meta-item">
            <span className={`status-badge status-${status}`}>
              {status}
            </span>
          </div>
          {debateId && (
            <div className="meta-item">
              <span className="meta-label">ID:</span>
              <span className="meta-value">
                <code className="debate-id-code">{debateId}</code>
              </span>
            </div>
          )}
          <div className="meta-item">
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
        </div>
      </div>

      <div className="speeches-container">
        {debate.speeches && debate.speeches.length > 0 ? (
          debate.speeches.map((speech, index) => {
            const side = isPro(speech.speech_type) ? 'PRO' : 'CON';
            const sideColor = side === 'PRO' ? '#00aa00' : '#aa0000'; // Green for PRO, Red for CON
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
                  {speech.content || 'Generating...'}
                </pre>
              </div>
            );
          })
        ) : (
          <div className="empty-state">
            <p>No speeches yet. The debate will appear here as it progresses.</p>
          </div>
        )}
      </div>

      {status === 'running' && (
        <div className="progress-indicator">
          <div className="spinner"></div>
          <span>Generating next speech...</span>
        </div>
      )}
    </div>
  );
}

export default DebateDisplay;

