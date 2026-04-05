import os
import uuid
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator

from models import LikeRequest, CommentRequest
from producers import produce_like, produce_comment

logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter(
    "api_requests_total", "Total API requests", ["endpoint", "method"]
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds", "API request latency", ["endpoint"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Notification API starting up")
    yield
    logger.info("Notification API shutting down")


app = FastAPI(
    title="Notification System API",
    description="Ingestion layer for like and comment events",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())


@app.post("/like", status_code=202)
async def create_like(body: LikeRequest):
    start = time.time()
    try:
        REQUEST_COUNT.labels(endpoint="/like", method="POST").inc()
        event_id = str(uuid.uuid4())
        produce_like(user_id=body.user_id, post_id=body.post_id, event_id=event_id)
        return {"event_id": event_id, "status": "accepted"}
    except Exception as e:
        logger.error("Failed to produce like event: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        REQUEST_LATENCY.labels(endpoint="/like").observe(time.time() - start)


@app.post("/comment", status_code=202)
async def create_comment(body: CommentRequest):
    start = time.time()
    try:
        REQUEST_COUNT.labels(endpoint="/comment", method="POST").inc()
        event_id = str(uuid.uuid4())
        produce_comment(
            user_id=body.user_id,
            post_id=body.post_id,
            content=body.content,
            event_id=event_id,
        )
        return {"event_id": event_id, "status": "accepted"}
    except Exception as e:
        logger.error("Failed to produce comment event: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        REQUEST_LATENCY.labels(endpoint="/comment").observe(time.time() - start)
