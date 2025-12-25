import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import './App.css';
import DebateConfig from './components/DebateConfig';
import DebateDisplay from './components/DebateDisplay';
import HistoryPage from './components/HistoryPage';

const API_URL = 'http://localhost:8001';

function App() {
  const [debate, setDebate] = useState(null);
  const [debateId, setDebateId] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, starting, running, complete, error
  const [allDebates, setAllDebates] = useState([]);
  const [currentPage, setCurrentPage] = useState('debate'); // 'debate' or 'history'
  const wsRef = useRef(null);

  const handleWebSocketMessage = useCallback((data) => {
    switch (data.type) {
      case 'debate_started':
        setDebateId(data.debate_id);
        setStatus('starting');
        setDebate({
          resolution: data.resolution,
          speeches: [],
          pro_model: null,
          con_model: null
        });
        break;
      
      case 'debate_status':
        if (data.debate_id === debateId) {
          setStatus(data.status);
        }
        break;
      
      case 'speech_started':
        if (data.debate_id === debateId) {
          setStatus('running');
        }
        break;
      
      case 'speech_complete':
        if (data.debate_id === debateId) {
          setDebate(prev => ({
            ...prev,
            speeches: [...(prev?.speeches || []), data.speech]
          }));
        }
        break;
      
      case 'debate_complete':
        if (data.debate_id === debateId) {
          setStatus('complete');
          setDebate(data.debate);
        }
        break;
      
      case 'debate_error':
        if (data.debate_id === debateId) {
          setStatus('error');
          alert(`Error: ${data.error}`);
        }
        break;
      
      default:
        break;
    }
  }, [debateId]);

  useEffect(() => {
    // WebSocket connection for real-time updates
    const ws = new WebSocket('ws://localhost:8001/ws');
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [debateId, handleWebSocketMessage]);

  const fetchAllDebates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/debates`);
      setAllDebates(response.data.debates || []);
    } catch (error) {
      console.error('Error fetching debates:', error);
    }
  };

  useEffect(() => {
    fetchAllDebates();
    // Refresh debate list every 5 seconds
    const interval = setInterval(fetchAllDebates, 5000);
    return () => clearInterval(interval);
  }, []);

  const startDebate = async (config) => {
    try {
      setStatus('starting');
      const response = await axios.post(`${API_URL}/api/debates/start`, null, {
        params: {
          resolution: config.resolution,
          pro_model: config.pro_model,
          con_model: config.con_model,
          temperature: config.temperature,
          prompt_style: config.prompt_style
        }
      });
      setDebateId(response.data.debate_id);
      // Refresh debate list after starting
      setTimeout(fetchAllDebates, 1000);
    } catch (error) {
      console.error('Error starting debate:', error);
      setStatus('error');
      alert(`Failed to start debate: ${error.message}`);
    }
  };

  const loadDebate = async (debateId) => {
    try {
      const response = await axios.get(`${API_URL}/api/debates/${debateId}`);
      setDebate(response.data.debate || response.data);
      setDebateId(debateId);
      setStatus(response.data.status || 'complete');
    } catch (error) {
      console.error('Error loading debate:', error);
      alert(`Failed to load debate: ${error.message}`);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>DebateBench</h1>
        <p>A controlled, reproducible benchmark for AI-generated debates</p>
        <nav className="main-nav">
          <button
            className={`nav-button ${currentPage === 'debate' ? 'active' : ''}`}
            onClick={() => setCurrentPage('debate')}
          >
            Debate
          </button>
          <button
            className={`nav-button ${currentPage === 'history' ? 'active' : ''}`}
            onClick={() => setCurrentPage('history')}
          >
            History
          </button>
        </nav>
      </header>
      
      <main className="App-main">
        {currentPage === 'debate' ? (
          <div className="container">
          <DebateConfig 
            onStart={startDebate}
            status={status}
          />
            
            {debate && (
              <DebateDisplay 
                debate={debate}
                status={status}
                debateId={debateId}
              />
            )}
          </div>
        ) : (
          <HistoryPage />
        )}
      </main>
    </div>
  );
}

export default App;

