from dataclasses import field
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import UUID4

app = FastAPI(title="Websocket chats")


class Chat:
    subscribers: list[WebSocket] = field(init=False, default_factory=list)

    async def subscribe(self, ws: WebSocket) -> None:
        await ws.accept()
        self.subscribers.append(ws)

    async def unsubscribe(self, ws: WebSocket) -> None:
        self.subscribers.remove(ws)

    async def publish(self, client_id: UUID4, message: str) -> None:
        text = f"{client_id} :: {message}"
        for ws in self.subscribers:
            await ws.send_text(text)


chats: dict[str, Chat] = {}


@app.websocket("/chat/{chat_name}")
async def ws_chat(ws: WebSocket, chat_name: str):
    client_id = uuid4()
    if chat_name not in chats:
        chats[chat_name] = Chat()

    chat_room = chats[chat_name]
    await chat_room.subscribe(ws)
    await chat_room.publish(client_id, "subscribed")
    try:
        while True:
            message = await ws.receive_text()
            await chat_room.publish(client_id, message)
    except WebSocketDisconnect:
        await chat_room.unsubscribe(ws)
        await chat_room.publish(client_id, "unsubscribed")
