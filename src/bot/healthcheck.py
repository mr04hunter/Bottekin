from fastapi import FastAPI, Response, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
import asyncpg
import time
from bot.config import config
from typing import Dict, Tuple

DB_URL = config.db_health_url
app = FastAPI()

health_check_counter = Counter(
    'bot_health_checks_total', 
    'Total number of health checks',
    ['status']
)
health_check_duration = Histogram(
    'bot_health_check_duration_seconds',
    'Time spent processing health check'
)
db_connection_status = Gauge(
    'bot_db_connection_status',
    'Database connection status (1=up, 0=down)'
)


bot_commands_total = Counter(
    'bot_commands_total',
    'Total number of commands executed',
    ['command_name', 'status']
)
bot_uptime_seconds = Gauge(
    'bot_uptime_seconds',
    'Bot uptime in seconds'
)



_bearer_scheme = HTTPBearer(auto_error=False)

async def verify_metrics_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme)
) -> None:
    if not credentials or credentials.credentials != config.metrics_secret_token:
        raise HTTPException(status_code=403, detail="Forbidden")



@app.get("/health")
async def health() -> Tuple[Dict[str, str], int]:
    start_time = time.time()
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute("SELECT 1;")
        await conn.close()
        
        db_connection_status.set(1)
        health_check_counter.labels(status='success').inc()
        
        return {"status": "ok"}, 200
    except Exception as e:
        db_connection_status.set(0)
        health_check_counter.labels(status='failure').inc()
        
        return {"status": "db down", "error": str(e)}, 500
    finally:
        health_check_duration.observe(time.time() - start_time)

@app.get("/metrics", dependencies=[Depends(verify_metrics_token)])
async def metrics() -> Response:
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )