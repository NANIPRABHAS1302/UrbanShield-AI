# UrbanShield AI — Presentation & Pitch Demo Script

This script provides a structured walkthrough to demonstrate the core capabilities of the UrbanShield AI predictive safety platform during pitches, hackathons, or system evaluations.

---

## Part 1: Operational Control Room (Dashboard)
1. **Open the Operations Dashboard** (`/frontend/pages/dashboard.html` or through the navigation bar).
2. **Point out the UI/UX indicators**:
   * **Live Clock & Geo-location**: Emphasize that the platform actively synchronizes with client-side coordinates and ticks in real-time.
   * **Dark / Light Mode Toggle**: Click the theme toggle button in the header topbar. Show how the Leaflet map tiles instantly redraw (Dark Map vs Light Street View) and how the settings persist via `localStorage`.
3. **Showcase the Interactive Map Overlays**:
   * **Safe & Danger Zones**: Point out the green circles (low-risk sectors) and red circles (active threat windows).
   * **Congestion Paths**: Point out the polyline links connecting the zones (red/orange indicates high congestion, green indicates low congestion).
   * **Emergency Coverage Area**: Point out the large light-blue dashed circles showing the 750m coverage radius of safety Help Points.
4. **Inspect the Telemetry**: Show the "Active Danger Windows" list and "Live Risk Heatmap" ranking zones by predictive threat scores.

---

## Part 2: Secure Commute (Route Safety Analysis)
1. **Navigate to Route Analysis** in the navigation bar.
2. **Setup a Commute Query**:
   * Select **Start Zone**: `Central Station`
   * Select **Destination**: `Tech Park`
   * Select **Preference**: `Safest Path First`
   * Leave "Women Safety Mode" **unchecked**.
3. **Run the Analysis**: Click "Analyze Risk & Alternatives".
   * Show the route: `Central Station &rarr; Market Street &rarr; Park Avenue &rarr; Tech Park`.
   * Point out the model signals breakdown: CNN telemetry risk, GNN topology weights, and MARL mitigation factors.
4. **Activate Women Safety Mode**:
   * Check the **Enable Women Safety Mode** checkbox.
   * Click "Analyze Risk & Alternatives" again.
   * **Explain the Deviation**: The GNN now detects that `Market Street` has moderate risk and poorly-lit connectors. The system recalculates and reroutes: `Central Station &rarr; East Metro &rarr; Tech Park` (completely bypassing low-light sectors and routing through Transit Hubs with active help points).
   * Point out the safety recommendations checklist generated dynamically.

---

## Part 3: Women Safety & Guardian Control Hub
1. **Navigate to the Guardian Hub** (`/frontend/pages/guardian_dashboard.html`).
2. **Explain the Setup**: This dashboard is used by family members or safety desks to track the companion's transit live.
3. **Simulate Live GPS Tracking**: Point out the blue tracking marker moving along the route coordinates on the map and generating GPS logs in the timeline.
4. **Trigger Route Deviation Alert**:
   * Click **Simulate Path Deviation**.
   * **Point out the UX impact**: Instantly, a massive red warning banner slides down alerting that the vehicle has drifted off the safe corridor near `Old Mill Road`. A red alert log is injected into the event feed.
5. **Manage Emergency Contacts (CRUD)**:
   * Scroll to the "Emergency Contacts Register".
   * **Delete a Contact**: Click "Delete" on "Urban Mobility Safety Desk". Confirm the prompt. Show that the contact is instantly removed from the UI.
   * **Register a New Contact**: Fill in the form: Name = `Guardian Prime`, Phone = `+91 99000-88000`, Relation = `Guardian / Family`, Priority = `Priority 1 (Primary)`.
   * Click "Register Contact". Point out that the contact is created dynamically and saved into the database files!

---

## Part 4: Emergency SOS Dispatch Alarm
1. **Navigate to the SOS page** (`/frontend/pages/sos.html`).
2. **Simulate Speech-to-Text Ingestion**:
   * Click **Simulate Voice Ingest**.
   * Show that the text area instantly populates with simulated voice transcriptions: *"Harassment warning near Old Mill Road. Seeking immediate dispatch."*
3. **Trigger the SOS Button**: Click the huge pulsing red **SOS** button.
   * **Explain the Visual Feedback**: The screen instantly triggers a full-screen crimson pulsing modal: **EMERGENCY BROADCAST ACTIVE**.
   * Point out that the incident ID is broadcasted along with SMS updates dispatched to all registered contacts (including the new one we registered).
4. **Cancel Alarm**: Click "Deactivate Alarm" to reset the page.

---

## Part 5: Citizen Incident Logging
1. **Navigate to the Incidents page** (`/frontend/pages/incident_report.html`).
2. **Submit a Community Report**:
   * Select zone: `River Walk`.
   * Severity: `High`.
   * Classification: `Harassment`.
   * Click "Submit Community Report".
3. **Verify Community Log**:
   * Point out the success ticket ID created under "Active Citizen Reports".
   * Return to the **Dashboard** and show that the heatmap risk score for `River Walk` has dynamically increased, and the incident list is updated in real-time!
