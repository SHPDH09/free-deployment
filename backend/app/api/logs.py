import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.deps import get_current_user
from app.core.security import decode_access_token
from app.database import async_session
from app.models import Deployment, DeploymentLog, Project, User
from app.services.github import get_redis, LOG_CHANNEL_PREFIX

router = APIRouter(tags=["logs"])


@router.websocket("/deployments/{deployment_id}/logs/stream")
async def stream_deployment_logs(websocket: WebSocket, deployment_id: uuid.UUID):
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=4001)
        return

    user_id = uuid.UUID(payload["sub"])

    async with async_session() as db:
        result = await db.execute(
            select(Deployment, Project)
            .join(Project, Deployment.project_id == Project.id)
            .where(Deployment.id == deployment_id, Project.user_id == user_id)
        )
        if not result.one_or_none():
            await websocket.close(code=4003)
            return

        logs_result = await db.execute(
            select(DeploymentLog)
            .where(
                DeploymentLog.deployment_id == deployment_id,
                DeploymentLog.is_user_visible.is_(True),
            )
            .order_by(DeploymentLog.created_at.asc())
        )
        for log in logs_result.scalars().all():
            await websocket.send_json({
                "message": log.message,
                "level": log.level,
                "step": log.step,
                "timestamp": log.created_at.isoformat(),
            })

    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"{LOG_CHANNEL_PREFIX}{deployment_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
