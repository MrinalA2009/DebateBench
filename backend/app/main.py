"""FastAPI backend for DebateBench"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from pydantic import BaseModel
import sys
import asyncio
from pathlib import Path
import json
from functools import partial

# Add parent directory to path for debatebench import
sys.path.insert(0, str(Path(__file__).parent.parent))

from debatebench import DebateRunner, OpenRouterClient, Debate, Speech, SpeechType
from debatebench.storage import save_debate, load_debate, load_all_debates
from debatebench.judge_prompts import get_judge_prompt

app = FastAPI(title="DebateBench API", version="1.0.0")

# Load debates from disk on startup
active_debates: Dict[str, Dict] = load_all_debates()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": "DebateBench API", "status": "running"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/debates/start")
async def start_debate(
    resolution: str,
    pro_model: str,
    con_model: str,
    temperature: float = 0.7,
    prompt_style: str = "standard"
):
    """Start a new debate"""
    import uuid
    debate_id = str(uuid.uuid4())
    
    # Store debate info
    debate_data = {
        "id": debate_id,
        "resolution": resolution,
        "pro_model": pro_model,
        "con_model": con_model,
        "temperature": temperature,
        "prompt_style": prompt_style,
        "status": "starting",
        "speeches": []
    }
    active_debates[debate_id] = debate_data
    save_debate(debate_id, debate_data)
    
    # Run debate in background
    asyncio.create_task(run_debate_task(debate_id, resolution, pro_model, con_model, temperature, prompt_style))
    
    return {"debate_id": debate_id, "status": "started"}


async def run_debate_task(
    debate_id: str,
    resolution: str,
    pro_model: str,
    con_model: str,
    temperature: float,
    prompt_style: str
):
    """Run debate and broadcast updates via WebSocket"""
    print(f"\n{'#'*80}")
    print(f"[DEBATE TASK] Starting new debate task")
    print(f"  Debate ID: {debate_id}")
    print(f"  Resolution: {resolution}")
    print(f"  PRO Model: {pro_model}")
    print(f"  CON Model: {con_model}")
    print(f"  Temperature: {temperature}")
    print(f"  Prompt Style: {prompt_style}")
    print(f"{'#'*80}\n")
    
    try:
        # Broadcast start
        print(f"[WEBSOCKET] Broadcasting debate_started event")
        await manager.broadcast({
            "type": "debate_started",
            "debate_id": debate_id,
            "resolution": resolution,
            "pro_model": pro_model,
            "con_model": con_model
        })
        
        # Initialize
        client = OpenRouterClient()
        runner = DebateRunner(
            client,
            temperature=temperature,
            prompt_style=prompt_style
        )
        
        debate = Debate(
            resolution=resolution,
            pro_model=pro_model,
            con_model=con_model
        )
        
        active_debates[debate_id]["status"] = "running"
        active_debates[debate_id]["pro_model"] = pro_model
        active_debates[debate_id]["con_model"] = con_model
        save_debate(debate_id, active_debates[debate_id])
        await manager.broadcast({
            "type": "debate_status",
            "debate_id": debate_id,
            "status": "running",
            "pro_model": pro_model,
            "con_model": con_model
        })
        
        # Generate each speech (run in executor to avoid blocking)
        import concurrent.futures
        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor()
        
        for speech_type in runner.protocol.turn_order:
            # Determine model and side
            if "pro" in speech_type.value:
                model = pro_model
                side = "PRO"
            else:
                model = con_model
                side = "CON"
            
            print(f"\n[DEBATE TASK] Starting speech generation:")
            print(f"  Debate ID: {debate_id}")
            print(f"  Speech type: {speech_type.value}")
            print(f"  Model: {model}")
            print(f"  Side: {side}\n")
            
            # Broadcast speech start
            await manager.broadcast({
                "type": "speech_started",
                "debate_id": debate_id,
                "speech_type": speech_type.value,
                "side": side
            })
            print(f"[WEBSOCKET] Broadcasted speech_started for {speech_type.value}")
            
            # Generate speech (run in executor since it's blocking I/O)
            # Use functools.partial to properly capture variables for the executor
            try:
                speech = await loop.run_in_executor(
                    executor,
                    partial(runner.generate_speech, speech_type, debate, model, side)
                )
                print(f"[DEBATE TASK] Speech generated successfully")
            except Exception as e:
                print(f"[ERROR] Failed to generate speech: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            
            debate.add_speech(speech)
            print(f"[DEBATE TASK] Speech added to debate object")
            
            # Update active debates
            speech_data = {
                "speech_type": speech.speech_type.value,
                "content": speech.content,
                "word_count": speech.word_count,
                "side": side
            }
            active_debates[debate_id]["speeches"].append(speech_data)
            save_debate(debate_id, active_debates[debate_id])
            print(f"[DEBATE TASK] Speech data saved to active_debates and disk")
            print(f"  Speech data keys: {list(speech_data.keys())}")
            print(f"  Content length: {len(speech_data['content'])} chars")
            print(f"  Word count: {speech_data['word_count']}")
            
            # Broadcast speech complete
            await manager.broadcast({
                "type": "speech_complete",
                "debate_id": debate_id,
                "speech": speech_data
            })
            print(f"[WEBSOCKET] Broadcasted speech_complete for {speech_type.value}")
            print(f"  Broadcast payload size: {len(str(speech_data))} chars\n")
        
        executor.shutdown(wait=False)
        print(f"[DEBATE TASK] All speeches generated, shutting down executor")
        
        # Debate complete
        print(f"[DEBATE TASK] Marking debate as complete")
        active_debates[debate_id]["status"] = "complete"
        active_debates[debate_id]["debate"] = {
            "resolution": debate.resolution,
            "pro_model": debate.pro_model,
            "con_model": debate.con_model,
            "speeches": [
                {
                    "speech_type": s.speech_type.value,
                    "content": s.content,
                    "word_count": s.word_count,
                    "side": "PRO" if "pro" in s.speech_type.value else "CON"
                }
                for s in debate.speeches
            ]
        }
        save_debate(debate_id, active_debates[debate_id])
        
        print(f"[WEBSOCKET] Broadcasting debate_complete event")
        await manager.broadcast({
            "type": "debate_complete",
            "debate_id": debate_id,
            "debate": active_debates[debate_id]["debate"]
        })
        print(f"[DEBATE TASK] Debate task completed successfully")
        print(f"{'#'*80}\n")
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"\n{'#'*80}")
        print(f"[ERROR] Debate task failed!")
        print(f"  Debate ID: {debate_id}")
        print(f"  Error: {error_msg}")
        print(f"{'#'*80}")
        traceback.print_exc()
        print(f"{'#'*80}\n")
        active_debates[debate_id]["status"] = "error"
        active_debates[debate_id]["error"] = error_msg
        save_debate(debate_id, active_debates[debate_id])
        await manager.broadcast({
            "type": "debate_error",
            "debate_id": debate_id,
            "error": error_msg
        })


@app.get("/api/debates/{debate_id}")
async def get_debate(debate_id: str):
    """Get debate status"""
    # Check in-memory first, then try loading from disk
    if debate_id not in active_debates:
        loaded = load_debate(debate_id)
        if loaded:
            active_debates[debate_id] = loaded
        else:
            raise HTTPException(status_code=404, detail="Debate not found")
    return active_debates[debate_id]


@app.get("/api/debates")
async def list_debates():
    """List all debates"""
    # Reload from disk to get all saved debates
    disk_debates = load_all_debates()
    # Merge with active debates (active takes precedence)
    all_debates = {**disk_debates, **active_debates}
    return {"debates": list(all_debates.values())}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            # Echo back or handle client messages
            await websocket.send_json({"type": "pong", "message": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


class JudgeRequest(BaseModel):
    debate_id: str
    judge_model: str
    judge_prompt: str


@app.post("/api/judge")
async def judge_debate(request: JudgeRequest):
    """Judge a debate using an AI model

    Args:
        request: Judge request containing debate_id, judge_model, and judge_prompt

    Returns:
        Judgment result
    """
    debate_id = request.debate_id
    judge_model = request.judge_model
    judge_prompt = request.judge_prompt
    print(f"\n{'#'*80}")
    print(f"[JUDGE] Starting judgment")
    print(f"  Debate ID: {debate_id}")
    print(f"  Judge Model: {judge_model}")
    print(f"  Judge Prompt: {judge_prompt}")
    print(f"{'#'*80}\n")

    try:
        # Load debate
        debate_data = load_debate(debate_id)
        if not debate_data:
            raise HTTPException(status_code=404, detail="Debate not found")

        # Check if debate is complete
        if debate_data.get('status') != 'complete':
            raise HTTPException(status_code=400, detail="Debate is not complete")

        # Get debate speeches
        speeches = debate_data.get('speeches', [])
        if not speeches:
            raise HTTPException(status_code=400, detail="No speeches found in debate")

        # Build transcript
        resolution = debate_data.get('resolution', 'Unknown')
        pro_model = debate_data.get('pro_model', 'Unknown')
        con_model = debate_data.get('con_model', 'Unknown')

        transcript = f"RESOLUTION: {resolution}\n\n"
        transcript += f"PRO: {pro_model}\n"
        transcript += f"CON: {con_model}\n"
        transcript += f"\n{'='*80}\n\n"

        for speech in speeches:
            side = speech.get('side', 'UNKNOWN')
            speech_type = speech.get('speech_type', 'unknown')
            content = speech.get('content', '')

            transcript += f"[{side}] {speech_type.upper().replace('_', ' ')}\n"
            transcript += f"{'-'*80}\n"
            transcript += f"{content}\n\n"
            transcript += f"{'='*80}\n\n"

        print(f"[JUDGE] Built transcript ({len(transcript)} chars)")

        # Get judge prompt
        prompt_text = get_judge_prompt(judge_prompt, transcript)
        print(f"[JUDGE] Generated prompt ({len(prompt_text)} chars)")

        # Call judge model
        client = OpenRouterClient()
        messages = [
            {"role": "system", "content": "You are an experienced debate judge."},
            {"role": "user", "content": prompt_text}
        ]

        print(f"[JUDGE] Calling {judge_model}...")
        judgment = client.call_model(
            model=judge_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

        print(f"[JUDGE] Received judgment ({len(judgment)} chars)")
        print(f"[JUDGE] Judgment complete\n")

        return {
            "judgment": judgment,
            "judge_model": judge_model,
            "judge_prompt": judge_prompt,
            "debate_id": debate_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to judge debate: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to judge debate: {str(e)}")

