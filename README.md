# DebateBench

A controlled, reproducible benchmark for AI-generated debates following Public Forum format.

## Architecture

DebateBench uses a **FastAPI backend + React frontend** architecture (similar to debatesim) with real-time WebSocket updates:

- **Backend**: FastAPI with WebSocket support for live debate progress
- **Frontend**: React with auto-updating UI via WebSocket connections
- **Real-time**: Speeches appear as they're generated

## Installation

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Or from the project root:

```bash
pip install -r backend/requirements.txt
```

**Note:** Make sure you're using the same Python environment where you'll run the backend.

### Frontend Setup

```bash
cd frontend
npm install
```

## Configuration

Create a `.env` file in the project root with your OpenRouter API key:

```
OPENROUTER_API_KEY=your_api_key_here
```

The `.env` file is automatically loaded using `python-dotenv`.

## Running the Application

### Start Backend (Terminal 1)

```bash
cd backend
uvicorn app.main:app --reload --port 8001
```

The API will be available at `http://localhost:8001`

### Start Frontend (Terminal 2)

```bash
cd frontend
PORT=3001 npm start
```

The UI will open at `http://localhost:3001`

## Quick Start Scripts

### Using the convenience scripts:

**Backend:**
```bash
./run_backend.sh
```

**Frontend:**
```bash
./run_frontend.sh
```

## Features

### Fixed Debate Protocol

- **Fixed Turn Order:**
  1. Pro Constructive (300 words)
  2. Con Constructive (300 words)
  3. Pro Rebuttal (250 words)
  4. Con Rebuttal (250 words)
  5. Pro Summary (200 words)
  6. Con Summary (200 words)

### Real-time Updates

- Speeches appear in real-time as they're generated
- Status updates via WebSocket
- Auto-refreshing UI without manual refresh

### UI Features

- Color-coded speeches (PRO: Blue, CON: Orange)
- Word count tracking
- Model metadata display
- Load saved debates by ID
- Clean, modern interface

## API Endpoints

- `GET /` - API health check
- `GET /api/health` - Health status
- `POST /api/debates/start` - Start a new debate
- `GET /api/debates/{debate_id}` - Get debate status
- `GET /api/debates` - List all debates
- `WS /ws` - WebSocket endpoint for real-time updates

## Project Structure

```
DebateBench/
├── backend/
│   ├── debatebench/         # Core library
│   │   ├── __init__.py
│   │   ├── protocol.py
│   │   ├── client.py
│   │   ├── runner.py
│   │   └── prompts.py
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DebateConfig.js
│   │   │   ├── DebateDisplay.js
│   │   │   └── ...
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── .env                     # API keys (not in git)
└── README.md
```

## Development

### Testing the Protocol

```bash
python3 test_protocol.py
```

### Running with Docker (Future)

A `docker-compose.yml` can be added for containerized deployment.

## Next Steps

- Part B: JudgeBench (AI judging protocol)
- Part C: Leaderboard construction with ELO
- Part D: Stability and reliability analysis
