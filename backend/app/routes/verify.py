from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Client, Verification
from app.middleware.auth import get_current_client
from app.middleware.rate_limit import rate_limit
from app.schemas.verify import BreakdownScores, VerifyResponse
from app.services import verification as verification_service

router = APIRouter()


@router.post("/verify", response_model=VerifyResponse)
async def verify_image(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(rate_limit),  # rate_limit also resolves get_current_client
):
    return await verification_service.process_verification(db, client, image)


@router.get("/verify/{verification_id}", response_model=VerifyResponse)
async def get_verification(
    verification_id: UUID,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    result = await db.execute(
        select(Verification)
        .where(Verification.id == verification_id)
        .where(Verification.client_id == client.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "VERIFICATION_NOT_FOUND", "message": "No such verification for this client"},
        )
    return {
        "verification_id": row.id,
        "trust_score": row.trust_score,
        "verdict": row.verdict,
        "confidence": row.confidence,
        "processing_ms": row.processing_ms or 0,
        "cached": row.cached,
        "billed_naira": row.billed_amount,
        "balance_remaining": client.balance_naira,
        "breakdown": BreakdownScores(
            spatial_score=row.spatial_score or 0,
            frequency_score=row.frequency_score or 0,
        ),
    }
