"""FastAPI backend for DebateBench"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
import sys
import asyncio
from pathlib import Path
import json
from functools import partial
from datetime import datetime

# Add parent directory to path for debatebench import
sys.path.insert(0, str(Path(__file__).parent.parent))

from debatebench import DebateRunner, OpenRouterClient, Debate, Speech, SpeechType
from debatebench.storage import save_debate, load_debate, load_all_debates
from debatebench.judge_prompts import get_judge_prompt
from debatebench import judgebench

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
    """Start two new debates with flipped model assignments"""
    import uuid

    import time
    created_timestamp = time.time()

    # Create first debate (original assignment)
    debate_id_1 = str(uuid.uuid4())
    debate_data_1 = {
        "id": debate_id_1,
        "resolution": resolution,
        "pro_model": pro_model,
        "con_model": con_model,
        "temperature": temperature,
        "prompt_style": prompt_style,
        "status": "starting",
        "speeches": [],
        "pair_id": None,  # Will link the paired debates
        "model_assignment": "original",
        "created_at": created_timestamp
    }

    # Create second debate (flipped assignment)
    debate_id_2 = str(uuid.uuid4())
    debate_data_2 = {
        "id": debate_id_2,
        "resolution": resolution,
        "pro_model": con_model,  # Flipped
        "con_model": pro_model,  # Flipped
        "temperature": temperature,
        "prompt_style": prompt_style,
        "status": "starting",
        "speeches": [],
        "pair_id": None,
        "model_assignment": "flipped",
        "created_at": created_timestamp
    }

    # Link the paired debates
    debate_data_1["pair_id"] = debate_id_2
    debate_data_2["pair_id"] = debate_id_1

    # Store both debates
    active_debates[debate_id_1] = debate_data_1
    active_debates[debate_id_2] = debate_data_2
    save_debate(debate_id_1, debate_data_1)
    save_debate(debate_id_2, debate_data_2)

    # Run both debates in background (in parallel)
    asyncio.create_task(run_debate_task(debate_id_1, resolution, pro_model, con_model, temperature, prompt_style))
    asyncio.create_task(run_debate_task(debate_id_2, resolution, con_model, pro_model, temperature, prompt_style))

    return {
        "debate_id": debate_id_1,
        "debate_id_flipped": debate_id_2,
        "status": "started",
        "message": "Two debates started with flipped model assignments"
    }


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
        debate_data = active_debates.get(debate_id, {})
        await manager.broadcast({
            "type": "debate_started",
            "debate_id": debate_id,
            "resolution": resolution,
            "pro_model": pro_model,
            "con_model": con_model,
            "model_assignment": debate_data.get("model_assignment", "unknown")
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
            "con_model": con_model,
            "model_assignment": active_debates[debate_id].get("model_assignment", "unknown")
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

        # Save judgment to debate
        import time
        judge_entry = {
            "judge_model": judge_model,
            "judge_prompt": judge_prompt,
            "judgment": judgment,
            "timestamp": time.time()
        }

        if "judges" not in debate_data:
            debate_data["judges"] = []
        debate_data["judges"].append(judge_entry)

        # Save to disk and update active debates
        save_debate(debate_id, debate_data)
        if debate_id in active_debates:
            active_debates[debate_id] = debate_data

        print(f"[JUDGE] Saved judgment to debate (total judges: {len(debate_data['judges'])})")

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


# ============================================================================
# JUDGEBENCH ENDPOINTS
# ============================================================================

@app.get("/api/judgebench/config")
async def get_judgebench_config():
    """Get JudgeBench configuration"""
    try:
        config = judgebench.load_judgebench_config()
        return {"config": config}
    except Exception as e:
        print(f"[ERROR] Failed to get JudgeBench config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


class JudgeBenchConfigRequest(BaseModel):
    judge_models: List[str]
    judge_prompts: List[str]
    num_debates: int
    runs_per_debate: int
    temperature: float


@app.post("/api/judgebench/config")
async def set_judgebench_config(request: JudgeBenchConfigRequest):
    """Set JudgeBench configuration"""
    try:
        config = {
            "judge_models": request.judge_models,
            "judge_prompts": request.judge_prompts,
            "num_debates": request.num_debates,
            "runs_per_debate": request.runs_per_debate,
            "temperature": request.temperature,
            "created_at": datetime.now().isoformat()
        }
        judgebench.save_judgebench_config(config)
        return {"success": True, "config": config}
    except Exception as e:
        print(f"[ERROR] Failed to set JudgeBench config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set config: {str(e)}")


@app.get("/api/judgebench/debates")
async def get_judgebench_debates():
    """Get all JudgeBench debates"""
    try:
        debates = judgebench.load_all_judgebench_debates()
        return {"debates": debates, "count": len(debates)}
    except Exception as e:
        print(f"[ERROR] Failed to get JudgeBench debates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get debates: {str(e)}")


class GenerateDebatesRequest(BaseModel):
    temperature: float = 1.0
    prompt_style: str = "analytical"


@app.post("/api/judgebench/debates/generate")
async def generate_judgebench_debates(request: GenerateDebatesRequest):
    """Generate 25 paired debates for JudgeBench"""
    try:
        # Load topics
        topics_path = Path(__file__).parent.parent.parent / "judgebench_topics.json"
        with open(topics_path, 'r') as f:
            topics_data = json.load(f)

        topics = [t['resolution'] for t in topics_data['topics']]

        # Model pairs with debate counts
        model_pairs = [
            ("openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct", 8),
            ("openai/gpt-4o-mini", "google/gemini-2.5-flash", 8),
            ("meta-llama/llama-3.3-70b-instruct", "google/gemini-2.5-flash", 9)
        ]

        debate_ids = []
        topic_idx = 0

        # Generate debates for each model pair
        for pro_model, con_model, count in model_pairs:
            for i in range(count):
                if topic_idx >= len(topics):
                    break

                resolution = topics[topic_idx]
                topic_idx += 1

                # Start paired debates (original + flipped)
                response = await start_debate(
                    resolution=resolution,
                    pro_model=pro_model,
                    con_model=con_model,
                    temperature=request.temperature,
                    prompt_style=request.prompt_style
                )

                # Save both debate IDs
                debate_ids.append({
                    "original": response["debate_id"],
                    "flipped": response["debate_id_flipped"],
                    "resolution": resolution,
                    "pro_model": pro_model,
                    "con_model": con_model
                })

        return {
            "success": True,
            "total_pairs": len(debate_ids),
            "debate_ids": debate_ids
        }

    except Exception as e:
        print(f"[ERROR] Failed to generate debates: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate debates: {str(e)}")


class SelectDebatesRequest(BaseModel):
    debate_ids: List[str]


@app.post("/api/judgebench/debates/select")
async def select_judgebench_debates(request: SelectDebatesRequest):
    """Copy selected debates to JudgeBench set"""
    try:
        count = 0
        for debate_id in request.debate_ids:
            debate_data = load_debate(debate_id)
            if debate_data:
                judgebench.save_judgebench_debate(debate_id, debate_data)
                count += 1

        return {"success": True, "count": count}
    except Exception as e:
        print(f"[ERROR] Failed to select debates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to select debates: {str(e)}")


@app.delete("/api/judgebench/debates/clear")
async def clear_judgebench_debates():
    """Clear all JudgeBench debates"""
    try:
        import shutil
        # Clear debate IDs file
        ids_file = judgebench.JUDGEBENCH_DIR / "debate_ids.json"
        if ids_file.exists():
            ids_file.unlink()

        # Clear all debate files
        debates_dir = judgebench.JUDGEBENCH_DEBATES_DIR
        if debates_dir.exists():
            shutil.rmtree(debates_dir)
            judgebench.ensure_judgebench_dirs()

        return {"success": True, "message": "All JudgeBench debates cleared"}
    except Exception as e:
        print(f"[ERROR] Failed to clear debates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear debates: {str(e)}")


def build_debate_transcript(debate: Dict) -> str:
    """Build debate transcript from debate data"""
    resolution = debate.get('resolution', 'Unknown')
    pro_model = debate.get('pro_model', 'Unknown')
    con_model = debate.get('con_model', 'Unknown')
    speeches = debate.get('speeches', [])

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
    
    return transcript


async def judge_single_debate_run(
    debate: Dict,
    judge_model: str,
    judge_prompt: str,
    judge_config: str,
    run_number: int,
    temperature: float,
    skip_existing: bool = True
) -> Tuple[bool, Optional[Dict]]:
    """Judge a single debate run. Returns (success: bool, result: Optional[Dict])"""
    debate_id = debate.get("id")
    if not debate_id:
        return False, None
    
    if skip_existing and judgebench.check_judgment_exists(judge_config, debate_id, run_number):
        print(f"[SKIP] Judgment already exists: {judge_config}/{debate_id}_run{run_number}")
        return True, None
    
    try:
        import time
        import re
        
        transcript = build_debate_transcript(debate)
        prompt_text = get_judge_prompt(judge_prompt, transcript)
        
        client = OpenRouterClient()
        messages = [
            {"role": "system", "content": "You are an experienced debate judge."},
            {"role": "user", "content": prompt_text}
        ]
        
        judgment = client.call_model(
            model=judge_model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        
        json_match = re.search(r'\{[\s\S]*\}', judgment)
        parsed = None
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
            except:
                pass
        
        result = {
            "debate_id": debate_id,
            "judge_model": judge_model,
            "judge_prompt": judge_prompt,
            "run_number": run_number,
            "judgment": judgment,
            "winner": parsed.get("winner") if parsed else None,
            "scores": parsed.get("scores") if parsed else None,
            "confidence": parsed.get("confidence") if parsed else None,
            "short_reason": parsed.get("short_reason") if parsed else None,
            "timestamp": time.time()
        }
        
        judgebench.save_judgment_result(judge_config, debate_id, run_number, result)
        return True, result
        
    except Exception as e:
        print(f"[ERROR] Failed to judge debate {debate_id} run {run_number}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None


class RunExperimentRequest(BaseModel):
    judge_model: str
    judge_prompt: str
    temperature: float = 0.1


@app.post("/api/judgebench/run")
async def run_judgebench_experiment(request: RunExperimentRequest):
    """Run JudgeBench experiment for one judge configuration"""
    try:
        judge_config = f"{request.judge_model.replace('/', '_')}_{request.judge_prompt}"
        debates = judgebench.load_all_judgebench_debates()
        config = judgebench.load_judgebench_config()

        if not config:
            raise HTTPException(status_code=400, detail="JudgeBench config not set")

        runs_per_debate = config.get("runs_per_debate", 3)
        total_runs = 0
        skipped = 0
        errors = 0

        for debate in debates:
            debate_id = debate.get("id")
            if not debate_id:
                continue

            # Run multiple times
            for run_num in range(runs_per_debate):
                success, result = await judge_single_debate_run(
                    debate=debate,
                    judge_model=request.judge_model,
                    judge_prompt=request.judge_prompt,
                    judge_config=judge_config,
                    run_number=run_num,
                    temperature=request.temperature,
                    skip_existing=True
                )
                
                if success:
                    if result is None:
                        skipped += 1
                    else:
                        total_runs += 1
                else:
                    errors += 1

        return {
            "success": True,
            "judge_config": judge_config,
            "total_runs": total_runs,
            "skipped": skipped,
            "errors": errors
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to run experiment: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to run experiment: {str(e)}")


class RunAllConfigurationsRequest(BaseModel):
    skip_existing: bool = True
    temperature: Optional[float] = None  # If None, uses config temperature


@app.post("/api/judgebench/run-all")
async def run_all_judge_configurations(request: RunAllConfigurationsRequest):
    """Run repeated judging for all judge configurations. For each config, judges all debates R times."""
    try:
        import time
        start_time = time.time()
        
        # Load configuration
        config = judgebench.load_judgebench_config()
        if not config:
            raise HTTPException(status_code=400, detail="JudgeBench config not set. Please set config first.")
        
        judge_models = config.get("judge_models", [])
        judge_prompts = config.get("judge_prompts", [])
        runs_per_debate = config.get("runs_per_debate", 3)
        temperature = request.temperature if request.temperature is not None else config.get("temperature", 0.1)
        
        if not judge_models or not judge_prompts:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid config: judge_models={judge_models}, judge_prompts={judge_prompts}"
            )
        
        configurations = judgebench.enumerate_judge_configurations(judge_models, judge_prompts)
        num_configs = len(configurations)
        
        print(f"\n{'='*80}")
        print(f"[JUDGEBENCH] Starting full experiment run")
        print(f"[JUDGEBENCH] Judge models: {judge_models}")
        print(f"[JUDGEBENCH] Judge prompts: {judge_prompts}")
        print(f"[JUDGEBENCH] Total configurations: {num_configs}")
        print(f"[JUDGEBENCH] Temperature: {temperature}")
        print(f"[JUDGEBENCH] Runs per debate: {runs_per_debate}")
        print(f"[JUDGEBENCH] Skip existing: {request.skip_existing}")
        print(f"{'='*80}\n")
        
        # Load all debates
        debates = judgebench.load_all_judgebench_debates()
        num_debates = len(debates)
        
        if num_debates == 0:
            raise HTTPException(status_code=400, detail="No JudgeBench debates found. Please generate debates first.")
        
        print(f"[JUDGEBENCH] Loaded {num_debates} debates")
        print(f"[JUDGEBENCH] Total judgments to run: {num_configs} configs × {num_debates} debates × {runs_per_debate} runs = {num_configs * num_debates * runs_per_debate}\n")
        
        # Track progress
        total_judgments = num_configs * num_debates * runs_per_debate
        completed = 0
        skipped = 0
        errors = 0
        config_results = {}
        
        for config_idx, (judge_model, judge_prompt, judge_config) in enumerate(configurations, 1):
            print(f"\n[{config_idx}/{num_configs}] Processing configuration: {judge_config}")
            print(f"  Model: {judge_model}")
            print(f"  Prompt: {judge_prompt}")
            
            config_completed = 0
            config_skipped = 0
            config_errors = 0
            
            for debate_idx, debate in enumerate(debates, 1):
                debate_id = debate.get("id", "unknown")
                print(f"  [{debate_idx}/{num_debates}] Debate: {debate_id[:8]}...")
                
                for run_num in range(runs_per_debate):
                    success, result = await judge_single_debate_run(
                        debate=debate,
                        judge_model=judge_model,
                        judge_prompt=judge_prompt,
                        judge_config=judge_config,
                        run_number=run_num,
                        temperature=temperature,
                        skip_existing=request.skip_existing
                    )
                    
                    if success:
                        if result is None:
                            skipped += 1
                            config_skipped += 1
                        else:
                            completed += 1
                            config_completed += 1
                    else:
                        errors += 1
                        config_errors += 1
                    
                    total_processed = completed + skipped + errors
                    if total_judgments > 0 and total_processed % 10 == 0:
                        progress = total_processed / total_judgments * 100
                        print(f"    Progress: {progress:.1f}% ({total_processed}/{total_judgments})")
            
            config_results[judge_config] = {
                "completed": config_completed,
                "skipped": config_skipped,
                "errors": config_errors,
                "total": num_debates * runs_per_debate
            }
            
            print(f"  ✓ Configuration complete: {config_completed} new, {config_skipped} skipped, {config_errors} errors")
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"[JUDGEBENCH] Experiment complete!")
        print(f"[JUDGEBENCH] Total time: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"[JUDGEBENCH] Completed: {completed} judgments")
        print(f"[JUDGEBENCH] Skipped: {skipped} judgments")
        print(f"[JUDGEBENCH] Errors: {errors} judgments")
        print(f"{'='*80}\n")
        
        return {
            "success": True,
            "summary": {
                "total_configurations": num_configs,
                "total_debates": num_debates,
                "runs_per_debate": runs_per_debate,
                "total_judgments": total_judgments,
                "completed": completed,
                "skipped": skipped,
                "errors": errors,
                "elapsed_seconds": elapsed_time
            },
            "configurations": config_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to run all configurations: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to run all configurations: {str(e)}")


@app.get("/api/judgebench/results")
async def get_judgebench_results():
    """Get JudgeBench metrics and results"""
    try:
        config = judgebench.load_judgebench_config()
        if not config:
            return {"metrics": {}, "rankings": []}

        # Load all results
        all_results = {}
        for judge_model in config.get("judge_models", []):
            for judge_prompt in config.get("judge_prompts", []):
                judge_config = f"{judge_model.replace('/', '_')}_{judge_prompt}"
                results = judgebench.load_judgment_results(judge_config)
                if results:
                    all_results[judge_config] = results

        # Compute metrics
        metrics = judgebench.compute_all_metrics(all_results)

        # Rank configurations
        rankings = judgebench.rank_judge_configurations(metrics)

        return {
            "metrics": metrics,
            "rankings": rankings,
            "config": config
        }

    except Exception as e:
        print(f"[ERROR] Failed to get results: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

