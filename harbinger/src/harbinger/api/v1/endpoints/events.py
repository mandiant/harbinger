import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from harbinger.crud import get_user_db
from harbinger.database.database import SessionLocal
from harbinger.database.redis_pool import redis_no_decode as redis
from harbinger.database.users import get_redis_strategy, get_user_manager

router = APIRouter()

REDIS_PUBSUB_CHANNEL = (
    "app_events_stream"
)

@router.websocket("/")
@router.websocket("")
async def websocket_events(websocket: WebSocket):
    cookie = websocket._cookies.get("fastapiusersauth", None)
    if not cookie:
        logging.warning("Authentication cookie 'fastapiusersauth' not found.")
        await websocket.close(code=1008, reason="Authentication required")
        return
    strat = get_redis_strategy()
    async with SessionLocal() as session:
        db = await anext(get_user_db(session))
        manager = await anext(get_user_manager(db))
        token = await strat.read_token(cookie, manager)
    if not token:
        logging.warning("Invalid or expired authentication token.")
        await websocket.close(code=1008, reason="Invalid or expired token")
        return
    await websocket.accept()
    logging.info(
        f"WebSocket client authenticated and accepted for user with token: {token}"
    )
    pubsub = redis.pubsub()
    try:
        await pubsub.subscribe(REDIS_PUBSUB_CHANNEL)
        logging.info(f"Subscribed to Redis channel: {REDIS_PUBSUB_CHANNEL}")

        async def redis_listener():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        payload_bytes = message["data"]
                        payload_str = payload_bytes.decode("utf-8")
                        await websocket.send_text(payload_str)
            except asyncio.CancelledError:
                logging.info("Redis listener task cancelled.")
            except Exception as e:
                logging.error(f"Error in Redis listener task: {e}")
            finally:
                logging.info("Unsubscribing from Redis Pub/Sub.")
                await pubsub.unsubscribe(REDIS_PUBSUB_CHANNEL)

        listener_task = asyncio.create_task(redis_listener())
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logging.info("WebSocket disconnected.")
        except Exception as e:
            logging.error(f"Error in WebSocket receive loop: {e}")
        finally:
            listener_task.cancel()
            await listener_task
            logging.info("WebSocket connection closed.")
    except Exception as e:
        logging.error(f"Error setting up Redis Pub/Sub for WebSocket: {e}")
        await websocket.close(
            code=1011, reason="Internal server error with event system"
        )