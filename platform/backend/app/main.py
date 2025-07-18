from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request, HTTPException

app = FastAPI(
    title="AI-Sound API",
    description="AI-Sound Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 配置文件上传大小限制
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import json

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length:
                content_length = int(content_length)
                if content_length > 52428800:  # 50MB in bytes
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "File too large. Maximum size allowed is 50MB"}
                    )
        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 导入路由
from app.api.v1 import api_router
app.include_router(api_router, prefix="/api/v1")

# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )