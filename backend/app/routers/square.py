# app/routers/square.py
import os
import json
import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas, models, deps
from app.utils import ai_engine
from app.constants.islands import ISLAND_KEYS

logger = logging.getLogger(__name__)
router = APIRouter()

# =============== 1.AI 推荐标签 =========================
@router.post("/tags/suggest", response_model=List[str])
async def suggest_tags(
    ticket_uid: str, # 前端传 ticket_uid 过来
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    用户点击“发送到岛屿”时调用。
    AI 实时读取 Ticket 的日记内容，生成推荐 Tag。
    """
    # 1. 查票
    ticket = crud.get_ticket_by_uid(db, ticket_uid)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # 2. 只有本人能操作
    if ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 3. 调 AI 生成
    # 使用 user_diary_summary (用户的原始心事)
    if not ticket.user_diary_summary:
        return ["#心情"]
        
    tags = await ai_engine.generate_suggested_tags(ticket.user_diary_summary)
    
    return tags


# ================= 2. 发送到岛屿 (Publish) =================
@router.post("/publish", response_model=schemas.TicketDTO)
def publish_to_island(
    publish_req: schemas.CardPublishRequest,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    【核心】点击“发送到岛屿”
    1. 校验卡片归属
    2. 更新 is_public = True
    3. 更新 selected_tags
    """
    ticket = crud.get_ticket_by_uid(db, publish_req.ticket_uid)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 执行发布
    published_ticket = crud.publish_ticket_to_island(
        db, 
        ticket_uid=ticket.ticket_uid, 
        tags=publish_req.selected_tags
    )
    
    # 这里应该埋点: island_publish_success
    
    return published_ticket

# ================= 3. 获取地图星星数据 (/map) =================
@router.get("/map/{island_key}", response_model=List[schemas.MapStarDTO])
def get_island_stars(
    island_key: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    获取某座岛屿的星星数据 (公开卡片)
    前端拿到后，随机分布在星空背景上。
    """
    # 校验岛屿是否存在
    if island_key not in ISLAND_KEYS:
        raise HTTPException(status_code=404, detail="Island not found")

    stars = crud.get_public_tickets_by_island(db, island_key, limit=50)
    return stars


@router.get("/island-tags/{island_key}", response_model=List[schemas.IslandTagDTO])
def get_island_tags(
    island_key: str,
    limit: int,
    preferred_tag: Optional[str] = None,
    preferred_ticket_uid: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    if island_key not in ISLAND_KEYS:
        raise HTTPException(status_code=404, detail="Island not found")

    if limit <= 0:
        return []

    return crud.get_public_island_tags(
        db,
        island_key=island_key,
        limit=limit,
        preferred_tag=preferred_tag,
        preferred_ticket_uid=preferred_ticket_uid,
    )

# ================= 4. 互动: 抱抱/查看 (/interact) =================
@router.post("/interact/{ticket_uid}")
def interact_with_card(
    ticket_uid: str,
    action_type: str, # "hug" or "view" (query param)
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    给别人的卡片一个抱抱
    """
    if action_type not in ["hug", "view"]:
         raise HTTPException(status_code=400, detail="Invalid action type")
         
    crud.increment_interaction(db, ticket_uid, action_type)
    return {"status": "ok", "action": action_type}
