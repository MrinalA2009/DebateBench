import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import './App.css';
import DebateConfig from './components/DebateConfig';
import DebateDisplay from './components/DebateDisplay';
import HistoryPage from './components/HistoryPage';
import JudgePage from './components/JudgePage';
import JudgeBenchPage from './components/JudgeBenchPage';
import JudgeBenchDebatesPage from './components/JudgeBenchDebatesPage';

const API_URL = 'http://localhost:8001';

function App() {
  const [debate, setDebate] = useState(null);
  const [debateId, setDebateId] = useState(null);
  const [debateFlipped, setDebateFlipped] = useState(null);
  const [debateIdFlipped, setDebateIdFlipped] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, starting, running, complete, error
  const [statusFlipped, setStatusFlipped] = useState('idle');
  const [allDebates, setAllDebates] = useState([]);
  const [currentPage, setCurrentPage] = useState('debate'); // 'debate', 'history', 'judge', 'judgebench', or 'judgebench-debates'
  const wsRef = useRef(null);

  const handleWebSocketMessage = useCallback((data) => {
    console.log('[WEBSOCKET] Received message:', data.type, data);

    // Determine which debate this message is for using model_assignment
    const isFlipped = data.model_assignment === 'flipped' || data.debate_id === debateIdFlipped;

    switch (data.type) {
      case 'debate_started':
        console.log('[DEBATE_STARTED] Debate ID:', data.debate_id);
        console.log('[DEBATE_STARTED] Assignment:', data.model_assignment);
        console.log('[DEBATE_STARTED] Resolution:', data.resolution);
        console.log('[DEBATE_STARTED] Models - PRO:', data.pro_model, 'CON:', data.con_model);

        const newDebate = {
          resolution: data.resolution,
          speeches: [],
          pro_model: data.pro_model || null,
          con_model: data.con_model || null
        };

        if (isFlipped) {
          console.log('[DEBATE_STARTED] Setting FLIPPED debate ID:', data.debate_id);
          setDebateIdFlipped(data.debate_id);
          setStatusFlipped('starting');
          setDebateFlipped(newDebate);
        } else {
          console.log('[DEBATE_STARTED] Setting ORIGINAL debate ID:', data.debate_id);
          setDebateId(data.debate_id);
          setStatus('starting');
          setDebate(newDebate);
        }
        break;
      
      case 'debate_status':
        console.log('[DEBATE_STATUS] Status:', data.status);
        console.log('[DEBATE_STATUS] Debate ID:', data.debate_id);
        console.log('[DEBATE_STATUS] Models - PRO:', data.pro_model, 'CON:', data.con_model);

        if (isFlipped) {
          setStatusFlipped(data.status);
          if (data.pro_model || data.con_model) {
            setDebateFlipped(prev => {
              if (!prev) {
                return {
                  resolution: '',
                  speeches: [],
                  pro_model: data.pro_model || null,
                  con_model: data.con_model || null
                };
              }
              return {
                ...prev,
                pro_model: data.pro_model || prev?.pro_model,
                con_model: data.con_model || prev?.con_model
              };
            });
          }
        } else {
          setStatus(data.status);
          if (data.pro_model || data.con_model) {
            setDebate(prev => {
              console.log('[DEBATE_STATUS] Previous debate state:', prev);
              if (!prev) {
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
        }
        break;
      
      case 'speech_started':
        console.log('[SPEECH_STARTED] Debate ID:', data.debate_id);
        console.log('[SPEECH_STARTED] Speech type:', data.speech_type, 'Side:', data.side);

        if (data.debate_id === debateId) {
          console.log('[SPEECH_STARTED] IDs match (original), setting status to running');
          setStatus('running');
        } else if (data.debate_id === debateIdFlipped) {
          console.log('[SPEECH_STARTED] IDs match (flipped), setting status to running');
          setStatusFlipped('running');
        }
        break;
      
      case 'speech_complete':
        console.log('[SPEECH_COMPLETE] Debate ID:', data.debate_id);
        console.log('[SPEECH_COMPLETE] Speech data:', data.speech);

        if (data.debate_id === debateId) {
          setDebate(prev => {
            const newSpeeches = [...(prev?.speeches || []), data.speech];
            console.log('[SPEECH_COMPLETE] Adding speech to original. Total speeches:', newSpeeches.length);
            return {
              ...prev,
              speeches: newSpeeches
            };
          });
        } else if (data.debate_id === debateIdFlipped) {
          setDebateFlipped(prev => {
            const newSpeeches = [...(prev?.speeches || []), data.speech];
            console.log('[SPEECH_COMPLETE] Adding speech to flipped. Total speeches:', newSpeeches.length);
            return {
              ...prev,
              speeches: newSpeeches
            };
          });
        }
        break;
      
      case 'debate_complete':
        console.log('[DEBATE_COMPLETE] Debate ID:', data.debate_id);
        console.log('[DEBATE_COMPLETE] Full debate data:', data.debate);

        if (data.debate_id === debateId) {
          setStatus('complete');
          setDebate(data.debate);
          console.log('[DEBATE_COMPLETE] Original debate completed');
        } else if (data.debate_id === debateIdFlipped) {
          setStatusFlipped('complete');
          setDebateFlipped(data.debate);
          console.log('[DEBATE_COMPLETE] Flipped debate completed');
        }
        break;
      
      case 'debate_error':
        console.error('[DEBATE_ERROR] Debate ID:', data.debate_id);
        console.error('[DEBATE_ERROR] Error:', data.error);

        if (data.debate_id === debateId) {
          setStatus('error');
          alert(`Error in original debate: ${data.error}`);
        } else if (data.debate_id === debateIdFlipped) {
          setStatusFlipped('error');
          alert(`Error in flipped debate: ${data.error}`);
        }
        break;
      
      default:
        break;
    }
  }, [debateId, debateIdFlipped]);

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
      console.log('[START_DEBATE] Starting debates with config:', config);
      // Clear previous debate states
      setDebateId(null);
      setDebateIdFlipped(null);
      setStatus('starting');
      setStatusFlipped('starting');

      // Initialize debate states
      const initialDebate = {
        resolution: config.resolution,
        speeches: [],
        pro_model: config.pro_model,
        con_model: config.con_model
      };

      const initialDebateFlipped = {
        resolution: config.resolution,
        speeches: [],
        pro_model: config.con_model,  // Flipped
        con_model: config.pro_model   // Flipped
      };

      setDebate(initialDebate);
      setDebateFlipped(initialDebateFlipped);

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
      const newDebateIdFlipped = response.data.debate_id_flipped;

      console.log('[START_DEBATE] Setting debate IDs:', newDebateId, newDebateIdFlipped);
      setDebateId(newDebateId);
      setDebateIdFlipped(newDebateIdFlipped);

      // Refresh debate list after starting
      setTimeout(fetchAllDebates, 1000);
    } catch (error) {
      console.error('[START_DEBATE] Error starting debates:', error);
      console.error('[START_DEBATE] Error details:', error.response?.data || error.message);
      setStatus('error');
      setStatusFlipped('error');
      setDebate(null);
      setDebateFlipped(null);
      alert(`Failed to start debates: ${error.message}`);
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
            className={`nav-button ${currentPage === 'judge' ? 'active' : ''}`}
            onClick={() => setCurrentPage('judge')}
          >
            Judge
          </button>
          <button
            className={`nav-button ${currentPage === 'history' ? 'active' : ''}`}
            onClick={() => setCurrentPage('history')}
          >
            History
          </button>
          <button
            className={`nav-button ${currentPage === 'judgebench-debates' ? 'active' : ''}`}
            onClick={() => setCurrentPage('judgebench-debates')}
          >
            JudgeBench Debates
          </button>
          <button
            className={`nav-button ${currentPage === 'judgebench' ? 'active' : ''}`}
            onClick={() => setCurrentPage('judgebench')}
          >
            JudgeBench
          </button>
        </nav>
      </header>
      
      <main className="App-main">
        {currentPage === 'debate' ? (
          <>
            <DebateConfig
              onStart={startDebate}
              status={status === 'running' || statusFlipped === 'running' ? 'running' : status}
            />

            <div className="debates-container">
              {debate && (
                <DebateDisplay
                  debate={debate}
                  status={status}
                  debateId={debateId}
                />
              )}

              {debateFlipped && (
                <DebateDisplay
                  debate={debateFlipped}
                  status={statusFlipped}
                  debateId={debateIdFlipped}
                />
              )}
            </div>
          </>
        ) : currentPage === 'judge' ? (
          <JudgePage />
        ) : currentPage === 'judgebench-debates' ? (
          <JudgeBenchDebatesPage />
        ) : currentPage === 'judgebench' ? (
          <JudgeBenchPage />
        ) : (
          <HistoryPage />
        )}
      </main>
    </div>
  );
}

export default App;

