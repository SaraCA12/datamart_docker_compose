from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import json
import os

app = FastAPI(
    title="DataMart Product Catalog API",
    description="API interna del catálogo de productos de DataMart S.A.S.",
    version="1.0.0",
)

class Product(BaseModel):
    code: str
    name: str
    category: str
    supplier_country: str
    is_active: bool

class ProductListResponse(BaseModel):
    total: int
    page: int
    size: int
    pages: int
    items: List[Product]

CATALOG_PATH = os.getenv("CATALOG_PATH", "/app/catalog.json")

def load_catalog() -> dict:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/health")
def health():
    return {"status": "ok", "service": "product-catalog-api"}

@app.get("/products", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None),
    active_only: bool = Query(False),
):
    catalog = load_catalog()
    products = list(catalog.values())
    if category:
        products = [p for p in products if p["category"].lower() == category.lower()]
    if active_only:
        products = [p for p in products if p["is_active"]]
    total = len(products)
    pages = max(1, (total + size - 1) // size)
    start = (page - 1) * size
    return ProductListResponse(
        total=total, page=page, size=size, pages=pages,
        items=[Product(**p) for p in products[start:start+size]],
    )

@app.get("/products/{code}", response_model=Product)
def get_product(code: str):
    catalog = load_catalog()
    code_normalized = code.upper().strip()
    if code_normalized not in catalog:
        raise HTTPException(status_code=404, detail=f"Producto '{code}' no encontrado.")
    return Product(**catalog[code_normalized])
