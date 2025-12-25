import React, { useState } from 'react';
import './DebateConfig.css';

function DebateConfig({ onStart, onLoad, status }) {
  const [resolution, setResolution] = useState('Resolved: Social media does more harm than good');
  const [proModel, setProModel] = useState('openai/gpt-4');
  const [conModel, setConModel] = useState('anthropic/claude-3-opus');
  const [temperature, setTemperature] = useState(0.7);
  const [promptStyle, setPromptStyle] = useState('standard');
  const [debateIdToLoad, setDebateIdToLoad] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (status === 'running' || status === 'starting') {
      return;
    }
    onStart({
      resolution,
      pro_model: proModel,
      con_model: conModel,
      temperature,
      prompt_style: promptStyle
    });
  };

  const handleLoad = () => {
    if (debateIdToLoad.trim()) {
      onLoad(debateIdToLoad.trim());
    }
  };

  const isRunning = status === 'running' || status === 'starting';

  return (
    <div className="debate-config">
      <div className="config-card">
        <h2>Configuration</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="pro-model">PRO Model</label>
            <input
              id="pro-model"
              type="text"
              value={proModel}
              onChange={(e) => setProModel(e.target.value)}
              disabled={isRunning}
              placeholder="openai/gpt-4"
            />
          </div>

          <div className="form-group">
            <label htmlFor="con-model">CON Model</label>
            <input
              id="con-model"
              type="text"
              value={conModel}
              onChange={(e) => setConModel(e.target.value)}
              disabled={isRunning}
              placeholder="anthropic/claude-3-opus"
            />
          </div>

          <div className="form-group">
            <label htmlFor="resolution">Resolution</label>
            <textarea
              id="resolution"
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              disabled={isRunning}
              rows="4"
              placeholder="Resolved: ..."
            />
          </div>

          <div className="form-group">
            <label htmlFor="temperature">
              Temperature: {temperature}
            </label>
            <input
              id="temperature"
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              disabled={isRunning}
            />
          </div>

          <div className="form-group">
            <label htmlFor="prompt-style">Prompt Style</label>
            <select
              id="prompt-style"
              value={promptStyle}
              onChange={(e) => setPromptStyle(e.target.value)}
              disabled={isRunning}
            >
              <option value="standard">Standard</option>
              <option value="structured">Structured</option>
              <option value="freeform">Freeform</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={isRunning}
          >
            {isRunning ? 'Running...' : 'Start Debate'}
          </button>
        </form>

        <div className="divider">or</div>

        <div className="form-group">
          <label htmlFor="load-id">Load Debate by ID</label>
          <div className="load-input-group">
            <input
              id="load-id"
              type="text"
              value={debateIdToLoad}
              onChange={(e) => setDebateIdToLoad(e.target.value)}
              placeholder="Enter debate ID"
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleLoad}
            >
              Load
            </button>
          </div>
        </div>

        <div className="protocol-info">
          <h3>Debate Protocol</h3>
          <ul>
            <li>Pro Constructive (300 words)</li>
            <li>Con Constructive (300 words)</li>
            <li>Pro Rebuttal (250 words)</li>
            <li>Con Rebuttal (250 words)</li>
            <li>Pro Summary (200 words)</li>
            <li>Con Summary (200 words)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default DebateConfig;

