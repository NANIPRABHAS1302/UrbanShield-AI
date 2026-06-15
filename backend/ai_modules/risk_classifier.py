"""Risk classification and explanation helpers."""

from __future__ import annotations

from typing import Any

from ..utils import clamp


class RiskClassifier:
    """Combines model signals into a user-facing risk band."""

    def combine(self, signals: dict[str, float], weights: dict[str, float]) -> dict[str, Any]:
        weighted_sum = 0.0
        used_weight = 0.0
        for key, value in signals.items():
            weight = float(weights.get(key, 0.0))
            weighted_sum += clamp(value) * weight
            used_weight += weight

        score = clamp(weighted_sum / used_weight if used_weight else 0.0)
        classification = self.classify(score)
        classification["score"] = round(score, 3)
        classification["signals"] = {key: round(clamp(value), 3) for key, value in signals.items()}
        classification["confidence"] = round(clamp(0.68 + len(signals) * 0.04, 0.68, 0.92), 2)
        return classification

    def classify(self, score: float) -> dict[str, Any]:
        score = clamp(score)
        if score >= 0.75:
            return {
                "level": "CRITICAL",
                "label": "Critical Risk",
                "color": "#b42318",
                "action": "Avoid this route and trigger SOS if you are already there.",
            }
        if score >= 0.55:
            return {
                "level": "HIGH",
                "label": "High Risk",
                "color": "#d92d20",
                "action": "Use an alternate route or travel with support.",
            }
        if score >= 0.32:
            return {
                "level": "MODERATE",
                "label": "Moderate Risk",
                "color": "#b54708",
                "action": "Proceed with caution and stay on recommended roads.",
            }
        return {
            "level": "LOW",
            "label": "Low Risk",
            "color": "#027a48",
            "action": "Route is currently acceptable for normal travel.",
        }
