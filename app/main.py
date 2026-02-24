from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import runs, mapping, rule_params, audit
from app.core.config import PROJECT_NAME

app = FastAPI(
    title=PROJECT_NAME,
    description="医院科室绩效核算系统 API",
    version="1.0.0"
)

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs.router)
app.include_router(mapping.router)
app.include_router(rule_params.router)
app.include_router(audit.router)


@app.get("/")
def root():
    """API 根路径"""
    return {
        "message": "绩效核算系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy"}
