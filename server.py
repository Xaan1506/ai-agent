import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from agent import AutonomousResearchAgent
import uvicorn
import json
import os

app = FastAPI(title="OpenClaw Research Agent API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/research")
async def research(target: str):
    async def event_generator():
        # Queue for status updates
        queue = asyncio.Queue()

        async def status_callback(message):
            await queue.put({"type": "status", "message": message})

        # Create the agent
        agent = AutonomousResearchAgent(target, status_callback=status_callback)
        
        # Run agent in a separate task
        agent_task = asyncio.create_task(agent.run())

        while not agent_task.done() or not queue.empty():
            try:
                # Check for status updates
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield {
                        "event": "update",
                        "data": json.dumps(update)
                    }
                except asyncio.TimeoutError:
                    pass

                # If agent is done, yield the final result
                if agent_task.done() and queue.empty():
                    try:
                        report = agent_task.result()
                        yield {
                            "event": "result",
                            "data": json.dumps({"type": "report", "content": report})
                        }
                    except Exception as e:
                        yield {
                            "event": "error",
                            "data": json.dumps({"type": "error", "message": str(e)})
                        }
                    break
                    
                await asyncio.sleep(0.1)
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({"type": "error", "message": str(e)})
                }
                break

    return EventSourceResponse(event_generator())

# Serve the React production build if dist directory exists
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(FRONTEND_PATH):
    # Route for the main page
    @app.get("/")
    async def get_index():
        return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))

    # Mount static files (JS, CSS, assets)
    app.mount("/", StaticFiles(directory=FRONTEND_PATH), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
