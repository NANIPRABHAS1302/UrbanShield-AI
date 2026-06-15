"""Guardian contact management for UrbanShield AI."""

from __future__ import annotations

import re
import uuid
from typing import Any

from .data_store import JsonDataStore

MAX_GUARDIANS = 5


class GuardianManager:
    """Manages up to 5 emergency guardian contacts backed by a JSON file."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def list_guardians(self) -> list[dict[str, Any]]:
        return self.store.read_json("guardian_contacts.json", default=[])

    def add_guardian(self, data: dict[str, Any]) -> dict[str, Any]:
        guardians = self.list_guardians()
        if len(guardians) >= MAX_GUARDIANS:
            raise ValueError(f"Maximum of {MAX_GUARDIANS} guardians allowed")

        errors = self._validate(data)
        if errors:
            raise ValueError("; ".join(errors))

        phone = re.sub(r"[\s\-\(\)]", "", data["phone"].strip())
        # Check for duplicate phone
        for g in guardians:
            if re.sub(r"[\s\-\(\)]", "", g["phone"]) == phone:
                raise ValueError(f"Guardian with phone {data['phone']} already exists")

        guardian = {
            "id": str(uuid.uuid4())[:8],
            "name": data["name"].strip(),
            "relationship": data.get("relationship", "Other").strip(),
            "phone": data["phone"].strip(),
        }
        guardians.append(guardian)
        self.store.write_json("guardian_contacts.json", guardians)
        return guardian

    def delete_guardian(self, guardian_id: str) -> bool:
        guardians = self.list_guardians()
        updated = [g for g in guardians if g["id"] != guardian_id]
        if len(updated) == len(guardians):
            return False
        self.store.write_json("guardian_contacts.json", updated)
        return True

    def _validate(self, data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not data.get("name", "").strip():
            errors.append("Guardian name is required")
        phone = data.get("phone", "").strip()
        if not phone or len(re.sub(r"[\s\-\+\(\)]", "", phone)) < 10:
            errors.append("Valid phone number is required (min 10 digits)")
        return errors
