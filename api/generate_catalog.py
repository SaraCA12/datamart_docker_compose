import json
import os
import pandas as pd
from collections import Counter

DATA_PATH    = os.getenv("DATA_PATH", "/app/data")
CATALOG_PATH = os.getenv("CATALOG_PATH", "/app/catalog.json")

CATEGORY_KEYWORDS = {
    "Electronica": ["LIGHT", "LAMP", "BULB", "BATTERY", "WIRE", "CABLE", "CLOCK", "TIMER"],
    "Hogar":       ["CANDLE", "HOLDER", "CUSHION", "FRAME", "MIRROR", "VASE", "BASKET",
                    "BOX", "STORAGE", "HOOK", "HANGER", "MAT", "BOTTLE", "JAR", "TIN"],
    "Cocina":      ["CUP", "MUG", "BOWL", "PLATE", "GLASS", "SPOON", "FORK", "KNIFE",
                    "TRAY", "CAKE", "BAKING", "KITCHEN", "PAN", "POT"],
    "Ropa":        ["BAG", "PURSE", "WALLET", "SCARF", "HAT", "GLOVE", "APRON", "WRAP"],
    "Deportes":    ["BALL", "SPORT", "FITNESS", "SWIM", "GOLF", "TENNIS"],
    "Papeleria":   ["PEN", "PENCIL", "PAPER", "CARD", "NOTE", "BOOK", "DIARY",
                    "RULER", "STAMP", "STICKER", "TAG", "LABEL"],
    "Fiesta":      ["PARTY", "CHRISTMAS", "BIRTHDAY", "WEDDING", "BALLOON", "BANNER",
                    "RIBBON", "DECORATION", "ADVENT", "EASTER", "HALLOWEEN"],
    "Juguetes":    ["TOY", "DOLL", "PUPPET", "PUZZLE", "PLAY"],
}

def infer_category(name: str) -> str:
    name_upper = str(name).upper()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in name_upper for kw in keywords):
            return cat
    return "Varios"

def generate_catalog():
    print("Generando catalogo de productos...")
    dfs = []
    f1 = os.path.join(DATA_PATH, "data.csv")
    if os.path.exists(f1):
        df1 = pd.read_csv(f1, encoding="latin-1", dtype=str, low_memory=False)
        df1 = df1.rename(columns={"StockCode": "code", "Description": "name", "InvoiceDate": "date"})
        df1["date"] = pd.to_datetime(df1["date"], errors="coerce")
        dfs.append(df1[["code", "name", "date"]])
    f2 = os.path.join(DATA_PATH, "online_retail_II.csv")
    if os.path.exists(f2):
        df2 = pd.read_csv(f2, dtype=str, low_memory=False)
        df2 = df2.rename(columns={"StockCode": "code", "Description": "name", "InvoiceDate": "date"})
        df2["date"] = pd.to_datetime(df2["date"], errors="coerce")
        dfs.append(df2[["code", "name", "date"]])
    if not dfs:
        json.dump({}, open(CATALOG_PATH, "w"))
        return
    df = pd.concat(dfs, ignore_index=True)
    df["code"] = df["code"].astype(str).str.upper().str.strip()
    df["name"] = df["name"].astype(str).str.strip()
    df = df[df["code"].notna() & (df["code"] != "") & (df["code"] != "NAN")]
    max_date = df["date"].max()
    cutoff = max_date - pd.Timedelta(days=180)
    active_codes = set(df[df["date"] >= cutoff]["code"].unique())
    catalog = {}
    for code, group in df.groupby("code"):
        names = group["name"].dropna().tolist()
        if not names:
            continue
        canonical_name = Counter(names).most_common(1)[0][0]
        catalog[code] = {
            "code": code,
            "name": canonical_name,
            "category": infer_category(canonical_name),
            "supplier_country": "United Kingdom",
            "is_active": code in active_codes,
        }
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Catalogo generado: {len(catalog):,} productos")

if __name__ == "__main__":
    generate_catalog()
