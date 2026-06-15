"""FastAPI entry point for UrbanShield AI."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .safety_engine import SafetyEngine
from .profile_manager import ProfileManager
from .guardian_manager import GuardianManager
from .checkin_system import SafetyCommandCenter

# Structured Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("urbanshield")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title="UrbanShield AI",
    version="1.0.0",
    description="Predictive safety intelligence platform for urban mobility.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_and_handle_errors(request: Request, call_next):
    logger.info(f"Incoming: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Outgoing status: {response.status_code}")
        return response
    except Exception as exc:
        logger.error(f"Error handling request: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal safety engine error occurred."}
        )

engine = SafetyEngine()
profile_mgr = ProfileManager(engine.store)
guardian_mgr = GuardianManager(engine.store)
command_center = SafetyCommandCenter(engine.store)


class RouteAnalysisRequest(BaseModel):
    start_zone: str = Field(default="central_station")
    end_zone: str = Field(default="tech_park")
    departure_time: Optional[datetime] = None
    women_mode: bool = False
    route_preference: Literal["safest", "balanced", "fastest"] = "safest"


class IncidentRequest(BaseModel):
    zone_id: str
    incident_type: str = "suspicious_activity"
    description: str = ""
    severity: Literal["low", "medium", "high", "critical"] = "medium"


class SOSRequest(BaseModel):
    zone_id: str
    user_name: str = "UrbanShield User"
    message: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    risk_level: str = "UNKNOWN"
    women_mode: bool = False
    sos_category: Optional[str] = "unsafe_area"


class ContactRequest(BaseModel):
    id: str
    name: str
    phone: str
    type: str = "emergency"
    priority: int = 2


class ProfileRequest(BaseModel):
    name: str
    email: str
    phone: str
    gender: str = "prefer_not_to_say"
    home_location: str = ""
    work_location: str = ""
    blood_group: str = ""


class GuardianRequest(BaseModel):
    name: str
    relationship: str = "Other"
    phone: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "UrbanShield AI"}


@app.get("/api/zones")
def zones() -> dict[str, object]:
    return {"zones": engine.zones(), "options": engine.zone_options()}


@app.get("/api/dashboard")
def dashboard() -> dict[str, object]:
    return engine.dashboard()


@app.get("/api/danger-zones")
def danger_zones(departure_time: Optional[datetime] = None) -> dict[str, object]:
    return {"danger_zones": engine.danger_zones(departure_time)}


@app.post("/api/analyze-route")
def analyze_route(payload: RouteAnalysisRequest) -> dict[str, object]:
    try:
        return engine.analyze_route(
            start_zone=payload.start_zone,
            end_zone=payload.end_zone,
            departure_time=payload.departure_time,
            women_mode=payload.women_mode,
            route_preference=payload.route_preference,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/incidents")
def incidents() -> dict[str, object]:
    return {"incidents": engine.incidents.list_incidents()}


@app.post("/api/incidents")
def report_incident(payload: IncidentRequest) -> dict[str, object]:
    try:
        return {"incident": engine.report_incident(payload.dict())}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/sos")
def sos_events() -> dict[str, object]:
    return {"events": engine.sos.recent_events()}


@app.post("/api/sos")
def trigger_sos(payload: SOSRequest) -> dict[str, object]:
    try:
        return {"sos_event": engine.trigger_sos(payload.dict())}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/guardian")
def get_guardian_status() -> dict[str, object]:
    contacts = engine.store.read_json("emergency_contacts.json", default=[])
    return {
        "guardian_sharing_enabled": True,
        "active_trip": {
            "start_zone": "central_station",
            "end_zone": "tech_park",
            "status": "active"
        },
        "emergency_contacts": contacts
    }


@app.get("/api/routes")
def get_routes() -> dict[str, object]:
    return engine.store.read_json("routes.json", default={"edges": []})


@app.post("/api/guardian/contacts")
def add_guardian_contact(payload: ContactRequest) -> dict[str, object]:
    contacts = engine.store.read_json("emergency_contacts.json", default=[])
    for c in contacts:
        if c.get("id") == payload.id:
            raise HTTPException(status_code=400, detail="Contact with this ID already exists.")
    
    new_contact = payload.dict()
    contacts.append(new_contact)
    engine.store.write_json("emergency_contacts.json", contacts)
    return {"status": "success", "contact": new_contact}


@app.delete("/api/guardian/contacts/{contact_id}")
def delete_guardian_contact(contact_id: str) -> dict[str, object]:
    contacts = engine.store.read_json("emergency_contacts.json", default=[])
    filtered = [c for c in contacts if c.get("id") != contact_id]
    if len(filtered) == len(contacts):
        raise HTTPException(status_code=404, detail="Contact not found.")
    
    engine.store.write_json("emergency_contacts.json", filtered)
    return {"status": "success", "message": "Contact deleted successfully."}


@app.get("/api/safety-trends")
def get_safety_trends() -> dict[str, object]:
    zones = engine.zones()
    cctv = engine.store.read_json("simulated/mock_cctv_feed.json", default={})
    time_weights = engine.store.read_json("time_risk_weights.json", default={})
    trends = []
    for zone in zones:
        zone_id = zone["id"]
        camera = cctv.get(zone_id, {})
        trends.append({
            "zone_id": zone_id,
            "zone_name": zone["name"],
            "base_risk": round(zone.get("crime_index", 0.3) * 0.6 + (1 - zone.get("lighting_score", 0.7)) * 0.4, 2),
            "cctv_coverage": zone.get("cctv_coverage", 0.5),
            "police_eta_min": zone.get("police_eta_min", 10),
            "anomaly_score": camera.get("anomaly_score", 0.2)
        })
    return {
        "trends": trends,
        "time_weights": time_weights
    }


# --- Profile Endpoints ---

@app.get("/api/profile")
def get_profile() -> dict[str, object]:
    return {"profile": profile_mgr.get_profile()}


@app.post("/api/profile")
def save_profile(payload: ProfileRequest) -> dict[str, object]:
    try:
        return {"profile": profile_mgr.save_profile(payload.dict())}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# --- Guardian Endpoints (new system) ---

@app.get("/api/guardians")
def list_guardians() -> dict[str, object]:
    return {"guardians": guardian_mgr.list_guardians(), "max": 5}


@app.post("/api/guardians")
def add_guardian(payload: GuardianRequest) -> dict[str, object]:
    try:
        return {"guardian": guardian_mgr.add_guardian(payload.dict())}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/guardians/{guardian_id}")
def remove_guardian(guardian_id: str) -> dict[str, object]:
    if not guardian_mgr.delete_guardian(guardian_id):
        raise HTTPException(status_code=404, detail="Guardian not found.")
    return {"status": "success", "message": "Guardian removed."}


# --- Command Center ---

@app.get("/api/command-center")
def get_command_center() -> dict[str, object]:
    return {"status": command_center.get_status()}


# --- Mobility Services ---

@app.get("/api/mobility")
def get_mobility() -> dict[str, object]:
    metro = engine.store.read_json("metro_stations.json", default={"stations": []})
    bus = engine.store.read_json("bus_stops.json", default={"stops": []})
    cab = engine.store.read_json("cab_services.json", default={"zones": {}})
    return {
        "metro_stations": metro.get("stations", []),
        "bus_stops": bus.get("stops", []),
        "cab_services": cab.get("zones", {}),
    }


# --- Emergency Services ---

@app.get("/api/emergency-services")
def get_emergency_services() -> dict[str, object]:
    police = engine.store.read_json("police_stations.json", default={"stations": []})
    hospitals = engine.store.read_json("hospitals.json", default={"hospitals": []})
    return {
        "police_stations": police.get("stations", []),
        "hospitals": hospitals.get("hospitals", []),
        "helplines": {
            "police": "100",
            "emergency": "112",
            "women_helpline": "1091",
            "ambulance": "108",
            "fire": "101",
            "child_helpline": "1098",
        },
    }


# Static frontend is mounted last so /api routes continue to take precedence.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
