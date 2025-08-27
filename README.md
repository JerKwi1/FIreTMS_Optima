
# firetms-optima-sync (ready-to-run)

Produkcyjny, gotowy do testów pakiet integracyjny **fireTMS → Comarch Optima**, napisany w Pythonie.
Zawiera:
- skrypt `sync.py` z asynchroniczną obsługą API (aiohttp), idempotencją i SQLite
- walidację danych (Pydantic)
- mapowanie pól w osobnym module `mapper.py`
- konfigurację przez `.env`
- logowanie (loguru) z rotacją
- **mock serwery** (FastAPI) symulujące API fireTMS i Optimy do bezpiecznych testów
- Dockerfile + docker-compose oraz unit pliki systemd
- testowe dane

> **Uwaga:** Endpointy i modele w mockach są zgodne z przykładową strukturą z `mapper.py`. W produkcji podmień URL-e i ewentualnie dostosuj mapowanie.

---

## Szybki start (tryb testów z mockami)

1. **Wymagania**: Python 3.10+, docker (opcjonalnie).
2. Skopiuj plik `.env.example` do `.env` i zostaw wartości domyślne (mocki).
3. Zainstaluj zależności i uruchom mock serwery:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn tests.mock_server:app --reload --port 8000  # w innym terminalu (mocki)
```

4. Uruchom synchronizację (skrypt będzie działał w pętli, sprawdzając nowe faktury co `POLL_INTERVAL` sekund):

```bash
python sync.py
```

Powinieneś zobaczyć logi „pobrano 25 faktur” i „wysłano do Optimy…”. Dane zapisują się w SQLite (`sync_state.sqlite`).

---

## Uruchomienie w Dockerze (mocki + synchronizacja)

```bash
docker compose up --build
```

- `mock` uruchamia FastAPI pod `http://localhost:8000`
- `sync` startuje kontener z integracją według `.env`

---

## Przejście na produkcję

1. W `.env` ustaw prawdziwe dane połączeń:
```
FIRETMS_URL=https://<twoj-firetms-api>
FIRETMS_TOKEN=...
OPTIMA_DB_HOST=<host-bazy-optimy>
OPTIMA_DB_PORT=3306
OPTIMA_DB_USER=<uzytkownik>
OPTIMA_DB_PASSWORD=<haslo>
OPTIMA_DB_NAME=<nazwa-bazy>
```
2. Zweryfikuj mapowanie w `mapper.py` (stawki VAT, waluty, pola kontrahenta).
3. Zrób test na **firmie testowej** w Optimie.
4. Uruchom integrację jako usługę działającą w tle (np. `systemd` lub kontener Dockera);
   skrypt sam sprawdza nowe faktury co `POLL_INTERVAL` sekund.

---

## Kluczowe zmienne środowiskowe (.env)

```
FIRETMS_URL=http://localhost:8000/firetms
FIRETMS_TOKEN=dev-firetms-token
OPTIMA_DB_HOST=localhost
OPTIMA_DB_PORT=3306
OPTIMA_DB_USER=root
OPTIMA_DB_PASSWORD=
OPTIMA_DB_NAME=optima

# Wydajność i zachowanie
CONCURRENCY=10
BATCH_SIZE=50
REQUEST_TIMEOUT=30
RETRIES=6
POLL_INTERVAL=60

# Znacznik czasu startu (ISO8601, UTC)
SINCE_TS=2025-01-01T00:00:00Z

# Logi
LOG_LEVEL=INFO
LOG_DIR=logs
```

---

## Struktura projektu

```
.
├── README.md
├── sync.py
├── mapper.py
├── models.py
├── config.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── systemd/
│   ├── firetms-optima.service
│   └── firetms-optima.timer
└── tests/
    ├── mock_server.py
    └── data/sample_invoice.json
```

---

## Typowe modyfikacje

- **Mapowanie VAT**: edytuj `mapper.py` → `vat_rate_map`.
- **Idempotencja**: skrypt nie wyśle ponownie faktury o niezmienionej treści (hash payloadu).
- **Dwukierunkowość**: dodaj w `sync.py` funkcję pobierania statusów płatności z Optimy i PATCH do fireTMS (przykład w komentarzu).

Powodzenia! :)
