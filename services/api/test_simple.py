"""
最简单的API测试服务
用于验证基础环境是否正常
"""

from fastapi import FastAPI
import uvicorn

# 创建FastAPI应用
app = FastAPI(title="AI-Sound TTS API Test", version="1.0.0")

@app.get("/")
def root():
    """根路径"""
    return {
        "message": "AI-Sound TTS API Test",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ai-sound-api",
        "message": "服务运行正常"
    }

@app.get("/test")
def test_endpoint():
    """测试端点"""
    return {
        "test": "success",
        "message": "API测试成功"
    }

if __name__ == "__main__":
    print("启动AI-Sound TTS API测试服务...")
    print("服务地址: http://localhost:9930")
    print("健康检查: http://localhost:9930/health")
    print("按 Ctrl+C 停止服务")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9930,
        reload=False,
        log_level="info"
    )