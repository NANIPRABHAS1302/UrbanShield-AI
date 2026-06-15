const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:8000/api" : "/api";
const appState = { zones: [] };

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "UrbanShield API request failed");
  }
  return data;
}

function riskClass(level = "") {
  const clean = level.toLowerCase();
  if (clean === "low") return "risk-low";
  if (clean === "moderate") return "risk-moderate";
  if (clean === "critical") return "risk-critical";
  return "risk-high";
}

function riskBadge(risk) {
  return `<span class="risk-badge ${riskClass(risk.level)}">${escapeHtml(risk.label || risk.level)} ${Math.round((risk.score || 0) * 100)}%</span>`;
}

function scoreBar(score) {
  const pct = Math.round((score || 0) * 100);
  const tone = pct >= 75 ? "critical" : pct >= 50 ? "watch" : "";
  return `<div class="bar"><div class="bar-fill ${tone}" style="width:${pct}%"></div></div>`;
}

function setHtml(id, html) {
  const node = document.getElementById(id);
  if (node) node.innerHTML = html;
}

// Global utilities: clock, location, theme
function initTheme() {
  const toggle = $("#themeToggle");
  
  // Set default theme from localStorage or system setting (default dark)
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);

  if (toggle) {
    toggle.addEventListener("click", () => {
      const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);
      updateThemeIcon(newTheme);
      
      // Redraw map tiles if map exists to match theme
      if (mapInstance) {
        mapInstance.remove();
        mapInstance = null;
        loadDashboard();
      }
    });
  }
}

function updateThemeIcon(theme) {
  const icon = $("#themeIcon");
  if (!icon) return;
  if (theme === "light") {
    // Moon/Dark icon
    icon.innerHTML = `<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>`;
  } else {
    // Sun/Light icon
    icon.innerHTML = `<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>`;
  }
}

function initClock() {
  const sysTimeSpan = $("#sysTime span");
  if (!sysTimeSpan) return;
  
  const updateClock = () => {
    const now = new Date();
    sysTimeSpan.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  };
  
  updateClock();
  setInterval(updateClock, 1000);
}

function initLocation() {
  const sysLocationSpan = $("#sysLocation span");
  if (!sysLocationSpan) return;

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(4);
        const lon = position.coords.longitude.toFixed(4);
        sysLocationSpan.textContent = `${lat}, ${lon}`;
      },
      () => {
        sysLocationSpan.textContent = "Bengaluru, IN";
      }
    );
  } else {
    sysLocationSpan.textContent = "Bengaluru, IN";
  }
}

async function loadZones() {
  const data = await api("/zones");
  appState.zones = data.options || [];
  appState.fullZones = data.zones || [];
  $$("select[data-zone-select]").forEach((select) => {
    const selected = select.dataset.default || select.value;
    select.innerHTML = appState.zones
      .map((zone) => `<option value="${escapeHtml(zone.id)}">${escapeHtml(zone.name)}</option>`)
      .join("");
    if (selected) select.value = selected;
  });
}

function routePayload(form) {
  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  payload.women_mode = Boolean($('[name="women_mode"]', form)?.checked);
  if (!payload.departure_time) delete payload.departure_time;
  return payload;
}

function renderRouteResult(data, targetId) {
  const route = data.recommended_route;
  const signals = route.risk.signals || {};
  const alternatives = data.alternatives || [];
  setHtml(
    targetId,
    `<div class="list-item" style="border-left: 4px solid ${route.risk.color || 'var(--accent)'}">
      <div class="list-title">
        <span>${escapeHtml(data.query.start_name)} to ${escapeHtml(data.query.end_name)}</span>
        ${riskBadge(route.risk)}
      </div>
      <div class="route-path">
        ${route.zone_names.map((name) => `<span class="route-node">${escapeHtml(name)}</span>`).join(" &rarr; ")}
      </div>
      <div class="list-meta">${route.distance_km} km - ${route.travel_time_min} mins - ${escapeHtml(data.time_context.label)}</div>
      <div class="signal-grid">
        ${Object.entries(signals)
          .map(
            ([name, score]) => `<div class="signal"><span>${escapeHtml(name.replace('_', ' '))}</span><strong>${Math.round(score * 100)}%</strong>${scoreBar(score)}</div>`
          )
          .join("")}
      </div>
      <div class="list-meta"><strong>Engine Recommendation:</strong> ${route.recommendations.map(escapeHtml).join(" ")}</div>
    </div>
    <div class="list" style="margin-top:16px">
      <h3>Alternative Route Calculations</h3>
      ${alternatives
        .map(
          (item) => `<div class="list-item" style="border-left:4px solid ${item.risk.color}">
            <div class="list-title"><span>${escapeHtml(item.preference)} path</span>${riskBadge(item.risk)}</div>
            <div class="list-meta">${item.zone_names.map(escapeHtml).join(" &rarr; ")} - ${item.travel_time_min} mins</div>
          </div>`
        )
        .join("")}
    </div>`
  );
}

function bindRouteForms() {
  $$("form[data-route-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const targetId = form.dataset.resultTarget || "routeResult";
      setHtml(targetId, `<p class="empty">Evaluating route risks...</p>`);
      try {
        const data = await api("/analyze-route", {
          method: "POST",
          body: JSON.stringify(routePayload(form)),
        });
        renderRouteResult(data, targetId);
      } catch (error) {
        setHtml(targetId, `<p class="empty">${escapeHtml(error.message)}</p>`);
      }
    });
  });
}

// Leaflet Map instance
let mapInstance = null;
async function renderMap(heatmapData) {
  const mapContainer = $("#safetyMap");
  if (!mapContainer || typeof L === 'undefined') return;

  if (mapInstance) {
    mapInstance.remove();
  }

  // Centering Bengaluru: 12.9762, 77.6150
  mapInstance = L.map('safetyMap').setView([12.9762, 77.6150], 12);
  
  const theme = document.documentElement.getAttribute("data-theme") || "dark";
  const tileUrl = theme === "dark" 
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

  L.tileLayer(tileUrl, {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
  }).addTo(mapInstance);

  // Load routes and draw polylines for Congestion Zones
  let routesData = { edges: [] };
  try {
    routesData = await api("/routes");
  } catch (err) {
    console.error("Failed to load routes for map", err);
  }

  const zoneCoords = {};
  heatmapData.forEach(z => {
    zoneCoords[z.zone_id] = [z.lat, z.lng];
  });

  // Render Edges (Paths) colored by congestion score
  routesData.edges.forEach(edge => {
    const startCoords = zoneCoords[edge.from];
    const endCoords = zoneCoords[edge.to];
    if (startCoords && endCoords) {
      const congestion = edge.congestion || 0.5;
      const pathColor = congestion >= 0.7 ? '#ef4444' : congestion >= 0.45 ? '#f59e0b' : '#10b981';
      const weight = congestion >= 0.7 ? 5 : 3;
      
      L.polyline([startCoords, endCoords], {
        color: pathColor,
        weight: weight,
        opacity: 0.65,
        dashArray: congestion >= 0.7 ? 'none' : '4, 6'
      }).addTo(mapInstance).bindPopup(`
        <div style="font-family:'Inter',sans-serif;color:var(--ink);">
          <strong style="font-size:0.95rem;">Transit Channel Connection</strong><br/>
          From: <strong>${escapeHtml(edge.from.replace('_', ' ').toUpperCase())}</strong><br/>
          To: <strong>${escapeHtml(edge.to.replace('_', ' ').toUpperCase())}</strong><br/><br/>
          Congestion Level: <strong>${Math.round(congestion * 100)}%</strong><br/>
          Base Route Safety: <strong>${Math.round(edge.base_safety * 100)}%</strong><br/>
          Transit Duration: <strong>${edge.travel_time_min} mins</strong>
        </div>
      `);
    }
  });

  // Render Nodes (Zones)
  heatmapData.forEach(zone => {
    const risk = zone.risk_score;
    const color = risk >= 0.75 ? '#ef4444' : risk >= 0.5 ? '#f59e0b' : '#10b981';
    
    // Draw risk circle overlay (Safe vs Danger zones)
    L.circle([zone.lat, zone.lng], {
      color: color,
      fillColor: color,
      fillOpacity: 0.22,
      radius: 450
    }).addTo(mapInstance);

    // Fetch full metadata for emergency coverage areas (Help Points)
    const zoneMeta = (appState.fullZones || []).find(z => z.id === zone.zone_id) || {};
    const helpPoints = zoneMeta.help_points || 0;

    // Draw Emergency Coverage Area ring if help points exist (Blue Circles)
    if (helpPoints > 0) {
      L.circle([zone.lat, zone.lng], {
        color: '#2563eb',
        fillColor: '#2563eb',
        fillOpacity: 0.05,
        radius: 750,
        weight: 1.5,
        dashArray: '4, 5'
      }).addTo(mapInstance);
    }

    // Place marker with details
    L.marker([zone.lat, zone.lng]).addTo(mapInstance)
      .bindPopup(`
        <div style="font-family:'Inter',sans-serif;color:var(--ink);">
          <strong style="font-size:1rem; display:block; margin-bottom:2px;">${escapeHtml(zone.zone_name)}</strong>
          <span style="font-size:0.8rem;color:var(--muted); display:block; margin-bottom:8px;">${escapeHtml(zone.category)}</span>
          Risk Score: <strong>${Math.round(risk * 100)}%</strong><br/>
          Safety Status: <strong style="color:${color}">${zone.status.toUpperCase()}</strong><br/>
          CCTV Feed Status: <strong>${Math.round((zone.signals.cctv_coverage || 0.5) * 100)}% coverage</strong><br/>
          Help Points Available: <strong style="color:#2563eb;">${helpPoints} units</strong><br/>
          Police ETA: <strong>${zoneMeta.police_eta_min || 10} mins</strong>
        </div>
      `);
  });
}

function renderDashboard(data) {
  setHtml(
    "dashboardStats",
    `<div class="metric-card"><div class="metric-label">Active Monitoring Zones</div><div class="metric-value">${data.zones_count}</div></div>
    <div class="metric-card"><div class="metric-label">High Risk Hotspots</div><div class="metric-value">${data.high_risk_zones.length}</div></div>
    <div class="metric-card"><div class="metric-label">SOS Dispatches Today</div><div class="metric-value">${data.recent_sos_events.length}</div></div>`
  );

  setHtml(
    "heatmapList",
    (data.heatmap || [])
      .map(
        (zone) => `<div class="list-item" style="border-left:4px solid ${zone.risk_score >= 0.75 ? 'var(--red)' : zone.risk_score >= 0.5 ? 'var(--amber)' : 'var(--green)'}">
          <div class="list-title"><span>${escapeHtml(zone.zone_name)}</span><span>${Math.round(zone.risk_score * 100)}%</span></div>
          ${scoreBar(zone.risk_score)}
          <div class="list-meta">${escapeHtml(zone.category)} - ${escapeHtml(zone.status.toUpperCase())}</div>
        </div>`
      )
      .join("")
  );

  setHtml(
    "dangerList",
    (data.danger_zones || []).length
      ? (data.danger_zones || [])
          .map(
            (zone) => `<div class="list-item" style="border-left:4px solid var(--red)">
              <div class="list-title"><span>${escapeHtml(zone.zone_name)}</span><span class="risk-badge risk-critical">${zone.active_now ? "Active Window" : "Monitored"}</span></div>
              ${scoreBar(zone.effective_risk)}
              <div class="list-meta"><strong>Guidelines:</strong> ${escapeHtml(zone.recommendation)}</div>
            </div>`
          )
          .join("")
      : `<p class="empty">No active danger zone alerts.</p>`
  );

  setHtml(
    "incidentList",
    (data.recent_incidents || []).length
      ? data.recent_incidents
          .map(
            (incident) => `<div class="list-item" style="border-left:4px solid var(--amber)">
              <div class="list-title"><span>${escapeHtml(incident.incident_type.replace('_', ' '))}</span><span class="risk-badge risk-moderate">${escapeHtml(incident.severity.toUpperCase())}</span></div>
              <div class="list-meta">Zone: ${escapeHtml(incident.zone_name || incident.zone_id)} - Status: ${escapeHtml(incident.status.toUpperCase())}</div>
              <p style="margin-top:8px;font-size:0.88rem;color:var(--muted);">${escapeHtml(incident.description)}</p>
            </div>`
          )
          .join("")
      : `<p class="empty">No citizen incidents reported yet.</p>`
  );

  setHtml("pipelineList", (data.model_pipeline || []).map((step) => `<span>${escapeHtml(step)}</span>`).join(""));
  
  // Render Map if safetyMap container exists
  if ($("#safetyMap")) {
    renderMap(data.heatmap);
  }
}

async function loadDashboard() {
  if (!$("#dashboardStats") && !$("#heatmapList")) return;
  try {
    renderDashboard(await api("/dashboard"));
  } catch (error) {
    setHtml("dashboardStats", `<p class="empty">${escapeHtml(error.message)}</p>`);
  }
}

function bindIncidentForm() {
  const form = $("#incidentForm");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setHtml("incidentResult", `<p class="empty">Submitting incident...</p>`);
    try {
      const payload = Object.fromEntries(new FormData(form).entries());
      const data = await api("/incidents", { method: "POST", body: JSON.stringify(payload) });
      setHtml("incidentResult", `<div class="list-item" style="border-left:4px solid var(--green)">Community Incident Logged Successfully. Ticket ID: ${escapeHtml(data.incident.id)}</div>`);
      form.reset();
      await loadDashboard();
    } catch (error) {
      setHtml("incidentResult", `<p class="empty">${escapeHtml(error.message)}</p>`);
    }
  });
}

async function loadSosEvents() {
  if (!$("#sosEvents")) return;
  const data = await api("/sos");
  setHtml(
    "sosEvents",
    (data.events || []).length
      ? data.events
          .map(
            (event) => `<div class="list-item" style="border-left:4px solid var(--red);">
              <div class="list-title"><span>${escapeHtml(event.user_name)} (${escapeHtml(event.category || 'emergency')})</span><span class="risk-badge risk-critical">${escapeHtml(event.risk_level)}</span></div>
              <div class="list-meta">Zone: ${escapeHtml(event.zone_name)} - Status: Dispatch Confirmed</div>
              <p style="margin-top:8px;font-size:0.85rem;color:var(--muted);">${escapeHtml(event.message)}</p>
            </div>`
          )
          .join("")
      : `<p class="empty">No simulated SOS dispatches recorded.</p>`
  );
}

function bindSosForm() {
  const form = $("#sosForm");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setHtml("sosResult", `<p class="empty">Initiating emergency transmission...</p>`);
    try {
      const payload = Object.fromEntries(new FormData(form).entries());
      payload.women_mode = Boolean($('[name="women_mode"]', form)?.checked);
      const data = await api("/sos", { method: "POST", body: JSON.stringify(payload) });
      const eventData = data.sos_event;
      setHtml(
        "sosResult",
        `<div class="list-item" style="border-left: 4px solid var(--red);margin-top:16px;">
          <div class="list-title"><span>SOS Active &bull; ${escapeHtml(eventData.id)}</span><span class="risk-badge risk-critical">Dispatched</span></div>
          <p style="margin-top:8px;font-size:0.9rem;">SMS Broadcast sent to contacts: <strong>${escapeHtml(eventData.notified_contacts.map((contact) => contact.name).join(", "))}</strong></p>
        </div>`
      );
      await loadSosEvents();

      // Show Full-screen Crimson SOS dispatch alert overlay
      let overlay = $("#sosActiveOverlay");
      if (!overlay) {
        document.body.insertAdjacentHTML("beforeend", `
          <div id="sosActiveOverlay" class="sos-overlay-active">
            <div class="sos-overlay-content">
              <div class="sos-overlay-icon">🚨</div>
              <h1>EMERGENCY BROADCAST ACTIVE</h1>
              <p>GPS tracking token shared with emergency responders and local safety desk.</p>
              <div class="dispatch-details">
                <p><strong>Incident ID:</strong> <span id="sosOverlayId">-</span></p>
                <p><strong>Notified Responders:</strong> <span id="sosOverlayContacts">-</span></p>
                <p><strong>Response ETA:</strong> 4 mins</p>
              </div>
              <button class="btn-cancel-sos" id="btnCancelSosOverlay">Deactivate Alarm</button>
            </div>
          </div>
        `);
        overlay = $("#sosActiveOverlay");
      }
      
      $("#sosOverlayId").textContent = eventData.id;
      $("#sosOverlayContacts").textContent = eventData.notified_contacts.map(c => `${c.name} (${c.phone})`).join(", ");
      overlay.style.display = "flex";
      
      $("#btnCancelSosOverlay").onclick = () => {
        overlay.style.display = "none";
      };

    } catch (error) {
      setHtml("sosResult", `<p class="empty">${escapeHtml(error.message)}</p>`);
    }
  });
}

// Guardian specific fetches
async function loadGuardian() {
  const contactList = $("#guardianContactList");
  if (!contactList) return;
  try {
    const data = await api("/guardian");
    if (data.emergency_contacts && data.emergency_contacts.length) {
      contactList.innerHTML = data.emergency_contacts.map(c => `
        <div class="list-item" style="border-left: 4px solid var(--accent); display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div class="list-title"><span>${escapeHtml(c.name)}</span><span class="risk-badge risk-low">${escapeHtml(c.type.toUpperCase())}</span></div>
            <div class="list-meta">Phone: ${escapeHtml(c.phone)} | Priority: ${c.priority}</div>
          </div>
          <button class="danger btn-delete-contact" data-id="${escapeHtml(c.id)}" style="min-height:30px; padding:4px 8px; font-size:0.75rem; box-shadow:none;">Delete</button>
        </div>
      `).join("");
      
      // Bind delete events
      $$(".btn-delete-contact", contactList).forEach(btn => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.id;
          if (confirm(`Are you sure you want to delete this contact?`)) {
            try {
              await api(`/guardian/contacts/${id}`, { method: "DELETE" });
              await loadGuardian();
            } catch (err) {
              alert(err.message);
            }
          }
        });
      });
    } else {
      contactList.innerHTML = `<p class="empty">No emergency contacts registered.</p>`;
    }
  } catch (err) {
    contactList.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  }
}

function bindGuardianForm() {
  const form = $("#addContactForm");
  if (!form) return;
  // Prevent duplicate bindings
  if (form.dataset.bound) return;
  form.dataset.bound = "true";
  
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.id = 'CON-' + Math.random().toString(36).substr(2, 9).toUpperCase();
    payload.priority = parseInt(payload.priority || "2");
    
    try {
      await api("/guardian/contacts", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      form.reset();
      await loadGuardian();
    } catch (err) {
      alert(err.message);
    }
  });
}

// Safety Trends fetches
async function loadSafetyTrends() {
  const trendsBody = $("#safetyTrendsTableBody");
  const weightsList = $("#timeWeightsList");
  if (!trendsBody && !weightsList) return;
  try {
    const data = await api("/safety-trends");
    
    if (trendsBody && data.trends) {
      trendsBody.innerHTML = data.trends.map(t => {
        const risk = t.base_risk;
        const color = risk >= 0.75 ? 'var(--red)' : risk >= 0.5 ? 'var(--amber)' : 'var(--green)';
        return `
          <tr>
            <td><strong>${escapeHtml(t.zone_name)}</strong></td>
            <td><span style="color:${color}; font-weight:700;">${Math.round(risk * 100)}%</span></td>
            <td>${Math.round(t.cctv_coverage * 100)}%</td>
            <td>${t.police_eta_min} mins</td>
          </tr>
        `;
      }).join("");
    }
    
    if (weightsList && data.time_weights) {
      weightsList.innerHTML = Object.entries(data.time_weights).map(([key, bucket]) => {
        const risk = bucket.risk || 0.3;
        const level = risk >= 0.7 ? 'Critical Risk' : risk >= 0.5 ? 'High Risk' : risk >= 0.3 ? 'Moderate Risk' : 'Low Risk';
        const tone = risk >= 0.7 ? 'critical' : risk >= 0.5 ? 'watch' : '';
        const hoursStr = `${bucket.hours[0]}:00 - ${bucket.hours[1]}:00`;
        return `
          <div class="list-item">
            <div class="list-title"><span>${escapeHtml(bucket.label)} (${hoursStr})</span><span>${Math.round(risk * 100)}%</span></div>
            <div class="bar"><div class="bar-fill ${tone}" style="width:${Math.round(risk * 100)}%"></div></div>
            <div class="list-meta">${level} period</div>
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    if (trendsBody) trendsBody.innerHTML = `<tr><td colspan="4" class="empty">${escapeHtml(err.message)}</td></tr>`;
    if (weightsList) weightsList.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  }
}

// --- Profile Page ---
async function loadProfile() {
  const form = $("#profileForm");
  if (!form) return;
  try {
    const data = await api("/profile");
    const p = data.profile || {};
    if (p.name) {
      form.querySelector('[name="name"]').value = p.name || "";
      form.querySelector('[name="email"]').value = p.email || "";
      form.querySelector('[name="phone"]').value = p.phone || "";
      form.querySelector('[name="gender"]').value = p.gender || "prefer_not_to_say";
      form.querySelector('[name="home_location"]').value = p.home_location || "";
      form.querySelector('[name="work_location"]').value = p.work_location || "";
      form.querySelector('[name="blood_group"]').value = p.blood_group || "";
    }
  } catch (err) {
    console.error("Profile load error:", err);
  }
}

function bindProfileForm() {
  const form = $("#profileForm");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const resultEl = $("#profileResult");
    try {
      const payload = Object.fromEntries(new FormData(form).entries());
      await api("/profile", { method: "POST", body: JSON.stringify(payload) });
      if (resultEl) resultEl.innerHTML = `<div class="list-item" style="border-left:4px solid var(--green)">Profile saved successfully!</div>`;
    } catch (error) {
      if (resultEl) resultEl.innerHTML = `<p class="empty">${escapeHtml(error.message)}</p>`;
    }
  });
}

// --- Guardians Page (New System) ---
async function loadGuardians() {
  const listEl = $("#guardiansList");
  const counterEl = $("#guardiansCounter");
  if (!listEl) return;
  try {
    const data = await api("/guardians");
    const guardians = data.guardians || [];
    if (counterEl) counterEl.textContent = `${guardians.length} / ${data.max}`;

    if (guardians.length) {
      listEl.innerHTML = guardians.map(g => `
        <div class="list-item" style="border-left:4px solid var(--accent); display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div class="list-title"><span>${escapeHtml(g.name)}</span><span class="risk-badge risk-low">${escapeHtml(g.relationship)}</span></div>
            <div class="list-meta">Phone: ${escapeHtml(g.phone)}</div>
          </div>
          <button class="danger btn-remove-guardian" data-id="${escapeHtml(g.id)}" style="min-height:30px; padding:4px 8px; font-size:0.75rem; box-shadow:none;">Remove</button>
        </div>
      `).join("");

      $$(".btn-remove-guardian", listEl).forEach(btn => {
        btn.addEventListener("click", async () => {
          if (confirm("Remove this guardian?")) {
            try {
              await api(`/guardians/${btn.dataset.id}`, { method: "DELETE" });
              await loadGuardians();
            } catch (err) { alert(err.message); }
          }
        });
      });
    } else {
      listEl.innerHTML = `<p class="empty">No guardians added yet. Add up to 5 emergency contacts.</p>`;
    }
  } catch (err) {
    listEl.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  }
}

function bindGuardiansForm() {
  const form = $("#addGuardianForm");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = Object.fromEntries(new FormData(form).entries());
      await api("/guardians", { method: "POST", body: JSON.stringify(payload) });
      form.reset();
      await loadGuardians();
    } catch (err) { alert(err.message); }
  });
}

// --- Live Tracking Page ---
let trackingMap = null;
let userMarker = null;
function initLiveTracking() {
  const mapContainer = $("#trackingMap");
  if (!mapContainer || typeof L === "undefined") return;

  const theme = document.documentElement.getAttribute("data-theme") || "dark";
  const tileUrl = theme === "dark"
    ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
    : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

  trackingMap = L.map("trackingMap").setView([12.9716, 77.5946], 13);
  L.tileLayer(tileUrl, { maxZoom: 19, attribution: "&copy; OSM & CARTO" }).addTo(trackingMap);

  const statusEl = $("#trackingStatus");
  const coordsEl = $("#trackingCoords");

  if (navigator.geolocation) {
    if (statusEl) statusEl.textContent = "Acquiring GPS signal...";
    navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude, accuracy } = pos.coords;
        if (coordsEl) coordsEl.textContent = `${latitude.toFixed(5)}, ${longitude.toFixed(5)} (±${Math.round(accuracy)}m)`;
        if (statusEl) statusEl.textContent = "Live Tracking Active";
        if (statusEl) statusEl.className = "tracking-status active";

        if (userMarker) {
          userMarker.setLatLng([latitude, longitude]);
        } else {
          userMarker = L.marker([latitude, longitude]).addTo(trackingMap).bindPopup("You are here").openPopup();
        }
        trackingMap.setView([latitude, longitude], 15);
      },
      () => {
        if (statusEl) statusEl.textContent = "Location denied — showing Bengaluru center";
        if (statusEl) statusEl.className = "tracking-status fallback";
        if (coordsEl) coordsEl.textContent = "12.9716, 77.5946 (default)";
      },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 }
    );
  } else {
    if (statusEl) statusEl.textContent = "Geolocation not supported";
    if (coordsEl) coordsEl.textContent = "12.9716, 77.5946 (default)";
  }

  // Load zone markers
  api("/zones").then(data => {
    (data.zones || []).forEach(z => {
      const risk = z.crime_index || 0.3;
      const color = risk >= 0.6 ? "#ef4444" : risk >= 0.4 ? "#f59e0b" : "#10b981";
      L.circle([z.lat, z.lng], { color, fillColor: color, fillOpacity: 0.18, radius: 400 }).addTo(trackingMap);
      L.marker([z.lat, z.lng], { opacity: 0.7 }).addTo(trackingMap).bindPopup(`<strong>${escapeHtml(z.name)}</strong><br/>Risk: ${Math.round(risk * 100)}%`);
    });
  }).catch(() => {});
}

// --- Mobility Services Page ---
async function loadMobility() {
  const metroEl = $("#metroList");
  const busEl = $("#busList");
  const cabEl = $("#cabList");
  if (!metroEl && !busEl && !cabEl) return;

  try {
    const data = await api("/mobility");

    if (metroEl) {
      metroEl.innerHTML = (data.metro_stations || []).map(s => `
        <div class="list-item" style="border-left:4px solid #7c3aed;">
          <div class="list-title"><span>${escapeHtml(s.name)}</span><span class="risk-badge" style="background:rgba(124,58,237,0.15);color:#7c3aed;">${escapeHtml(s.line)}</span></div>
          <div class="list-meta">Zone: ${escapeHtml(s.zone_id.replace(/_/g, ' '))}</div>
        </div>
      `).join("");
    }

    if (busEl) {
      busEl.innerHTML = (data.bus_stops || []).map(s => `
        <div class="list-item" style="border-left:4px solid #2563eb;">
          <div class="list-title"><span>${escapeHtml(s.name)}</span><span class="risk-badge" style="background:rgba(37,99,235,0.15);color:#2563eb;">Every ${s.frequency_min} min</span></div>
          <div class="list-meta">Routes: ${s.routes.map(escapeHtml).join(", ")}</div>
        </div>
      `).join("");
    }

    if (cabEl) {
      const zones = Object.entries(data.cab_services || {});
      cabEl.innerHTML = zones.map(([zoneId, info]) => {
        const surgeColor = info.surge_level === "critical" ? "var(--red)" : info.surge_level === "high" ? "var(--amber)" : "var(--green)";
        return `
          <div class="list-item" style="border-left:4px solid ${surgeColor};">
            <div class="list-title">
              <span>${escapeHtml(zoneId.replace(/_/g, ' '))}</span>
              <span class="risk-badge" style="background:${surgeColor}22;color:${surgeColor};">${escapeHtml(info.surge_level)}</span>
            </div>
            <div class="list-meta">
              Cab: ${info.cab_available ? "✅" : "❌"} | Auto: ${info.auto_available ? "✅" : "❌"} | Wait: ~${info.avg_wait_min} min
            </div>
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    if (metroEl) metroEl.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  }
}

// --- Emergency Hub Page ---
let emergencyMap = null;
async function loadEmergencyHub() {
  const policeEl = $("#policeList");
  const hospitalEl = $("#hospitalList");
  const helplinesEl = $("#helplinesList");
  if (!policeEl && !hospitalEl) return;

  try {
    const data = await api("/emergency-services");

    if (policeEl) {
      policeEl.innerHTML = (data.police_stations || []).map(s => `
        <div class="list-item" style="border-left:4px solid #2563eb;">
          <div class="list-title"><span>${escapeHtml(s.name)}</span></div>
          <div class="list-meta">📞 ${escapeHtml(s.phone)} | Zone: ${escapeHtml(s.zone_id.replace(/_/g, ' '))}</div>
        </div>
      `).join("");
    }

    if (hospitalEl) {
      hospitalEl.innerHTML = (data.hospitals || []).map(h => `
        <div class="list-item" style="border-left:4px solid #10b981;">
          <div class="list-title">
            <span>${escapeHtml(h.name)}</span>
            ${h.trauma_center ? '<span class="risk-badge risk-critical" style="font-size:0.65rem;">TRAUMA</span>' : ''}
          </div>
          <div class="list-meta">📞 ${escapeHtml(h.phone)} | Zone: ${escapeHtml(h.zone_id.replace(/_/g, ' '))}</div>
        </div>
      `).join("");
    }

    if (helplinesEl && data.helplines) {
      const icons = { police: "👮", emergency: "🆘", women_helpline: "🚺", ambulance: "🚑", fire: "🚒", child_helpline: "👶" };
      helplinesEl.innerHTML = Object.entries(data.helplines).map(([key, number]) => `
        <div class="helpline-card">
          <span class="helpline-icon">${icons[key] || "📞"}</span>
          <span class="helpline-label">${escapeHtml(key.replace(/_/g, ' '))}</span>
          <span class="helpline-number">${escapeHtml(number)}</span>
        </div>
      `).join("");
    }

    // Render emergency map if container exists
    const mapContainer = $("#emergencyMap");
    if (mapContainer && typeof L !== "undefined") {
      const theme = document.documentElement.getAttribute("data-theme") || "dark";
      const tileUrl = theme === "dark"
        ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

      emergencyMap = L.map("emergencyMap").setView([12.9716, 77.5946], 11);
      L.tileLayer(tileUrl, { maxZoom: 19, attribution: "&copy; OSM & CARTO" }).addTo(emergencyMap);

      (data.police_stations || []).forEach(s => {
        L.marker([s.lat, s.lng]).addTo(emergencyMap).bindPopup(`<strong>🚔 ${escapeHtml(s.name)}</strong><br/>📞 ${escapeHtml(s.phone)}`);
      });
      (data.hospitals || []).forEach(h => {
        L.marker([h.lat, h.lng]).addTo(emergencyMap).bindPopup(`<strong>🏥 ${escapeHtml(h.name)}</strong><br/>📞 ${escapeHtml(h.phone)}${h.trauma_center ? "<br/>⚠️ Trauma Center" : ""}`);
      });
    }
  } catch (err) {
    if (policeEl) policeEl.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  }
}

// --- Command Center Widgets ---
async function loadCommandCenter() {
  const widgetGrid = $("#commandCenterWidgets");
  if (!widgetGrid) return;
  try {
    const data = await api("/command-center");
    const s = data.status;
    widgetGrid.innerHTML = `
      <div class="widget-card">
        <div class="widget-icon">🛡️</div>
        <div class="widget-label">City Safety Score</div>
        <div class="widget-value" style="color:${s.city_safety_score >= 0.7 ? 'var(--green)' : s.city_safety_score >= 0.5 ? 'var(--amber)' : 'var(--red)'}">${Math.round(s.city_safety_score * 100)}%</div>
      </div>
      <div class="widget-card">
        <div class="widget-icon">📍</div>
        <div class="widget-label">Monitoring Zones</div>
        <div class="widget-value">${s.total_zones}</div>
      </div>
      <div class="widget-card">
        <div class="widget-icon">⚠️</div>
        <div class="widget-label">Active Danger Zones</div>
        <div class="widget-value" style="color:var(--red)">${s.active_danger_zones}</div>
      </div>
      <div class="widget-card">
        <div class="widget-icon">📋</div>
        <div class="widget-label">Total Incidents</div>
        <div class="widget-value">${s.total_incidents}</div>
      </div>
      <div class="widget-card">
        <div class="widget-icon">👥</div>
        <div class="widget-label">Guardians</div>
        <div class="widget-value">${s.guardian_count} / ${s.max_guardians}</div>
      </div>
      <div class="widget-card">
        <div class="widget-icon">👤</div>
        <div class="widget-label">Profile</div>
        <div class="widget-value" style="font-size:0.9rem;">${escapeHtml(s.profile_name)}</div>
      </div>
      <div class="widget-card">
        <div class="widget-icon">🚔</div>
        <div class="widget-label">Police Stations</div>
        <div class="widget-value">${s.police_stations_count}</div>
      </div>
      <div class="widget-card">
        <div class="widget-icon">🏥</div>
        <div class="widget-label">Hospitals</div>
        <div class="widget-value">${s.hospitals_count}</div>
      </div>
    `;
  } catch (err) {
    if (widgetGrid) widgetGrid.innerHTML = `<p class="empty">${escapeHtml(err.message)}</p>`;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    initTheme();
    initClock();
    initLocation();
    await loadZones();
    bindRouteForms();
    bindIncidentForm();
    bindSosForm();
    bindGuardianForm();
    bindProfileForm();
    bindGuardiansForm();
    await loadDashboard();
    await loadCommandCenter();
    await loadSosEvents();
    await loadGuardian();
    await loadGuardians();
    await loadProfile();
    await loadSafetyTrends();
    await loadMobility();
    await loadEmergencyHub();
    initLiveTracking();
    const autoForm = document.querySelector("form[data-auto-run]");
    if (autoForm) autoForm.requestSubmit();
  } catch (error) {
    document.body.insertAdjacentHTML("beforeend", `<div class="shell"><p class="empty">${escapeHtml(error.message)}</p></div>`);
  }
});
