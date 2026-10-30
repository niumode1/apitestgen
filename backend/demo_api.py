"""本地演示 API — 用户管理系统

启动后自动导出 OpenAPI，可直接导入平台测试。

启动: python demo_api.py
文档: http://localhost:9001/docs
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

app = FastAPI(
    title="用户管理系统 API",
    description="演示用 — 支持增删改查的用户管理接口",
    version="1.0.0",
)

# ── 内存数据库 ──
users: dict[int, dict] = {
    1: {"id": 1, "name": "张三", "email": "zhangsan@example.com", "age": 28, "active": True},
    2: {"id": 2, "name": "李四", "email": "lisi@example.com", "age": 35, "active": True},
    3: {"id": 3, "name": "王五", "email": "wangwu@example.com", "age": 22, "active": False},
}
_next_id = 4


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    age: int = Field(default=18, ge=0, le=150, description="年龄")
    active: bool = Field(default=True, description="是否激活")


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=150)
    active: Optional[bool] = None


# ── 接口 ──

@app.get("/api/v1/users")
def list_users(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    active: Optional[bool] = Query(default=None, description="筛选激活状态"),
):
    """获取用户列表，支持分页和筛选"""
    result = list(users.values())
    if active is not None:
        result = [u for u in result if u["active"] == active]
    total = len(result)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": result[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/v1/users/{user_id}")
def get_user(user_id: int):
    """获取单个用户详情"""
    if user_id not in users:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    return users[user_id]


@app.post("/api/v1/users", status_code=201)
def create_user(user: UserCreate):
    """创建新用户"""
    global _next_id
    new_user = user.model_dump()
    new_user["id"] = _next_id
    users[_next_id] = new_user
    _next_id += 1
    return new_user


@app.put("/api/v1/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    """更新用户信息（部分更新）"""
    if user_id not in users:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    update_data = user.model_dump(exclude_unset=True)
    users[user_id].update(update_data)
    return users[user_id]


@app.delete("/api/v1/users/{user_id}")
def delete_user(user_id: int):
    """删除用户"""
    if user_id not in users:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    del users[user_id]
    return {"message": f"用户 {user_id} 已删除"}


@app.get("/api/v1/health")
def health():
    """健康检查"""
    return {"status": "ok", "users_count": len(users)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9001)
