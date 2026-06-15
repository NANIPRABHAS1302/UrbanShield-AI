# UrbanShield AI — Competitive Feature Matrix

This matrix compares UrbanShield AI's predictive, multi-modal capabilities against traditional navigation tools and standard personal safety alert apps.

---

## Capabilities Comparison

| Capability | UrbanShield AI | Traditional Maps (Google / Apple Maps) | Standard Safety Apps (SOS/GPS Trackers) |
| :--- | :---: | :---: | :---: |
| **Pathfinding Core** | GNN multi-objective shortest path | Dijkstra/A* (Time/Traffic-only) | No pathfinding (Static alerts/GPS logs) |
| **CCTV CV Integration** | Simulated CNN anomaly scoring & camera health checks | None | None |
| **Dynamic Patrol Mitigation** | Multi-Agent Reinforcement Learning (MARL) simulation | None | None |
| **Women Safety Mode** | Penalizes low-lighting streets, prioritizes Help Points | None | Static geo-sharing only |
| **Community Incident Logs** | Citizen-sourced, safety-model validated logs | Traffic/Accidents only | Simple panic text messages |
| **Interactive Overlays** | Safe, Danger, Congestion, and Emergency Coverage maps | Traffic & simple satellite layers | Simple tracking dots on map |
| **Guardian Deviance Alarm** | Real-time GPS deviance trigger alerts | None | Static geo-fence boundaries |
| **Database Architecture** | Flat JSON-backed stores (hackathon/demo friendly) | High-scale relational databases | Cloud SaaS databases |

---

## Module Breakdown in UrbanShield AI

### 1. Route Optimization Preference (GNN Graph)
* **Safest Path**: Strict safety weight multipliers. Fully bypasses low-lit alleys (lighting < 0.6) and high-crime sectors (crime_index > 0.6) even if travel time increases by 2.5x.
* **Balanced Path**: Compromise routing. Weighs edge safety score against travel duration in a 65:35 ratio.
* **Fastest Path**: Prioritizes transit speed, but continues to factor minor safety adjustments to avoid extremely critical zones.

### 2. Women Safety Checklist Elements
* **Street Lighting Index**: Graph path weights penalize poorly illuminated links.
* **Emergency Dispatch Proximity**: Paths are guided to route within 500m of police stations or active Help Points.
* **Deviance Timeline Alerts**: Live script triggers deviation overlays if GPS veers away from safety vectors.
* **Primary Contacts Priority**: Escalate broadcast dispatches selectively based on verified contact categories (police, emergency, guardian).
