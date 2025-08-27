
from typing import Dict
from models import FireTMSInvoice, OptimaInvoice, OptimaContractor, OptimaItem, OptimaTotals

# Proste mapowanie stawek VAT (dostosuj do Optimy)
vat_rate_map = {
    "23": "23",
    "8": "8",
    "5": "5",
    "0": "0",
    "np.": "NP",
    "zw.": "ZW",
}

def map_to_optima(inv: Dict) -> Dict:
    f = FireTMSInvoice(**inv)  # walidacja wejścia
    items = [
        OptimaItem(
            name=p.name,
            qty=p.quantity,
            netPrice=p.netPrice,
            vatRate=vat_rate_map.get(p.vatRate, p.vatRate),
        )
        for p in f.positions
    ]
    mapped = OptimaInvoice(
        docNo=f.number,
        issueDate=f.issueDate,
        currency=f.currency,
        contractor=OptimaContractor(
            taxId=f.buyer.nip,
            name=f.buyer.name,
            address=f.buyer.address,
        ),
        items=items,
        totals=OptimaTotals(
            net=f.totals.net,
            vat=f.totals.vat,
            gross=f.totals.gross,
        ),
    )
    return mapped.model_dump()
