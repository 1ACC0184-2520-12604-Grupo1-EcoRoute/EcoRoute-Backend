from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from pydantic import BaseModel
from pathlib import Path
import json

from app.core.security import get_current_user
from app.auth.schemas import UserOut

router = APIRouter(prefix="/reports", tags=["Reports"])

DATA_PATH = Path("app/data/reports.json")


class ReportCreate(BaseModel):
    title: str
    algorithm: str  # "dijkstra" | "kruskal" | "tsp"
    description: str
    result_summary: str


class ReportOut(ReportCreate):
    id: int
    user: str
    created_at: str
    hidden: bool


def _load_reports():
    if not DATA_PATH.exists():
        return []
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_reports(reports):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)


@router.get("/me", response_model=List[ReportOut])
async def get_my_reports(current_user: UserOut = Depends(get_current_user)):
    reports = _load_reports()
    return [
        r
        for r in reports
        if r.get("user") == current_user.username and not r.get("hidden", False)
    ]


@router.post("", response_model=ReportOut)
async def create_report(
    payload: ReportCreate,
    current_user: UserOut = Depends(get_current_user),
):
    reports = _load_reports()
    new_id = max((r.get("id", 0) for r in reports), default=0) + 1

    new_report = {
        "id": new_id,
        "user": current_user.username,
        "title": payload.title,
        "algorithm": payload.algorithm,
        "description": payload.description,
        "result_summary": payload.result_summary,
        "created_at": datetime.utcnow().isoformat(),
        "hidden": False,
    }

    reports.append(new_report)
    _save_reports(reports)
    return new_report


@router.patch("/{report_id}/hide", response_model=ReportOut)
async def hide_report(
    report_id: int,
    current_user: UserOut = Depends(get_current_user),
):
    reports = _load_reports()

    for r in reports:
        if r.get("id") == report_id and r.get("user") == current_user.username:
            r["hidden"] = True
            _save_reports(reports)
            return r

    raise HTTPException(
        status_code=404,
        detail="Reporte no encontrado o no pertenece al usuario.",
    )
