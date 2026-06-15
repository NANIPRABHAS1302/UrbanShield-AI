"""User profile management for UrbanShield AI."""

from __future__ import annotations

import re
from typing import Any

from .data_store import JsonDataStore

VALID_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
VALID_GENDERS = {"male", "female", "non-binary", "prefer_not_to_say"}


class ProfileManager:
    """Handles single-user profile CRUD backed by a JSON file."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def get_profile(self) -> dict[str, Any]:
        return self.store.read_json("user_profiles.json", default={})

    def save_profile(self, data: dict[str, Any]) -> dict[str, Any]:
        errors = self._validate(data)
        if errors:
            raise ValueError("; ".join(errors))

        profile = {
            "name": data["name"].strip(),
            "email": data["email"].strip().lower(),
            "phone": data["phone"].strip(),
            "gender": data.get("gender", "prefer_not_to_say").lower(),
            "home_location": data.get("home_location", "").strip(),
            "work_location": data.get("work_location", "").strip(),
            "blood_group": data.get("blood_group", "").upper(),
        }
        self.store.write_json("user_profiles.json", profile)
        return profile

    def _validate(self, data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not data.get("name", "").strip():
            errors.append("Name is required")
        email = data.get("email", "").strip()
        if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append("Valid email is required")
        phone = data.get("phone", "").strip()
        if not phone or len(re.sub(r"[\s\-\+\(\)]", "", phone)) < 10:
            errors.append("Valid phone number is required (min 10 digits)")
        gender = data.get("gender", "").lower()
        if gender and gender not in VALID_GENDERS:
            errors.append(f"Gender must be one of: {', '.join(sorted(VALID_GENDERS))}")
        blood = data.get("blood_group", "").upper()
        if blood and blood not in VALID_BLOOD_GROUPS:
            errors.append(f"Blood group must be one of: {', '.join(sorted(VALID_BLOOD_GROUPS))}")
        return errors
