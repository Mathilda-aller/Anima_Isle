# app/routers/ticket.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas, models, deps

router = APIRouter()

# ================= 1. 获取时间轴列表 (Timeline) =================
@router.get("/list", response_model=List[schemas.TicketDTO])
def get_timeline(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    【记忆航线】获取用户的历史船票列表 (倒序排列)
    用于 Tab 2 展示。
    """
    tickets = crud.get_user_tickets(db, user_id=current_user.id, skip=skip, limit=limit)
    return tickets

# ================= 2. 获取单张详情 =================
@router.get("/{ticket_uid}", response_model=schemas.TicketDTO)
def get_ticket_detail(
    ticket_uid: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    获取单张卡片详情 (支持点进查看大图)
    """
    ticket = crud.get_ticket_by_uid(db, ticket_uid)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # 权限校验：只能看自己的，或者该卡片是公开的(is_public=True)
    if ticket.user_id != current_user.id and not ticket.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
        
    return ticket

# ================= 3. 烟雾测试 (Smoke Test) =================
@router.post("/{ticket_uid}/print_intent", response_model=schemas.TicketPrintResponse)
def record_print_intent(
    ticket_uid: str,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    记录打印意向
    逻辑：
    1. 前端 Tab 2 点击“兑换实体船票”按钮。
    2. 弹出“敬请期待” Toast 的同时，静默调用此接口。
    3. 后端将 is_printed_intent 置为 True。
    4. 运营人员通过 SQL 统计 True 的数量，计算转化率。
    """
    ticket = crud.get_ticket_by_uid(db, ticket_uid)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 核心业务逻辑
    crud.mark_ticket_print_intent(db, ticket_uid)
    
    return schemas.TicketPrintResponse(
        ticket_uid=ticket.ticket_uid,
        is_printed_intent=True,
        message="Intent recorded. Feature coming soon."
    )