import asyncio
import logging
import re
import io
from typing import AsyncGenerator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import UUID4
from paramiko import (
    SSHClient,
    AutoAddPolicy,
    AuthenticationException,
    SSHException,
    RSAKey,
)
from harbinger import crud
from harbinger.crud import get_user_db
from harbinger.database.database import SessionLocal
from harbinger.database.redis_pool import redis_no_decode as redis
from harbinger.database.users import get_redis_strategy, get_user_manager
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def parse_tmate_ssh_username(output: str, readonly: bool = False) -> str:
    """
    Parses the tmate SSH connection string from the job output and returns just the username.
    Returns an empty string if the username cannot be found.
    """
    # Regex to capture the username part: ssh -p<port> <username>@
    username_pattern = r"ssh -p\d+\s+([a-zA-Z0-9_-]+)@"

    if readonly:
        match = re.search(r"ssh session read only: " + username_pattern, output)
    else:
        match = re.search(r"ssh session: " + username_pattern, output)

    if match:
        return match.group(1)  # Return the captured username
    return ""


async def get_db_ws() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_current_active_user(
    websocket: WebSocket,
):
    """
    Authenticates the user using the fastapiusersauth cookie.
    This is a simplified example; a real-world scenario might involve
    more robust token validation and user retrieval.
    """
    try:
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
            await websocket.close(code=1008, reason="Authentication failed")
            return None

        logging.info(f"User authenticated successfully for WebSocket.")
        return token

    except Exception as e:
        logging.error(f"Authentication error: {e}")
        await websocket.close(code=1011, reason=f"Authentication error: {e}")
        return None


dummy_key = RSAKey.generate(2048)


async def handle_ssh_websocket(
    websocket: WebSocket,
    username: str,
):
    """
    Handles the SSH websocket communication.
    """

    logging.info(f"Attempting SSH connection to {username}@tmate:2200 for user")

    ssh_client = None
    channel = None

    try:
        await websocket.accept()  # Accept connection after successful authentication and details retrieval

        ssh_client = SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())

        try:

            dummy_key_str = io.StringIO()
            dummy_key.write_private_key(dummy_key_str)
            dummy_key_str.seek(0)
            pkey = RSAKey.from_private_key(dummy_key_str)
            logging.info("Generated dummy SSH key for tmate connection attempt.")
        except Exception as e:
            logging.error(f"Failed to generate dummy SSH key for tmate connection: {e}")
            pkey = None  # Proceed without it if generation fails, though connection might fail

        ssh_client.connect(
            hostname="tmate",
            port=2200,
            username=username,
            pkey=pkey,  # Pass the dummy key to force publickey auth negotiation
            password=None,
            timeout=10,
            compress=True,
            allow_agent=False,  # Disable looking for SSH agent keys
            look_for_keys=False,  # Disable looking for ~/.ssh/id_rsa, etc.
        )
        logging.info(f"SSH connection established to for {username}.")

        channel = ssh_client.invoke_shell(term="xterm", width=80, height=24)
        channel.setblocking(0)  # Make channel non-blocking

        async def ssh_to_websocket():
            while True:
                try:
                    if channel.recv_ready():
                        data = channel.recv(4096).decode("utf-8", errors="ignore")
                        if data:
                            await websocket.send_text(data)
                    else:
                        await asyncio.sleep(0.01)  # Small delay to prevent busy-waiting
                except Exception as e:
                    logging.error(f"Error in ssh_to_websocket for user {username}: {e}")
                    break
            logging.info(f"ssh_to_websocket task finished for user {username}.")

        async def websocket_to_ssh():
            while True:
                try:
                    message = await websocket.receive_text()
                    if message:
                        if message.startswith("RESIZE:"):
                            try:
                                _, cols_str, rows_str = message.split(":")
                                cols = int(cols_str)
                                rows = int(rows_str)
                                channel.resize_pty(width=cols, height=rows)
                                logging.info(
                                    f"Resized PTY to cols={cols}, rows={rows} for user {username}"
                                )
                            except ValueError as ve:
                                logging.warning(
                                    f"Failed to parse resize message: {message} - {ve}"
                                )
                        else:
                            channel.send(message.encode("utf-8"))
                except WebSocketDisconnect:
                    logging.info(
                        f"WebSocket disconnected from client for user {username}."
                    )
                    break
                except Exception as e:
                    logging.error(f"Error in websocket_to_ssh for user {username}: {e}")
                    break
            logging.info(f"websocket_to_ssh task finished for user {username}.")

        await asyncio.gather(ssh_to_websocket(), websocket_to_ssh())

    except AuthenticationException:
        logging.error(
            f"SSH authentication failed for user {username} to {username}@tmate:2200."
        )
        await websocket.send_text(
            "SSH authentication failed. Please check the job output details."
        )
    except SSHException as e:
        logging.error(f"SSH connection or channel error for user {username}: {e}")
        try:
            await websocket.send_text(f"SSH error: {e}")
        except RuntimeError:
            pass  # WebSocket might already be closed
    except Exception as e:
        logging.error(
            f"Unexpected error in SSH connection handler for user {username}: {e}"
        )
        try:
            await websocket.send_text(f"An unexpected error occurred: {e}")
        except RuntimeError:
            pass  # WebSocket might already be closed
    finally:
        if channel:
            channel.close()
            logging.info(f"SSH channel closed for user {username}.")
        if ssh_client:
            ssh_client.close()
            logging.info(f"SSH client closed for user {username}.")
        logging.info(f"WebSocket connection handler finished for user {username}.")


@router.websocket("/ssh/readonly/{job_id}")
async def websocket_ssh_readonly_endpoint(websocket: WebSocket, job_id: str):
    user = await get_current_active_user(websocket)
    if not user:
        return
    logging.info(
        f"Attempting read-only SSH connection for job_id: {job_id} and user: {user.email}"
    )
    async with SessionLocal() as db:
        job_output = "\n".join(
            [entry.output for entry in await crud.get_proxy_job_output(db, job_id)]
        )
    username = parse_tmate_ssh_username(job_output, readonly=True)
    await handle_ssh_websocket(websocket, username)


@router.websocket("/ssh/interactive/{job_id}")
async def websocket_ssh_interactive_endpoint(websocket: WebSocket, job_id: str):
    user = await get_current_active_user(websocket)
    if not user:
        return
    logging.info(
        f"Attempting read-only SSH connection for job_id: {job_id} and user: {user.email}"
    )
    async with SessionLocal() as db:
        job_output = "\n".join(
            [entry.output for entry in await crud.get_proxy_job_output(db, job_id)]
        )
    username = parse_tmate_ssh_username(job_output, readonly=False)
    await handle_ssh_websocket(websocket, username)


@router.websocket("/plans/{plan_id}/llm_logs")
async def websocket_llm_logs(websocket: WebSocket, plan_id: UUID4):
    """
    WebSocket endpoint to stream real-time LLM logs for a specific plan.
    """
    cookie = websocket._cookies["fastapiusersauth"]
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
    channel = f"plan:llm_logs:{plan_id}"
    pubsub = redis.pubsub()

    async def redis_listener():
        """Listens to the Redis channel and forwards messages to the WebSocket."""
        try:
            await pubsub.subscribe(channel)
            logging.info(f"WebSocket subscribed to Redis channel: {channel}")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"].decode("utf-8"))
        except asyncio.CancelledError:
            logging.info(f"Redis listener for {channel} cancelled.")
        except Exception as e:
            logging.error(f"Error in Redis listener for {channel}: {e}")
        finally:
            await pubsub.unsubscribe(channel)

    listener_task = asyncio.create_task(redis_listener())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logging.info(f"WebSocket for plan {plan_id} disconnected.")
    finally:
        listener_task.cancel()
        await listener_task
