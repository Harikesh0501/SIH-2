from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import check_db_health
from app.api import auth, profile, competencies, recommendations, assessments, chat, passport, reports, admin

app = FastAPI(
    title="Karmayogi Sankhyiki API",
    description="AI-Enabled Skill Intelligence & Learning Platform for India's Official Statistical System (MoSPI/NSSTA)",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_init():
    """Ensure database schema is created and default data seeded on first run"""
    try:
        from app.core.database import Base, engine, SessionLocal
        from app.models.user import User
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            if user_count == 0:
                print("[Startup] Fresh database detected. Auto-seeding initial data and personas...")
                import seed_database
                seed_database.seed(reset=False)
        except Exception as seed_err:
            print(f"[Startup Seed Error]: {seed_err}")
        finally:
            db.close()
    except Exception as e:
        print(f"[Startup DB Init Error]: {e}")

# Include Routers
app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(competencies.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(assessments.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(passport.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/api/me", tags=["Authentication & SSO"])
def api_me_alias(current_user=Depends(auth.get_current_user)):
    return current_user

@app.get("/api/team/my-subordinates", tags=["Team Matrix"])
def get_team_subordinates(
    current_user=Depends(auth.get_current_user),
    db=Depends(auth.get_db)
):
    """Alias for team matrix subordinates"""
    from app.api.competencies import get_team_matrix
    try:
        matrix = get_team_matrix(division=None, db=db, current_user=current_user)
        return {
            "subordinates": [
                {
                    "id": s.id,
                    "full_name": s.full_name,
                    "designation": s.designation,
                    "cadre": s.cadre,
                    "division": s.division,
                    "readiness_percentage": s.readiness_percentage,
                    "competencies": [
                        {
                            "code": c.code,
                            "name": c.name,
                            "current_level": c.current_level,
                            "target_level": c.required_level
                        }
                        for c in s.competencies
                    ]
                }
                for s in matrix.subordinates
            ]
        }
    except Exception as e:
        return {"subordinates": []}

@app.post("/api/team/calibrate/{officer_id}", tags=["Team Matrix"])
def calibrate_officer(
    officer_id: int,
    data: dict,
    current_user=Depends(auth.get_current_user),
    db=Depends(auth.get_db)
):
    """Alias for supervisor calibrate"""
    from app.models.competency import Competency, UserCompetency
    from datetime import datetime
    code = data.get("competency_code")
    lvl = data.get("new_level", 3)
    comp = db.query(Competency).filter(Competency.code == code).first()
    if comp:
        uc = db.query(UserCompetency).filter(UserCompetency.user_id == officer_id, UserCompetency.competency_id == comp.id).first()
        if uc:
            uc.current_level = lvl
            uc.assessed_via = "SUPERVISOR"
            uc.last_evaluated_at = datetime.utcnow()
        else:
            uc = UserCompetency(user_id=officer_id, competency_id=comp.id, current_level=lvl, assessed_via="SUPERVISOR")
            db.add(uc)
        db.commit()
    return {"success": True, "message": "Rating calibrated"}

@app.get("/api/health", tags=["Health"])
def health_check():
    db_ok = check_db_health()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "ai_engine": "nvidia_nim",
        "nvidia_model": settings.NVIDIA_MODEL,
        "environment": settings.ENVIRONMENT,
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to Karmayogi Sankhyiki API (SIH26101)",
        "documentation": "/docs",
        "health": "/api/health",
    }
