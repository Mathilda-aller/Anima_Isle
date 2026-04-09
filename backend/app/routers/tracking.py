from fastapi import APIRouter
from app import schemas, crud, deps
from sqlalchemy.orm import Session
from fastapi import Depends, BackgroundTasks

router = APIRouter()

@router.post("/log/event", response_model=schemas.BaseResponse, tags=["System"])
def log_client_event(
    event_req: schemas.EventLogSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    # 允许未登录用户上报(如启动App)，user_id 可为空
):
    """
    【通用埋点接口】接收前端上报的任何事件 (点击、浏览、停留时长)
    使用后台任务异步写入，绝不阻塞主线程。
    """
    background_tasks.add_task(crud.create_tracking_log, db, event_req)
    return schemas.BaseResponse(message="Event logged")