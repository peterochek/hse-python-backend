from dataclasses import dataclass, field
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


@dataclass(slots=True)
class ChatRoom:
    subscribers: list[WebSocket] = field(init=False, default_factory=list)

    async def subscribe(self, ws: WebSocket) -> None:
        await ws.accept()
        self.subscribers.append(ws)

    async def unsubscribe(self, ws: WebSocket) -> None:
        self.subscribers.remove(ws)

    async def publish(self, message: str) -> None:
        for ws in self.subscribers:
            await ws.send_text(message)

chat_rooms = {}

@app.websocket("/chat/{chat_name}")
async def ws_chat(ws: WebSocket, chat_name: str):
    client_id = uuid4()
    if chat_name not in chat_rooms:
        chat_rooms[chat_name] = ChatRoom()

    chat_room = chat_rooms[chat_name]
    await chat_room.subscribe(ws)
    await chat_room.publish(f"client {client_id} subscribed")
    try:
        while True:
            message = await ws.receive_text()
            await chat_room.publish(message)
    except WebSocketDisconnect:
        chat_room.unsubscribe(ws)
        await chat_room.publish(f"client {client_id} unsubscribed")