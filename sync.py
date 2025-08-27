
import os, asyncio, json, time, hashlib, sqlite3
from contextlib import closing
from loguru import logger
import aiohttp

from config import settings
from mapper import map_to_optima

# Przygotowanie logów
os.makedirs(settings.LOG_DIR, exist_ok=True)
logger.add(os.path.join(settings.LOG_DIR, "sync.log"), rotation="10 MB", level=settings.LOG_LEVEL)

DB_PATH = settings.SYNC_DB

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            payload_hash TEXT,
            external_id TEXT,
            status TEXT,
            updated_at REAL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS state (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")
        c.commit()

def get_state(key, default=None):
    with closing(sqlite3.connect(DB_PATH)) as c:
        row = c.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

def set_state(key, value):
    with closing(sqlite3.connect(DB_PATH)) as c:
        c.execute("INSERT OR REPLACE INTO state(key,value) VALUES(?,?)", (key, value))
        c.commit()

def payload_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

async def backoff_sleep(attempt):
    await asyncio.sleep(min(60, 2 ** attempt))

class FireTMS:
    def __init__(self, session): self.s = session
    async def list_invoices(self, since_ts, page=1, page_size=100):
        headers={"Authorization": f"Bearer {settings.FIRETMS_TOKEN}"}
        params={"updatedFrom": since_ts, "page": page, "pageSize": page_size}
        url = f"{settings.FIRETMS_URL}/invoices"
        for attempt in range(settings.RETRIES):
            try:
                async with self.s.get(url, headers=headers, params=params, timeout=settings.REQUEST_TIMEOUT) as r:
                    if r.status in (429, 500, 502, 503, 504):
                        logger.warning(f"FireTMS list_invoices status={r.status}, retry={attempt}")
                        await backoff_sleep(attempt); continue
                    r.raise_for_status()
                    data = await r.json()
                    return data  # {items: [...], nextPage: bool}
            except Exception as e:
                logger.warning(f"FireTMS list_invoices retry {attempt}: {e}")
                await backoff_sleep(attempt)
        raise RuntimeError("FireTMS list_invoices failed")

class Optima:
    def __init__(self, session): self.s = session
    async def upsert_invoice(self, doc):
        headers={"Authorization": f"Bearer {settings.OPTIMA_TOKEN}", "Content-Type":"application/json"}
        url = f"{settings.OPTIMA_URL}/invoices/upsert"
        for attempt in range(settings.RETRIES):
            try:
                async with self.s.post(url, headers=headers, json=doc, timeout=settings.REQUEST_TIMEOUT) as r:
                    if r.status in (429, 500, 502, 503, 504):
                        logger.warning(f"Optima upsert status={r.status}, retry={attempt}")
                        await backoff_sleep(attempt); continue
                    r.raise_for_status()
                    return await r.json()  # {externalId: "..."}
            except Exception as e:
                logger.warning(f"Optima upsert retry {attempt}: {e}")
                await backoff_sleep(attempt)
        raise RuntimeError("Optima upsert failed")

async def process_invoice(sem, optima: Optima, inv: dict):
    async with sem:
        mapped = map_to_optima(inv)
        h = payload_hash(mapped)
        with closing(sqlite3.connect(DB_PATH)) as c:
            row = c.execute("SELECT payload_hash, external_id, status FROM invoices WHERE id=?", (inv["id"],)).fetchone()
            if row and row[0] == h and row[2] == "synced":
                logger.debug(f"Skip unchanged invoice {inv['id']}")
                return  # idempotent
        res = await optima.upsert_invoice(mapped)
        ext_id = res.get("externalId")
        with closing(sqlite3.connect(DB_PATH)) as c:
            c.execute("INSERT OR REPLACE INTO invoices(id,payload_hash,external_id,status,updated_at) VALUES(?,?,?,?,?)",
                      (inv["id"], h, ext_id, "synced", time.time()))
            c.commit()
        logger.info(f"Synced invoice {inv['id']} -> externalId={ext_id}")

async def run_sync():
    init_db()
    since = get_state("since_ts", settings.SINCE_TS)
    sem = asyncio.Semaphore(settings.CONCURRENCY)
    total = 0
    async with aiohttp.ClientSession() as session:
        ft = FireTMS(session)
        op = Optima(session)

        page = 1
        while True:
            batch = await ft.list_invoices(since, page=page, page_size=settings.BATCH_SIZE)
            items = batch.get("items", [])
            if not items:
                break
            await asyncio.gather(*(process_invoice(sem, op, inv) for inv in items))
            total += len(items)
            if not batch.get("nextPage"):
                break
            page += 1

    set_state("since_ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    logger.success(f"Sync finished. Total processed: {total}")

if __name__ == "__main__":
    asyncio.run(run_sync())
