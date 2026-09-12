import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .config import FRONTEND_DIR, APP_NAME, APP_VERSION, API_PREFIX
from .database import init_db, query_all
from .seed_data import seed_database, seed_enhancements_if_needed

# Import routers
from .routers.auth_router import router as auth_router
from .routers.patient_router import router as patient_router
from .routers.doctor_router import router as doctor_router
from .routers.admin_router import router as admin_router
from .routers.appointment_router import router as appointment_router
from .routers.chatbot_router import router as chatbot_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize tables and seed realistic healthcare data
    init_db()
    seed_database()
    try:
        seed_enhancements_if_needed()
    except Exception as e:
        print(f"Error seeding enhancements: {e}")
    yield
    # Shutdown

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="CareAura Health OS — Indian Hospital Resource & Doctor Availability Optimization Platform",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^https?://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(patient_router, prefix=API_PREFIX)
app.include_router(doctor_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(appointment_router, prefix=API_PREFIX)
app.include_router(chatbot_router, prefix=API_PREFIX)

@app.get(f"{API_PREFIX}/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "environment": "production"
    }

@app.get(f"{API_PREFIX}/search", tags=["Global Search"])
def global_search(q: str = "", city: str = ""):
    term = f"%{q.strip().lower()}%" if q.strip() else "%"
    city_term = f"%{city.strip().lower()}%" if city.strip() else "%"

    doctors = query_all("""
        SELECT d.id, d.specialization, d.experience_years, d.consultation_fee,
               d.hospital_name, d.city, d.languages,
               u.full_name, u.avatar_url, dep.name as department_name
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        JOIN departments dep ON d.department_id = dep.id
        WHERE u.is_active = 1
          AND (LOWER(u.full_name) LIKE ? OR LOWER(d.specialization) LIKE ? OR LOWER(dep.name) LIKE ? OR LOWER(d.languages) LIKE ?)
          AND LOWER(COALESCE(d.city, '')) LIKE ?
        ORDER BY d.experience_years DESC
        LIMIT 10
    """, (term, term, term, term, city_term))

    hospitals = query_all("""
        SELECT id, name, city, locality, address, contact_phone as phone, starting_fee as consultation_base_fee, opening_hours
        FROM hospitals
        WHERE (LOWER(name) LIKE ? OR LOWER(locality) LIKE ? OR LOWER(city) LIKE ?)
          AND LOWER(city) LIKE ?
        ORDER BY id ASC
        LIMIT 8
    """, (term, term, term, city_term))

    departments = query_all("""
        SELECT id, name, code, description, floor_location, contact_extension
        FROM departments
        WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?
        LIMIT 8
    """, (term, term))

    return {
        "query": q,
        "city": city,
        "doctors": doctors,
        "hospitals": hospitals,
        "departments": departments
    }


# Mount static frontend directories
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    # Fallback to index.html for client-side routing
    @app.get("/{catchall:path}")
    def serve_spa(catchall: str):
        if catchall.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
        # Check if static file exists
        static_file = FRONTEND_DIR / catchall
        if static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
