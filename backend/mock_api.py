"""Minimal mock API so you can see tests actually pass.

Run: python mock_api.py
Then: curl http://localhost:9000/health
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Mock Petstore")

pets: dict[int, dict] = {
    1: {"id": 1, "name": "Buddy", "status": "available", "photoUrls": [], "tags": []},
    2: {"id": 2, "name": "Kitty", "status": "pending", "photoUrls": [], "tags": []},
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v3/pet/{pet_id}")
def get_pet(pet_id: int):
    if pet_id not in pets:
        raise HTTPException(404, "Not found")
    return pets[pet_id]


@app.get("/api/v3/pet/findByStatus")
def find_by_status(status: str = "available"):
    return [p for p in pets.values() if p["status"] == status]


@app.post("/api/v3/pet")
def create_pet(pet: dict):
    pet_id = max(pets.keys()) + 1 if pets else 1
    pet["id"] = pet_id
    pets[pet_id] = pet
    return pet


@app.put("/api/v3/pet")
def update_pet(pet: dict):
    pid = pet.get("id")
    if pid not in pets:
        raise HTTPException(404, "Not found")
    pets[pid] = pet
    return pet


@app.delete("/api/v3/pet/{pet_id}")
def delete_pet(pet_id: int):
    if pet_id not in pets:
        raise HTTPException(404, "Not found")
    del pets[pet_id]
    return {"message": "Deleted"}


@app.get("/api/v3/store/inventory")
def inventory():
    return {"available": 10, "pending": 5, "sold": 3}


@app.post("/api/v3/store/order")
def place_order(order: dict):
    return order


@app.get("/api/v3/store/order/{order_id}")
def get_order(order_id: int):
    return {"id": order_id, "status": "approved"}


@app.delete("/api/v3/store/order/{order_id}")
def delete_order(order_id: int):
    return {"message": "Deleted"}


@app.post("/api/v3/user")
def create_user(user: dict):
    return user


@app.get("/api/v3/user/{username}")
def get_user(username: str):
    return {"username": username, "email": f"{username}@test.com"}


@app.get("/api/v3/user/login")
def login(username: str = "", password: str = ""):
    return f"logged in as {username}"


@app.get("/api/v3/user/logout")
def logout():
    return "logged out"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
