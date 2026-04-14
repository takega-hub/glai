import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.database.connection import connect_to_db, close_db_connection, run_migrations, get_db
from api.routers import auth, monetization, content, dialogue, analytics, on_demand, re_engagement, ai_scenarist, characters, layers, ai_editor, user_state, admin, prompts, content_generation, user_characters, user_content, tokens, user_analytics, profile, user_profile, comfy_workflows, notifications
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS Middleware
origins = [
    "http://admin-eva.midoma.ru:5173",
    "https://admin-eva.midoma.ru",
    "https://eva.midoma.ru",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Mount the uploads directory to serve static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from typing import List, Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # For now, we don't need to handle incoming messages, just outgoing
    except WebSocketDisconnect:
        manager.disconnect(user_id)

app.include_router(auth.router)
app.include_router(monetization.router)
app.include_router(content.router)
app.include_router(dialogue.router)
app.include_router(analytics.router)
app.include_router(on_demand.router)
app.include_router(re_engagement.router)
app.include_router(ai_scenarist.router)
app.include_router(characters.router)
app.include_router(layers.router)
app.include_router(ai_editor.router)
app.include_router(user_state.router)
app.include_router(admin.router)
app.include_router(prompts.router)
app.include_router(content_generation.router)
app.include_router(user_characters.router)
app.include_router(user_content.router)
app.include_router(tokens.router)
app.include_router(user_analytics.router)
app.include_router(profile.router)
app.include_router(user_profile.router)
app.include_router(comfy_workflows.router)
app.include_router(notifications.router)


@app.on_event("startup")
async def startup_event():
    await connect_to_db()
    # Run migrations
    # async for db_pool in get_db():
    #     await run_migrations(db_pool)
    #     break

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_connection()

@app.get("/")
def read_root():
    return {"message": "Welcome to EVA AI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
