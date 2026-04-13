from fastapi import FastAPI

from finalscoring_api.routes.health import router as health_router

app = FastAPI(title="Final Scoring API")


app.include_router(health_router)
