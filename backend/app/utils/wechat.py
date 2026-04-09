# app/utils/wechat.py
import os
import httpx
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

WECHAT_APP_ID = os.getenv("WECHAT_APP_ID")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET")

class WeChatAuthError(Exception):
    """自定义微信认证异常"""
    pass

async def code_to_session(code: str) -> dict:
    """
    用前端传来的 code 换取 openid 和 session_key
    文档: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
    """
    if not WECHAT_APP_ID or not WECHAT_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Server misconfiguration: Missing WeChat credentials."
        )

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WECHAT_APP_ID,
        "secret": WECHAT_APP_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }

    try:
        # 使用异步客户端，设置超时时间防止卡死
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status() # 如果网络层报错(404/500)直接抛出
            
            data = response.json()
            
            # 微信接口只要返回了 errcode 且不为 0，就是业务错误
            if "errcode" in data and data["errcode"] != 0:
                error_msg = data.get("errmsg", "Unknown WeChat error")
                print(f" WeChat API Error: {data}") # 生产环境应用 logging.error
                raise WeChatAuthError(f"WeChat login failed: {error_msg}")
            
            return {
                "openid": data.get("openid"),
                "unionid": data.get("unionid"), # 只有绑定了开放平台才有
                "session_key": data.get("session_key")
            }

    except httpx.RequestError as e:
        # 网络连通性问题
        print(f" WeChat Network Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to connect to WeChat server"
        )
    except WeChatAuthError as e:
        # 业务逻辑错误 (如 code 无效)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )