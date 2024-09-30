from fastapi import FastAPI, HTTPException
from typing import Optional
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI(title="Shop API")


class Item(BaseModel):
    id: int
    name: str
    price: float
    deleted: bool = False


class CartItem(BaseModel):
    id: int
    name: str
    quantity: int
    available: bool = True


class Cart(BaseModel):
    id: int
    items: list[CartItem] = []
    price: float = 0.0


items_db: dict[int, Item] = {}
carts_db: dict[int, Cart] = {}


def calculate_cart_total(cart: Cart):
    print(cart)
    return sum(
        item.quantity * items_db[item.id].price for item in cart.items if item.available
    )


@app.post("/cart", response_model=int)
def create_cart():
    cart_id = uuid4().int
    carts_db[cart_id] = Cart(id=cart_id)
    return cart_id


@app.get("/cart/{cart_id}", response_model=Cart)
def get_cart(cart_id: int):
    cart = carts_db.get(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


@app.get("/cart", response_model=list[Cart])
def list_carts(
        offset: int = 0,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_quantity: Optional[int] = None,
        max_quantity: Optional[int] = None,
):
    filtered_carts = []
    for cart in carts_db.values():
        total_price = calculate_cart_total(cart)
        total_quantity = sum(item.quantity for item in cart.items if item.available)
        if (
                (min_price is not None and total_price < min_price)
                or (max_price is not None and total_price > max_price)
                or (min_quantity is not None and total_quantity < min_quantity)
                or (max_quantity is not None and total_quantity > max_quantity)
        ):
            continue
        filtered_carts.append(cart)

    return filtered_carts[offset: offset + limit]


@app.post("/cart/{cart_id}/add/{item_id}")
def add_item_to_cart(cart_id: int, item_id: int):
    cart = carts_db.get(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")

    item_in_cart = next((item for item in cart.items if item.id == item_id), None)
    if item_in_cart:
        item_in_cart.quantity += 1
    else:
        item = items_db[item_id]
        cart.items.append(
            CartItem(id=item_id, name=item.name, quantity=1, available=not item.deleted)
        )

    cart.price = calculate_cart_total(cart)
    return {"message": "Item added to cart"}


@app.post("/item", response_model=int)
def add_item(item: Item):
    if item.id in items_db:
        raise HTTPException(status_code=400, detail="Item with this ID already exists")
    items_db[item.id] = item
    return item.id


@app.get("/item/{item_id}", response_model=Item)
def get_item(item_id: int):
    item = items_db.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.get("/item", response_model=list[Item])
def list_items(
        offset: int = 0,
        limit: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        show_deleted: bool = False,
):
    filtered_items = []
    for item in items_db.values():
        if (
                (min_price is not None and item.price < min_price)
                or (max_price is not None and item.price > max_price)
                or (not show_deleted and item.deleted)
        ):
            continue
        filtered_items.append(item)
    return filtered_items[offset: offset + limit]


@app.put("/item/{item_id}")
def replace_item(item_id: int, item: Item):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id] = item
    return {"message": "Item replaced"}


@app.patch("/item/{item_id}")
def update_item(item_id: int, item: Item):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    current_item = items_db[item_id]
    if item.name:
        current_item.name = item.name
    if item.price is not None:
        current_item.price = item.price
    return {"message": "Item updated"}


@app.delete("/item/{item_id}")
def delete_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    items_db[item_id].deleted = True
    return {"message": "Item marked as deleted"}