import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import Product, Order, Wishlist, PromoCode, BlogPost, Event, Newsletter, RecommendationFeedback

app = FastAPI(title="Pikalba API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"name": "Pikalba", "status": "ok"}

# --------- Catalog Endpoints ---------

@app.get("/api/products", response_model=List[Product])
def list_products(category: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    filter_dict = {"active": True}
    if category:
        filter_dict["category"] = category
    if q:
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]
    try:
        docs = get_documents("product", filter_dict, limit)
        # coerce to Product-serializable
        for d in docs:
            d.pop("_id", None)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products", status_code=201)
def create_product(product: Product):
    try:
        _id = create_document("product", product)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------- Orders & Payments (PayPal placeholder) ---------

class CreateOrderRequest(BaseModel):
    order: Order
    promo_code: Optional[str] = None

@app.post("/api/orders", status_code=201)
def create_order(req: CreateOrderRequest):
    order = req.order.model_dump()
    # Apply promo code if exists
    if req.promo_code:
        promos = get_documents("promocode", {"code": req.promo_code, "active": True}, 1)
        if promos:
            promo = promos[0]
            percent = promo.get("percent_off")
            amount = promo.get("amount_off")
            if percent:
                order["discount"] = order.get("discount", 0) + round(order["subtotal"] * percent / 100, 2)
            if amount:
                order["discount"] = order.get("discount", 0) + amount
            order["total"] = max(0, round(order["subtotal"] + order["shipping_cost"] - order.get("discount", 0), 2))
    _id = create_document("order", order)
    # For MVP, simulate PayPal by returning a fake order id
    paypal_order_id = f"SIM-PAYPAL-{_id}"
    return {"id": _id, "paypal_order_id": paypal_order_id}

@app.get("/api/orders/track/{order_id}")
def track_order(order_id: str):
    docs = get_documents("order", {"_id": {"$regex": order_id}}, 1)
    if not docs:
        raise HTTPException(status_code=404, detail="Order not found")
    doc = docs[0]
    doc.pop("_id", None)
    return doc

# --------- Wishlist ---------

@app.post("/api/wishlist")
def save_wishlist(w: Wishlist):
    _id = create_document("wishlist", w)
    return {"id": _id}

# --------- Marketing ---------

@app.post("/api/newsletter")
def subscribe_newsletter(n: Newsletter):
    _id = create_document("newsletter", n)
    return {"id": _id}

# --------- Blog & Events ---------

@app.get("/api/blog", response_model=List[BlogPost])
def list_blog(limit: int = 20):
    docs = get_documents("blogpost", {"published": True}, limit)
    for d in docs:
        d.pop("_id", None)
    return docs

@app.post("/api/blog")
def create_blog(p: BlogPost):
    _id = create_document("blogpost", p)
    return {"id": _id}

@app.get("/api/events", response_model=List[Event])
def list_events(limit: int = 50):
    docs = get_documents("event", {}, limit)
    for d in docs:
        d.pop("_id", None)
    return docs

@app.post("/api/events")
def create_event(e: Event):
    _id = create_document("event", e)
    return {"id": _id}

# --------- AI Recommendations (simple content-based MVP) ---------

@app.get("/api/recommendations/{sku}")
def recommend_for_sku(sku: str, limit: int = 8):
    # Use shared tags/brand/category for simple recommendations
    prod_docs = get_documents("product", {"sku": sku}, 1)
    if not prod_docs:
        raise HTTPException(status_code=404, detail="Product not found")
    p = prod_docs[0]
    tags = p.get("tags", [])
    brand = p.get("brand")
    category = p.get("category")
    query = {"active": True, "sku": {"$ne": sku}, "$or": []}
    if tags:
        query["$or"].append({"tags": {"$in": tags}})
    if brand:
        query["$or"].append({"brand": brand})
    if category:
        query["$or"].append({"category": category})
    if not query["$or"]:
        query.pop("$or")
    recs = get_documents("product", query, limit)
    for r in recs:
        r.pop("_id", None)
    return {"items": recs}

@app.post("/api/recommendations/feedback")
def recommendation_feedback(f: RecommendationFeedback):
    _id = create_document("recommendationfeedback", f)
    return {"id": _id}

# --------- Health & Schema Info ---------

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
