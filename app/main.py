"""Entry point of the ShopFlow orders and refunds service."""

import json
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import clock, config
from .routers import admin, customers, orders
from .services.order_service import NotFound
from .services.refund_policy import RefundDenied

app = FastAPI(title="ShopFlow Orders", version=config.app_version())


@app.exception_handler(NotFound)
def handle_not_found(_: Request, exc: NotFound):
    return JSONResponse(
        status_code=404, content={"detail": {"code": "NOT_FOUND", "message": str(exc)}}
    )


@app.exception_handler(RefundDenied)
def handle_refund_denied(_: Request, exc: RefundDenied):
    return JSONResponse(
        status_code=400, content={"detail": {"code": exc.code, "message": exc.message}}
    )


@app.middleware("http")
async def access_log(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    entry = {
        "ts": clock.now().isoformat(),
        "env": config.env_name(),
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "ms": round((time.perf_counter() - started) * 1000, 1),
        "client": request.headers.get("user-agent", "-"),
    }
    line = json.dumps(entry, ensure_ascii=False)
    path = config.log_path()
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    else:
        print(line, file=sys.stdout, flush=True)
    return response


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "version": config.app_version(), "env": config.env_name()}


app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(admin.router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
