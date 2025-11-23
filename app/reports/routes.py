from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.auth.schemas import UserOut
from app.database import get_db
from app.models.analisis_resultados import AnalisisResultado

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportCreate(BaseModel):
    title: str
    algorithm: str  # "dijkstra" | "kruskal" | "tsp" | ...
    description: str
    result_summary: str


class ReportOut(ReportCreate):
    id: int
    user: str
    created_at: str
    hidden: bool


@router.get("/me", response_model=List[ReportOut])
async def get_my_reports(
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(AnalisisResultado)
        .filter(
            AnalisisResultado.user_id == current_user.id,
            AnalisisResultado.hidden == False,
        )
        .order_by(AnalisisResultado.created_at.asc())
        .all()
    )

    result: List[ReportOut] = []
    for r in rows:
        result.append(
            ReportOut(
                id=r.id,
                user=current_user.username,
                title=r.title,
                algorithm=r.algorithm,
                description=r.description,
                result_summary=r.result_summary,
                created_at=r.created_at.isoformat()
                if hasattr(r.created_at, "isoformat")
                else str(r.created_at),
                hidden=r.hidden,
            )
        )
    return result


@router.post("", response_model=ReportOut)
async def create_report(
    payload: ReportCreate,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Como tu tabla NO es AUTO_INCREMENT en el DDL, calculamos el siguiente id
    max_id = db.query(func.max(AnalisisResultado.id)).scalar() or 0
    new_id = max_id + 1

    now = datetime.utcnow()

    row = AnalisisResultado(
        id=new_id,
        user_id=current_user.id,
        title=payload.title,
        algorithm=payload.algorithm,
        description=payload.description,
        result_summary=payload.result_summary,
        created_at=now,
        hidden=False,
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return ReportOut(
        id=row.id,
        user=current_user.username,
        title=row.title,
        algorithm=row.algorithm,
        description=row.description,
        result_summary=row.result_summary,
        created_at=now.isoformat(),
        hidden=row.hidden,
    )


@router.patch("/{report_id}/hide", response_model=ReportOut)
async def hide_report(
    report_id: int,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(AnalisisResultado)
        .filter(
            AnalisisResultado.id == report_id,
            AnalisisResultado.user_id == current_user.id,
        )
        .first()
    )

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Reporte no encontrado o no pertenece al usuario.",
        )

    row.hidden = True
    db.commit()
    db.refresh(row)

    return ReportOut(
        id=row.id,
        user=current_user.username,
        title=row.title,
        algorithm=row.algorithm,
        description=row.description,
        result_summary=row.result_summary,
        created_at=row.created_at.isoformat()
        if hasattr(row.created_at, "isoformat")
        else str(row.created_at),
        hidden=row.hidden,
    )
