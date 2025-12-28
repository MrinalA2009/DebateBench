import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import './App.css';
import DebateConfig from './components/DebateConfig';
import DebateDisplay from './components/DebateDisplay';
import HistoryPage from './components/HistoryPage';
import JudgePage from './components/JudgePage';

const API_URL = 'http://localhost:8001';

function App() {
  const [debate, setDebate] = useState(null);
  const [debateId, setDebateId] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, starting, running, complete, error
  const [allDebates, setAllDebates] = useState([]);
  const [currentPage, setCurrentPage] = useState('debate'); // 'debate', 'history', or 'judge'
  const wsRef = useRef(null);

  const handleWebSocketMessage = useCallback((data) => {
    console.log('[WEBSOCKET] Received message:', data.type, data);
    switch (data.type) {
      case 'debate_started':
        console.log('[DEBATE_STARTED] Setting debate ID:', data.debate_id);
        console.log('[DEBATE_STARTED] Resolution:', data.resolution);
        console.log('[DEBATE_STARTED] Models - PRO:', data.pro_model, 'CON:', data.con_model);
        setDebateId(data.debate_id);
        setStatus('starting');
        const newDebate = {
          resolution: data.resolution,
          speeches: [],
          pro_model: data.pro_model || null,
          con_model: data.con_model || null
        };
        console.log('[DEBATE_STARTED] Setting debate state:', newDebate);
        setDebate(newDebate);
        break;
      
      case 'debate_status':
        console.log('[DEBATE_STATUS] Status:', data.status);
        console.log('[DEBATE_STATUS] Debate ID:', data.debate_id, 'Current debateId:', debateId);
        console.log('[DEBATE_STATUS] Models - PRO:', data.pro_model, 'CON:', data.con_model);
        // Update status and model names if debate exists (even if debateId not set yet)
        setStatus(data.status);
        if (data.pro_model || data.con_model) {
          setDebate(prev => {
            console.log('[DEBATE_STATUS] Previous debate state:', prev);
            if (!prev) {
              // If no debate state exists yet, create it
              const newDebate = {
                resolution: '',
                speeches: [],
                pro_model: data.pro_model || null,
                con_model: data.con_model || null
              };
              console.log('[DEBATE_STATUS] Creating new debate state:', newDebate);
              return newDebate;
            }
            const updatedDebate = {
              ...prev,
              pro_model: data.pro_model || prev?.pro_model,
              con_model: data.con_model || prev?.con_model
            };
            console.log('[DEBATE_STATUS] Updating debate state:', updatedDebate);
            return updatedDebate;
          });
        }
        break;
      
      case 'speech_started':
        console.log('[SPEECH_STARTED] Debate ID:', data.debate_id, 'Current debateId:', debateId);
        console.log('[SPEECH_STARTED] Speech type:', data.speech_type, 'Side:', data.side);
        if (data.debate_id === debateId) {
          console.log('[SPEECH_STARTED] IDs match, setting status to running');
          setStatus('running');
        } else {
          console.log('[SPEECH_STARTED] IDs do not match, ignoring');
        }
        break;
      
      case 'speech_complete':
        console.log('[SPEECH_COMPLETE] Debate ID:', data.debate_id, 'Current debateId:', debateId);
        console.log('[SPEECH_COMPLETE] Speech data:', data.speech);
        if (data.debate_id === debateId) {
          setDebate(prev => {
            const newSpeeches = [...(prev?.speeches || []), data.speech];
            console.log('[SPEECH_COMPLETE] Adding speech. Total speeches:', newSpeeches.length);
            console.log('[SPEECH_COMPLETE] New speeches array:', newSpeeches);
            return {
              ...prev,
              speeches: newSpeeches
            };
          });
        } else {
          console.log('[SPEECH_COMPLETE] IDs do not match, ignoring');
        }
        break;
      
      case 'debate_complete':
        console.log('[DEBATE_COMPLETE] Debate ID:', data.debate_id, 'Current debateId:', debateId);
        console.log('[DEBATE_COMPLETE] Full debate data:', data.debate);
        if (data.debate_id === debateId) {
          setStatus('complete');
          setDebate(data.debate);
          console.log('[DEBATE_COMPLETE] Debate completed, state updated');
        } else {
          console.log('[DEBATE_COMPLETE] IDs do not match, ignoring');
        }
        break;
      
      case 'debate_error':
        console.error('[DEBATE_ERROR] Debate ID:', data.debate_id, 'Current debateId:', debateId);
        console.error('[DEBATE_ERROR] Error:', data.error);
        if (data.debate_id === debateId) {
          setStatus('error');
          alert(`Error: ${data.error}`);
        } else {
          console.log('[DEBATE_ERROR] IDs do not match, ignoring');
        }
        break;
      
      default:
        break;
    }
  }, [debateId]);

  useEffect(() => {
    // WebSocket connection for real-time updates
    console.log('[WEBSOCKET] Setting up WebSocket connection');
    const ws = new WebSocket('ws://localhost:8001/ws');
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WEBSOCKET] Connection opened');
    };

    ws.onmessage = (event) => {
      console.log('[WEBSOCKET] Raw message received:', event.data);
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('[WEBSOCKET] Error parsing message:', error, 'Raw data:', event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('[WEBSOCKET] Error:', error);
    };

    ws.onclose = (event) => {
      console.log('[WEBSOCKET] Connection closed. Code:', event.code, 'Reason:', event.reason, 'WasClean:', event.wasClean);
    };

    return () => {
      console.log('[WEBSOCKET] Cleaning up WebSocket connection');
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [debateId, handleWebSocketMessage]);

  const fetchAllDebates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/debates`);
      const debates = response.data.debates || [];
      setAllDebates(debates);
    } catch (error) {
      console.error('[API] Error fetching debates:', error);
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
      console.log('[START_DEBATE] Starting debate with config:', config);
      // Clear the previous debate display immediately
      console.log('[START_DEBATE] Clearing previous debate state');
      setDebateId(null);
      setStatus('starting');
      // Initialize debate state immediately with model names so they're available right away
      const initialDebate = {
        resolution: config.resolution,
        speeches: [],
        pro_model: config.pro_model,
        con_model: config.con_model
      };
      console.log('[START_DEBATE] Setting initial debate state:', initialDebate);
      setDebate(initialDebate);
      
      const params = {
        resolution: config.resolution,
        pro_model: config.pro_model,
        con_model: config.con_model,
        temperature: config.temperature,
        prompt_style: config.prompt_style
      };
      console.log('[API] POST /api/debates/start with params:', params);
      const response = await axios.post(`${API_URL}/api/debates/start`, null, { params });
      console.log('[API] Start debate response:', response.data);
      const newDebateId = response.data.debate_id;
      console.log('[START_DEBATE] Setting debate ID:', newDebateId);
      setDebateId(newDebateId);
      // Refresh debate list after starting
      setTimeout(fetchAllDebates, 1000);
    } catch (error) {
      console.error('[START_DEBATE] Error starting debate:', error);
      console.error('[START_DEBATE] Error details:', error.response?.data || error.message);
      setStatus('error');
      setDebate(null);
      alert(`Failed to start debate: ${error.message}`);
    }
  };

  const loadDebate = async (debateId) => {
    try {
      console.log('[LOAD_DEBATE] Loading debate:', debateId);
      const url = `${API_URL}/api/debates/${debateId}`;
      console.log('[API] GET', url);
      const response = await axios.get(url);
      console.log('[API] Load debate response:', response.data);
      const debateData = response.data.debate || response.data;
      console.log('[LOAD_DEBATE] Setting debate data:', debateData);
      setDebate(debateData);
      setDebateId(debateId);
      const status = response.data.status || 'complete';
      console.log('[LOAD_DEBATE] Setting status:', status);
      setStatus(status);
    } catch (error) {
      console.error('[LOAD_DEBATE] Error loading debate:', error);
      console.error('[LOAD_DEBATE] Error details:', error.response?.data || error.message);
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
          <button
            className={`nav-button ${currentPage === 'judge' ? 'active' : ''}`}
            onClick={() => setCurrentPage('judge')}
          >
            Judge
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
        ) : currentPage === 'history' ? (
          <HistoryPage />
        ) : (
          <JudgePage />
        )}
      </main>
    </div>
  );
}

export default App;

