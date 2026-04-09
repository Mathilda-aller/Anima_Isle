from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, models, deps

router = APIRouter()

@router.get("/me", response_model=schemas.UserDTO)
def read_users_me(
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    【需登录】获取当前用户信息
    用于前端：
    1. 登录后展示用户昵称、头像
    2. 判断用户是否选过 ui_style_pref (如果是默认值，可能要弹窗让选)
    """
    return current_user

@router.post("/style", response_model=schemas.UserDTO)
def update_user_style(
    style_data: schemas.UserStyleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    【需登录】更新 UI 风格偏好 (Warm/Dark)
    这是 PRD 2.0 中登录后的关键一步，决定了 AI 生成图片的色调。
    """
    # 简单的参数校验
    if style_data.style_pref not in ["Warm", "Dark"]:
        raise HTTPException(status_code=400, detail="Invalid style preference. Must be 'Warm' or 'Dark'.")
        
    # 调用 CRUD 更新
    updated_user = crud.update_user_style(db, current_user.id, style_data.style_pref)
    return updated_user