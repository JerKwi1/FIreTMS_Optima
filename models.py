
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class Buyer(BaseModel):
    nip: str
    name: str
    address: str

class Position(BaseModel):
    name: str
    quantity: float
    netPrice: float
    vatRate: str  # '23', '8', '0', 'np.' etc.

class Totals(BaseModel):
    net: float
    vat: float
    gross: float

class FireTMSInvoice(BaseModel):
    id: str
    number: str
    issueDate: str
    currency: str = "PLN"
    buyer: Buyer
    positions: List[Position]
    totals: Totals

    @field_validator("issueDate")
    def validate_date(cls, v):
        # Prosta walidacja formatu YYYY-MM-DD
        if len(v) < 10 or v[4] != "-" or v[7] != "-":
            raise ValueError("issueDate must be YYYY-MM-DD")
        return v

class OptimaContractor(BaseModel):
    taxId: str
    name: str
    address: str

class OptimaItem(BaseModel):
    name: str
    qty: float
    netPrice: float
    vatRate: str

class OptimaTotals(BaseModel):
    net: float
    vat: float
    gross: float

class OptimaInvoice(BaseModel):
    docNo: str
    issueDate: str
    currency: str = "PLN"
    contractor: OptimaContractor
    items: List[OptimaItem]
    totals: OptimaTotals
