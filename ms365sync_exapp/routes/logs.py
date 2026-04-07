"""Log retrieval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/{job_id}", response_class=PlainTextResponse)
def get_log(job_id: int, request: Request) -> str:
    return request.app.state.rclone.tail_log(lines=1000)


@router.get("/{job_id}/tail", response_class=PlainTextResponse)
def tail_log(job_id: int, request: Request, lines: int = 50) -> str:
    return request.app.state.rclone.tail_log(lines=lines)
