
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
import random, time

app = FastAPI(title="Mock fireTMS & Optima API")

# Pseudo-baza faktur w fireTMS
MOCK_INVOICES: List[Dict] = []

def seed_data():
    global MOCK_INVOICES
    if MOCK_INVOICES:
        return
    for i in range(1, 51):  # 50 faktur testowych
        qty = round(random.uniform(1, 10), 2)
        net = round(qty * 100.0, 2)
        vat = round(net * 0.23, 2)
        gross = round(net + vat, 2)
        inv = {
            "id": f"FTMS-{i:04d}",
            "number": f"FV/{i:04d}/2025",
            "issueDate": "2025-08-01",
            "currency": "PLN",
            "buyer": {
                "nip": "5250001009",
                "name": "ACME Sp. z o.o.",
                "address": "ul. Prosta 1, 00-000 Warszawa"
            },
            "positions": [
                {"name":"Usługa transportowa", "quantity": qty, "netPrice": 100.0, "vatRate": "23"}
            ],
            "totals": {"net": net, "vat": vat, "gross": gross},
            "updatedAt": f"2025-08-01T12:00:00Z"
        }
        MOCK_INVOICES.append(inv)

seed_data()

def verify_token(token: str, provided: Optional[str]):
    if provided != token:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/firetms/invoices")
def list_invoices(
    authorization: Optional[str] = Header(None),
    updatedFrom: Optional[str] = Query(None),
    page: int = 1,
    pageSize: int = 50,
):
    verify_token("Bearer dev-firetms-token", authorization)
    # Prosta stronicacja
    start = (page - 1) * pageSize
    end = start + pageSize
    items = MOCK_INVOICES[start:end]
    nextPage = end < len(MOCK_INVOICES)
    return {"items": items, "nextPage": nextPage}

@app.post("/optima/invoices/upsert")
def upsert_invoice(payload: Dict, authorization: Optional[str] = Header(None)):
    verify_token("Bearer dev-optima-token", authorization)
    # Zwracamy sztuczny externalId
    ext_id = f"OPT-{int(time.time()*1000)}-{random.randint(100,999)}"
    return JSONResponse({"externalId": ext_id})
