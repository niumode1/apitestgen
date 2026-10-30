"""演示 API — 书店管理系统，支持增删改查、搜索、统计

启动: python demo_api_full.py
文档: http://localhost:9002/docs
OpenAPI: http://localhost:9002/openapi.json
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

app = FastAPI(title="BookStore API", description="在线书店管理系统演示", version="2.0.0")

# 内存数据库
books = [
    {"id": 1, "title": "Python编程从入门到实践", "author": "Eric Matthes", "price": 89.0, "category": "技术", "stock": 50, "published": "2023-01-15"},
    {"id": 2, "title": "深入理解计算机系统", "author": "Randal Bryant", "price": 139.0, "category": "技术", "stock": 30, "published": "2022-06-01"},
    {"id": 3, "title": "百年孤独", "author": "加西亚·马尔克斯", "price": 55.0, "category": "文学", "stock": 100, "published": "2017-05-20"},
    {"id": 4, "title": "人类简史", "author": "尤瓦尔·赫拉利", "price": 68.0, "category": "社科", "stock": 80, "published": "2014-11-01"},
    {"id": 5, "title": "算法导论", "author": "Thomas Cormen", "price": 128.0, "category": "技术", "stock": 20, "published": "2023-04-10"},
]
_next_book_id = 6
orders = []
_next_order_id = 1


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, le=99999)
    category: str = Field(..., min_length=1, max_length=50)
    stock: int = Field(default=0, ge=0, le=99999)

class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    author: Optional[str] = Field(default=None, min_length=1, max_length=100)
    price: Optional[float] = Field(default=None, gt=0, le=99999)
    category: Optional[str] = Field(default=None)
    stock: Optional[int] = Field(default=None, ge=0)

class OrderCreate(BaseModel):
    book_id: int
    quantity: int = Field(default=1, ge=1, le=100)
    customer: str = Field(..., min_length=1, max_length=100)


# ── 书籍接口 ──
@app.get("/api/v2/books")
def list_books(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
):
    result = books[:]
    if category: result = [b for b in result if b["category"] == category]
    if search: result = [b for b in result if search.lower() in b["title"].lower() or search.lower() in b["author"].lower()]
    if min_price is not None: result = [b for b in result if b["price"] >= min_price]
    if max_price is not None and max_price > 0: result = [b for b in result if b["price"] <= max_price]
    total = len(result)
    start = (page - 1) * page_size
    return {"items": result[start:start + page_size], "total": total, "page": page, "page_size": page_size}

@app.get("/api/v2/books/{book_id}")
def get_book(book_id: int):
    for b in books:
        if b["id"] == book_id: return b
    raise HTTPException(404, f"Book {book_id} not found")

@app.post("/api/v2/books", status_code=201)
def create_book(book: BookCreate):
    global _next_book_id
    new_book = book.model_dump()
    new_book["id"] = _next_book_id
    _next_book_id += 1
    books.append(new_book)
    return new_book

@app.put("/api/v2/books/{book_id}")
def update_book(book_id: int, data: BookUpdate):
    for b in books:
        if b["id"] == book_id:
            for k, v in data.model_dump(exclude_unset=True).items():
                b[k] = v
            return b
    raise HTTPException(404, f"Book {book_id} not found")

@app.delete("/api/v2/books/{book_id}")
def delete_book(book_id: int):
    for i, b in enumerate(books):
        if b["id"] == book_id:
            del books[i]
            return {"message": f"Book {book_id} deleted"}
    raise HTTPException(404, f"Book {book_id} not found")

# ── 订单接口 ──
@app.get("/api/v2/orders")
def list_orders(page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100)):
    total = len(orders)
    start = (page - 1) * page_size
    return {"items": orders[::-1][start:start+page_size], "total": total, "page": page, "page_size": page_size}

@app.post("/api/v2/orders", status_code=201)
def create_order(order: OrderCreate):
    global _next_order_id
    # 检查库存
    book = next((b for b in books if b["id"] == order.book_id), None)
    if not book: raise HTTPException(404, f"Book {order.book_id} not found")
    if book["stock"] < order.quantity: raise HTTPException(400, "Insufficient stock")
    book["stock"] -= order.quantity
    new_order = order.model_dump()
    new_order["id"] = _next_order_id
    new_order["status"] = "pending"
    new_order["created_at"] = datetime.utcnow().isoformat()
    _next_order_id += 1
    orders.append(new_order)
    return new_order

@app.get("/api/v2/orders/{order_id}")
def get_order(order_id: int):
    for o in orders:
        if o["id"] == order_id: return o
    raise HTTPException(404, f"Order {order_id} not found")

# ── 统计接口 ──
@app.get("/api/v2/stats")
def stats():
    categories = {}
    total_stock = 0
    for b in books:
        categories[b["category"]] = categories.get(b["category"], 0) + 1
        total_stock += b["stock"]
    return {
        "total_books": len(books),
        "total_orders": len(orders),
        "total_stock": total_stock,
        "by_category": categories,
        "avg_price": round(sum(b["price"] for b in books) / len(books), 2) if books else 0,
    }

@app.get("/api/v2/health")
def health():
    return {"status": "ok", "service": "BookStore API", "books_count": len(books), "orders_count": len(orders)}

@app.get("/api/v2/categories")
def categories():
    cats = list(set(b["category"] for b in books))
    return {"categories": cats, "total": len(cats)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9002)
