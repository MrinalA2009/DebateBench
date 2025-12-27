import React, { useState } from 'react';
import './DebateConfig.css';
import topics from '../sortedtopics.json';

const POPULAR_MODELS = [
  'openai/gpt-5.2',
  'openai/gpt-4o-mini',
  'anthropic/claude-sonnet-4.5',
  'google/gemini-2.5-flash'
];

function DebateConfig({ onStart, status }) {
  const [resolution, setResolution] = useState('Resolved: Social media does more harm than good');
  const [proModel, setProModel] = useState('openai/gpt-5.2');
  const [proModelCustom, setProModelCustom] = useState('');
  const [proModelIsCustom, setProModelIsCustom] = useState(false);
  const [conModel, setConModel] = useState('anthropic/claude-sonnet-4.5');
  const [conModelCustom, setConModelCustom] = useState('');
  const [conModelIsCustom, setConModelIsCustom] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [promptStyle, setPromptStyle] = useState('standard');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (status === 'running' || status === 'starting') {
      return;
    }
    const finalProModel = proModelIsCustom ? proModelCustom.trim() : proModel;
    const finalConModel = conModelIsCustom ? conModelCustom.trim() : conModel;
    
    if (!finalProModel || !finalConModel) {
      alert('Please select or enter both PRO and CON models');
      return;
    }
    
    onStart({
      resolution,
      pro_model: finalProModel,
      con_model: finalConModel,
      temperature,
      prompt_style: promptStyle
    });
  };

  const handleRandomTopic = () => {
    const categories = Object.keys(topics);
    const randomCategory = categories[Math.floor(Math.random() * categories.length)];
    const categoryTopics = topics[randomCategory];
    const randomTopic = categoryTopics[Math.floor(Math.random() * categoryTopics.length)];
    setResolution(randomTopic);
  };

  const handleProModelChange = (value) => {
    if (value === 'custom') {
      setProModelIsCustom(true);
    } else {
      setProModelIsCustom(false);
      setProModel(value);
    }
  };

  const handleConModelChange = (value) => {
    if (value === 'custom') {
      setConModelIsCustom(true);
    } else {
      setConModelIsCustom(false);
      setConModel(value);
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
            {!proModelIsCustom ? (
              <select
                id="pro-model"
                value={proModel}
                onChange={(e) => handleProModelChange(e.target.value)}
                disabled={isRunning}
              >
                {POPULAR_MODELS.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
                <option value="custom">Custom...</option>
              </select>
            ) : (
              <input
                id="pro-model-custom"
                type="text"
                value={proModelCustom}
                onChange={(e) => setProModelCustom(e.target.value)}
                onBlur={() => {
                  if (!proModelCustom.trim()) {
                    setProModelIsCustom(false);
                  }
                }}
                disabled={isRunning}
                placeholder="Enter model ID (e.g., openai/gpt-4o-mini)"
              />
            )}
          </div>

          <div className="form-group">
            <label htmlFor="con-model">CON Model</label>
            {!conModelIsCustom ? (
              <select
                id="con-model"
                value={conModel}
                onChange={(e) => handleConModelChange(e.target.value)}
                disabled={isRunning}
              >
                {POPULAR_MODELS.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
                <option value="custom">Custom...</option>
              </select>
            ) : (
              <input
                id="con-model-custom"
                type="text"
                value={conModelCustom}
                onChange={(e) => setConModelCustom(e.target.value)}
                onBlur={() => {
                  if (!conModelCustom.trim()) {
                    setConModelIsCustom(false);
                  }
                }}
                disabled={isRunning}
                placeholder="Enter model ID (e.g., anthropic/claude-sonnet-4.5)"
              />
            )}
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
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleRandomTopic}
              disabled={isRunning}
            >
              Random Topic
            </button>
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

