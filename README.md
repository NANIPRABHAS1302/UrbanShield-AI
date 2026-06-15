# UrbanShield AI — Smart City Safety Platform

[![Status](https://img.shields.io/badge/Status-Hackathon--Ready-brightgreen.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](#)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](#)
[![Library](https://img.shields.io/badge/Library-NetworkX-orange.svg)](#)
[![UI/UX](https://img.shields.io/badge/UI/UX-MNC--Grade-cyan.svg)](#)

UrbanShield AI is a predictive safety intelligence platform for urban mobility. It coordinates computer vision anomaly metrics, graph neural networks (GNN), and multi-agent reinforcement learning (MARL) simulations to compute real-time safe transit routes, monitor smart city hazard grids, and safeguard citizens.

---

## 🌟 Core Features

* **Multi-Model AI Safety Pipeline**: Coordinated inference across CNN CCTV telemetry, GNN pathfinding, and MARL mitigation agents.
* **MNC-Grade UI/UX**: Premium dark/light themes, localStorage persistence, live system clocks, and active geo-location syncing.
* **Interactive Leaflet.js Overlay Map**: Visualizes Safe/Danger zones, congestion paths (colored by traffic levels), and Emergency Coverage areas (dashed help point ranges).
* **Women Safety Shield Mode**: Restructures GNN edge weights to penalize poorly-lit routes and prioritize areas with emergency dispatch points.
* **Guardian Control Hub**: Real-time companion tracking, route deviation alerts, timeline logs, and interactive Emergency Contact register management (CRUD).
* **Emergency SOS Dispatch**: Speech-to-text simulation triggers full-screen warning overlays and SMS dispatch broadcasts.
* **Citizen incident reporting**: Log local events to update the community risk heatmap dynamically.

---

## 📂 Project Structure

```text
UrbanShield-AI/
  ├── backend/               # FastAPI Backend Core
  │   ├── app.py             # REST API Entry Point & CORS Setup
  │   ├── safety_engine.py   # Pipeline Orchestrator
  │   ├── data_store.py      # Flat JSON Storage Controller
  │   ├── ai_modules/        # GNN, CNN, MARL, and Classifier modules
  │   └── utils.py           # Shared Math & Normalization Helpers
  ├── data/                  # Seeding Configurations & Active JSON Stores
  ├── frontend/              # MNC-Grade Client Assets
  │   ├── index.html         # Operation Shell
  │   ├── script.js          # Interactive Leaflet map & API client bindings
  │   ├── style.css          # Glassmorphic responsive styling rules
  │   └── pages/             # Route Analysis, Guardian, SOS, Trends dashboards
  ├── ARCHITECTURE.md        # System Topology & Data Flow Docs
  ├── feature_matrix.md      # Comparison vs Traditional Mapping Apps
  ├── demo_script.md         # End-to-End Presentation Checklist
  └── requirements.txt       # Python Dependencies
```

---

## 🚀 Quick Start

### 1. Prerequisite Checklist
Make sure you have **Python 3.10+** and **Git** installed on your system.

### 2. Run the Installation
Initialize a virtual environment, install dependencies, and launch the development server:

```bash
# Clone the repository
git clone https://github.com/your-username/UrbanShield-AI.git
cd UrbanShield-AI

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI Uvicorn server
python -m backend.app
```

### 3. Open the Application
* **Web Client**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
* **Swagger API Docs**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 📘 Documentation Links

For advanced reviews, check out our dedicated repository documentation:
1. **[ARCHITECTURE.md](file:///c:/UrbanShield-AI/ARCHITECTURE.md)**: Explains the detailed topological layouts, sequence flows, and REST endpoints.
2. **[feature_matrix.md](file:///c:/UrbanShield-AI/feature_matrix.md)**: Details the competitive analysis and parameters of UrbanShield AI vs Google/Apple Maps.
3. **[demo_script.md](file:///c:/UrbanShield-AI/demo_script.md)**: Provides a step-by-step pitch script for live demonstrations.

---

## 🛡️ Hackathon Scope

This MVP project keeps the AI modules lightweight, clean, and highly explainable. While GNN pathweighting uses real NetworkX path routing, the CNN and MARL components are simulated with structured inputs to demonstrate production telemetry without complex cloud overhead, making the codebase perfectly clean, robust, and presentation-ready.