from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.event.router import router as event_router
from app.modules.guest.router import router as guest_router
from app.modules.invitation.router import router as invitation_router
from app.modules.table.router import router as table_router
from app.modules.event_stats.router import router as event_stats_router
from app.modules.finance.router import router as finance_router

app = FastAPI(
    title="WeddingPlanner API",
    version="1.0.0"
)

origins = [str(origin) for origin in settings.ALLOWED_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(event_router)
app.include_router(guest_router)
app.include_router(invitation_router)
app.include_router(table_router)
app.include_router(event_stats_router)
app.include_router(finance_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}