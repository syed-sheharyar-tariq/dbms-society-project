import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.entities import Block, Category, Property
from app.schemas.society_schemas import (
    BlockResponse,
    CategoryResponse,
    PropertyResponse,
)

router = APIRouter(prefix="", tags=["Society & Master Data"])


@router.get("/blocks", response_model=List[BlockResponse])
async def list_blocks(
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
):
    stmt = select(Block)
    if active_only:
        stmt = stmt.where(Block.is_active.is_(True))
    stmt = stmt.order_by(Block.code)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/properties", response_model=List[PropertyResponse])
async def list_properties(
    block_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
):
    stmt = select(Property).options(selectinload(Property.block))
    if block_id:
        stmt = stmt.where(Property.block_id == block_id)
    if active_only:
        stmt = stmt.where(Property.is_active.is_(True))
    stmt = stmt.order_by(Property.property_number)
    res = await db.execute(stmt)
    props = res.scalars().all()
    
    response = []
    for p in props:
        response.append(
            PropertyResponse(
                id=p.id,
                block_id=p.block_id,
                property_number=p.property_number,
                property_type=p.property_type,
                address_note=p.address_note,
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at,
                block_name=p.block.name if p.block else None,
                block_code=p.block.code if p.block else None,
            )
        )
    return response


@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
):
    stmt = select(Category)
    if active_only:
        stmt = stmt.where(Category.is_active.is_(True))
    stmt = stmt.order_by(Category.name)
    res = await db.execute(stmt)
    return res.scalars().all()
