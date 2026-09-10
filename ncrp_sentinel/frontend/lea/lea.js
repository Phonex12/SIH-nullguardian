// State Management
let map = null;
let heatLayer = null;
let atmMarkersLayer = null;
let trajectoryLayer = null;
let targetPulseMarker = null;

let currentOfficerToken = sessionStorage.getItem("lea_token") || null;
let currentOfficerInfo = JSON.parse(sessionStorage.getItem("lea_officer") || "null");
let activeCases = [];
let selectedCase = null;

document.addEventListener("DOMContentLoaded", async () => {
    checkAuthentication();
    initTacticalMap();
    setupEventListeners();

    if (currentOfficerToken) {
        await loadDashboardData();
        startTelemetryPolling();
    }
});

// 1. Authentication & Officer Session
function checkAuthentication() {
    const modal = document.getElementById("loginModal");
    if (!currentOfficerToken) {
        modal.style.display = "flex";
    } else {
        modal.style.display = "none";
        updateOfficerHud();
    }
}

function updateOfficerHud() {
    if (currentOfficerInfo) {
        document.getElementById("officerBadgeText").innerText = currentOfficerInfo.badge_id || "I4C-OFFICER";
        document.getElementById("officerNameText").innerText = `${currentOfficerInfo.rank || ''} ${currentOfficerInfo.name || ''}`;
    }
}

window.quickLogin = function(badge, pwd) {
    document.getElementById("badgeIdInput").value = badge;
    document.getElementById("passwordInput").value = pwd;
    document.getElementById("leaLoginForm").dispatchEvent(new Event("submit"));
};

document.getElementById("leaLoginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const badge = document.getElementById("badgeIdInput").value.trim();
    const password = document.getElementById("passwordInput").value.trim();

    try {
        const res = await fetch("/api/auth/lea/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ badge_id: badge, password: password })
        });

        const data = await res.json();
        if (res.ok) {
            currentOfficerToken = data.access_token;
            currentOfficerInfo = data.user_info;
            sessionStorage.setItem("lea_token", currentOfficerToken);
            sessionStorage.setItem("lea_officer", JSON.stringify(currentOfficerInfo));
            
            document.getElementById("loginModal").style.display = "none";
            updateOfficerHud();
            await loadDashboardData();
            startTelemetryPolling();
            logToTerminal(`OFFICER AUTHENTICATED: ${data.user_info.name} (${data.user_info.badge_id}) // SESSION ACTIVE`);
        } else {
            alert(data.detail || "Authentication rejected. Invalid credentials.");
        }
    } catch (err) {
        console.error(err);
        alert("Network error connecting to tactical auth server.");
    }
});

document.getElementById("btnLogout").addEventListener("click", () => {
    sessionStorage.removeItem("lea_token");
    sessionStorage.removeItem("lea_officer");
    location.reload();
});

// 2. Leaflet GIS Map Initialization
function initTacticalMap() {
    // Center of India (Maharashtra / Central Corridor)
    map = L.map("tacticalMap", {
        center: [19.5, 75.5],
        zoom: 6,
        zoomControl: true,
        attributionControl: false
    });

    // Dark Matter Tiles
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 18,
        subdomains: "abcd"
    }).addTo(map);

    atmMarkersLayer = L.layerGroup().addTo(map);
    trajectoryLayer = L.layerGroup().addTo(map);
}

// 3. Load Dashboard Data
async function loadDashboardData() {
    await fetchStats();
    await fetchHeatmap();
    await fetchAtmMappings();
    await fetchCases();
}

async function fetchStats() {
    try {
        const res = await fetch("/api/lea/dashboard-stats", {
            headers: { "Authorization": `Bearer ${currentOfficerToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            document.getElementById("statTotalAtms").innerText = data.total_monitored_atms.toLocaleString();
            document.getElementById("statLiveCases").innerText = data.active_live_cases;
            document.getElementById("statCriticalAtms").innerText = data.critical_risk_atms.toLocaleString();
            document.getElementById("statFrozenAccounts").innerText = data.accounts_frozen_count;
            document.getElementById("statLatency").innerText = `${data.avg_prediction_latency_ms} ms`;
        }
    } catch (e) {
        console.warn("Failed fetching stats", e);
    }
}

async function fetchHeatmap() {
    const state = document.getElementById("mapStateFilter").value;
    try {
        const res = await fetch(`/api/lea/heatmap?state=${encodeURIComponent(state)}&min_risk=40`, {
            headers: { "Authorization": `Bearer ${currentOfficerToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            if (heatLayer) map.removeLayer(heatLayer);

            if (document.getElementById("toggleHeatmap").checked && data.points.length > 0) {
                heatLayer = L.heatLayer(data.points, {
                    radius: 20,
                    blur: 15,
                    maxZoom: 12,
                    gradient: { 0.3: '#3b82f6', 0.65: '#f59e0b', 0.95: '#ff3366' }
                }).addTo(map);
            }
        }
    } catch (e) {
        console.warn("Error fetching heatmap", e);
    }
}

async function fetchAtmMappings() {
    const state = document.getElementById("mapStateFilter").value;
    try {
        const res = await fetch(`/api/lea/atm-markers?state=${encodeURIComponent(state)}&limit=120`, {
            headers: { "Authorization": `Bearer ${currentOfficerToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            atmMarkersLayer.clearLayers();

            if (!document.getElementById("toggleAtmMappings").checked) return;

            data.markers.forEach(atm => {
                const isCritical = atm.risk_zone > 75;
                const circle = L.circleMarker([atm.latitude, atm.longitude], {
                    radius: isCritical ? 6 : 4,
                    fillColor: isCritical ? "#ff3366" : "#38bdf8",
                    color: "#ffffff",
                    weight: 1,
                    opacity: 0.9,
                    fillOpacity: 0.8
                });

                circle.bindPopup(`
                    <div style="font-family: var(--font-sans); font-size: 12px; color: #0f172a;">
                        <strong style="color: #0e2a47; font-size: 13px;">${atm.atm_id} (${atm.bank_id})</strong><br>
                        📍 ${atm.city}, ${atm.state}<br>
                        🚨 Threat Zone: <strong>${atm.risk_zone}/100</strong><br>
                        ⏱️ 24x7 Operations: <strong>${atm.operating_24x7 ? 'Yes' : 'No'}</strong><br>
                        📊 Baseline Txn Vol: ${atm.baseline_volume.toLocaleString()}/day
                    </div>
                `);

                atmMarkersLayer.addLayer(circle);
            });
        }
    } catch (e) {
        console.warn("Error fetching ATM markers", e);
    }
}

async function fetchCases() {
    try {
        const res = await fetch("/api/lea/cases", {
            headers: { "Authorization": `Bearer ${currentOfficerToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            activeCases = data.cases || [];
            renderIncidentFeed();
            
            // Auto select first case if none selected
            if (!selectedCase && activeCases.length > 0) {
                selectCase(activeCases[0].case_id);
            }
        }
    } catch (e) {
        console.warn("Error fetching cases", e);
    }
}

// 4. Render Incident Feed
function renderIncidentFeed() {
    const container = document.getElementById("incidentListContainer");
    const crimeFilter = document.getElementById("filterCrimeType").value;

    container.innerHTML = "";

    const filtered = activeCases.filter(c => {
        if (crimeFilter !== "ALL" && c.crime_type !== crimeFilter) return false;
        return true;
    });

    if (filtered.length === 0) {
        container.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: 12px; padding: 20px;">No incidents matching filter.</div>`;
        return;
    }

    filtered.forEach(c => {
        const card = document.createElement("div");
        card.className = `incident-card ${selectedCase && selectedCase.case_id === c.case_id ? 'selected' : ''}`;
        card.onclick = () => selectCase(c.case_id);

        const isFrozen = c.actions_taken?.bank_frozen;
        const threatBadgeClass = isFrozen ? 'badge-locked' : (c.prediction?.threat_level === 'CRITICAL' ? 'badge-critical' : 'badge-high');
        const threatBadgeText = isFrozen ? 'FUNDS_LOCKED' : (c.prediction?.threat_level || 'HIGH');

        const primaryAtm = c.prediction?.predicted_atms?.[0];
        const targetDesc = primaryAtm ? `${primaryAtm.atm_id} (${primaryAtm.city})` : 'Target Calculated';

        card.innerHTML = `
            <div class="incident-card-top">
                <span class="incident-case-id">${c.case_id}</span>
                <span class="badge-threat ${threatBadgeClass}">${threatBadgeText}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <span class="incident-amount">₹${Number(c.reported_amount).toLocaleString('en-IN')}</span>
                <span style="font-size: 11px; color: var(--neon-cyan); font-weight: 600;">${c.crime_type}</span>
            </div>
            <div class="incident-meta">
                <span>📍 ${c.city}, ${c.state}</span>
                <span>•</span>
                <span>⏱️ ${c.registered_at}</span>
            </div>
            <div class="incident-prediction-summary">
                <span style="color: var(--text-secondary);">🎯 Target ATM:</span>
                <strong style="color: #67e8f9;">${targetDesc}</strong>
            </div>
        `;
        container.appendChild(card);
    });
}

// 5. Select Case & Render Trajectory on Map
function selectCase(caseId) {
    selectedCase = activeCases.find(c => c.case_id === caseId);
    if (!selectedCase) return;

    renderIncidentFeed();

    // Show details in Right Panel
    document.getElementById("noCaseSelectedMsg").style.display = "none";
    document.getElementById("activeCaseDetailBox").style.display = "block";
    document.getElementById("selectedCaseBadge").innerText = selectedCase.case_id;

    document.getElementById("detailCaseId").innerText = `${selectedCase.case_id} (${selectedCase.crime_type})`;
    document.getElementById("detailAmount").innerText = `₹${Number(selectedCase.reported_amount).toLocaleString('en-IN')}`;
    document.getElementById("detailVictimMeta").innerText = `Victim: ${selectedCase.victim_name} (${selectedCase.victim_phone}) | Source: ${selectedCase.victim_account}`;

    const isFrozen = selectedCase.actions_taken?.bank_frozen;
    const badgeEl = document.getElementById("detailThreatBadge");
    badgeEl.innerText = isFrozen ? "FUNDS_LOCKED" : selectedCase.prediction?.threat_level;
    badgeEl.className = `badge-threat ${isFrozen ? 'badge-locked' : 'badge-critical'}`;

    const primaryAtm = selectedCase.prediction?.predicted_atms?.[0];
    if (primaryAtm) {
        document.getElementById("detailAtmId").innerText = `${primaryAtm.atm_id} (${primaryAtm.bank_id})`;
        document.getElementById("detailAtmLoc").innerText = `📍 ${primaryAtm.city}, ${primaryAtm.state} (Coords: ${primaryAtm.latitude.toFixed(4)}, ${primaryAtm.longitude.toFixed(4)})`;
        document.getElementById("detailAtmDist").innerText = `Dist: ${primaryAtm.distance_km} km`;
        document.getElementById("detailAtmConf").innerText = `Confidence: ${primaryAtm.confidence_pct}% (${primaryAtm.estimated_cashout_window})`;
    }

    // Update Proactive Action Buttons Status
    const btnFreeze = document.getElementById("btnActionFreeze");
    const btnDispatch = document.getElementById("btnActionDispatch");
    const btnSurveillance = document.getElementById("btnActionSurveillance");

    if (selectedCase.actions_taken?.bank_frozen) {
        btnFreeze.classList.add("done");
        btnFreeze.innerHTML = "<span>✓ Lien Active — Stolen Funds Frozen</span>";
    } else {
        btnFreeze.classList.remove("done");
        btnFreeze.innerHTML = "<span>⚡ Execute Automated Lien / Freeze</span>";
    }

    if (selectedCase.actions_taken?.intercept_dispatched) {
        btnDispatch.classList.add("done");
        btnDispatch.innerHTML = "<span>✓ PCR Intercept Dispatched (ETA: 8-12m)</span>";
    } else {
        btnDispatch.classList.remove("done");
        btnDispatch.innerHTML = "<span>🚨 Dispatch Nearest Unit (ETA: 8-12m)</span>";
    }

    if (selectedCase.actions_taken?.surveillance_alert) {
        btnSurveillance.classList.add("done");
        btnSurveillance.innerHTML = "<span>✓ Surveillance Camera Flag Active</span>";
    } else {
        btnSurveillance.classList.remove("done");
        btnSurveillance.innerHTML = "<span>👁️ Trigger Surveillance Alert</span>";
    }

    // Render Digital Hops Flow
    const hopsFlowEl = document.getElementById("detailHopsFlow");
    hopsFlowEl.innerHTML = (selectedCase.digital_hops || []).map((h, i) => `
        <div style="padding: 6px 0; border-bottom: 1px dashed var(--border-color);">
            <strong style="color: var(--neon-cyan);">Hop #${i+1}:</strong> ₹${Number(h.amount).toLocaleString('en-IN')} via ${h.bank_id} (${h.city}) ➔ ${h.destination_account || 'Mule Acc'}
        </div>
    `).join("") + `<div style="padding: 6px 0; color: #ff3366; font-weight: 700;">➔ [Predicted Cashout]: ${primaryAtm ? primaryAtm.atm_id : 'Target ATM'}</div>`;

    // Visual Trajectory on Leaflet Map
    renderTrajectoryOnMap(selectedCase);
}

function renderTrajectoryOnMap(incident) {
    trajectoryLayer.clearLayers();
    if (targetPulseMarker) {
        map.removeLayer(targetPulseMarker);
        targetPulseMarker = null;
    }

    const primaryAtm = incident.prediction?.predicted_atms?.[0];
    if (!primaryAtm) return;

    const lat = primaryAtm.latitude;
    const lon = primaryAtm.longitude;

    // Center map smoothly
    map.setView([lat, lon], 12, { animate: true });

    // 1. Add Pulsing Target Radar Pin
    const pulseIcon = L.divIcon({
        className: 'radar-pulse-marker',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    targetPulseMarker = L.marker([lat, lon], { icon: pulseIcon }).addTo(map);
    targetPulseMarker.bindPopup(`
        <div style="font-family: var(--font-sans); color: #0f172a; font-size: 13px;">
            <strong style="color: #ef4444;">🚨 PREDICTED TARGET ATM: ${primaryAtm.atm_id}</strong><br>
            Bank: <strong>${primaryAtm.bank_id}</strong> | City: <strong>${primaryAtm.city}</strong><br>
            Match Confidence: <strong style="color: #059669;">${primaryAtm.confidence_pct}%</strong><br>
            Cashout Window: <strong style="color: #dc2626;">${primaryAtm.estimated_cashout_window}</strong>
        </div>
    `).openPopup();

    // 2. Trajectory Flight Path Line (Victim city -> Target ATM)
    // Approximate victim point offset for visual flight path
    const startLat = lat - 0.45;
    const startLon = lon - 0.55;

    const pathCoords = [
        [startLat, startLon],
        [startLat + 0.2, startLon + 0.25],
        [lat, lon]
    ];

    const polyline = L.polyline(pathCoords, {
        color: '#00f0ff',
        weight: 3,
        opacity: 0.8,
        dashArray: '8, 8',
        lineCap: 'round'
    }).addTo(trajectoryLayer);

    logToTerminal(`RADAR LOCKED ON ${primaryAtm.atm_id} (${primaryAtm.city}) // TRAJECTORY HOP LINE PROJECTED`);
}

// 6. Proactive Intervention Triggers
function setupEventListeners() {
    // 1-Click Bank Freeze
    document.getElementById("btnActionFreeze").addEventListener("click", async () => {
        if (!selectedCase) return;
        if (selectedCase.actions_taken?.bank_frozen) return;

        const primaryAtm = selectedCase.prediction?.predicted_atms?.[0];
        const bankId = primaryAtm ? primaryAtm.bank_id : "BANK_02";
        const muleAcc = selectedCase.digital_hops?.[selectedCase.digital_hops.length - 1]?.destination_account || "ACC_MULE_99";

        try {
            const res = await fetch("/api/lea/action/freeze-account", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${currentOfficerToken}`
                },
                body: JSON.stringify({
                    case_id: selectedCase.case_id,
                    account_id: muleAcc,
                    bank_id: bankId,
                    freeze_reason: `Emergency CFCFRMS lien for Case ${selectedCase.case_id}`
                })
            });

            const data = await res.json();
            if (res.ok) {
                selectedCase.actions_taken.bank_frozen = true;
                selectCase(selectedCase.case_id);
                await fetchStats();
                logToTerminal(`[ACTION CONFIRMED] ${data.message} // FUNDS FROZEN AT BANK NODE`);
            }
        } catch (e) {
            console.error(e);
            alert("Error triggering automated bank freeze.");
        }
    });

    // Dispatch Intercept
    document.getElementById("btnActionDispatch").addEventListener("click", async () => {
        if (!selectedCase) return;
        if (selectedCase.actions_taken?.intercept_dispatched) return;

        const primaryAtm = selectedCase.prediction?.predicted_atms?.[0];
        const atmId = primaryAtm ? primaryAtm.atm_id : "ATM_000000";

        try {
            const res = await fetch("/api/lea/action/dispatch-intercept", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${currentOfficerToken}`
                },
                body: JSON.stringify({
                    case_id: selectedCase.case_id,
                    atm_id: atmId,
                    unit_callsign: "PCR-TACTICAL-ALPHA",
                    priority: "CRITICAL_IMMEDIATE"
                })
            });

            const data = await res.json();
            if (res.ok) {
                selectedCase.actions_taken.intercept_dispatched = true;
                selectCase(selectedCase.case_id);
                await fetchStats();
                logToTerminal(`[DISPATCH CONFIRMED] Tactical Intercept Unit PCR-ALPHA heading to ${atmId} (ETA: ${data.eta})`);
            }
        } catch (e) {
            console.error(e);
            alert("Error dispatching intercept unit.");
        }
    });

    // Surveillance Alert
    document.getElementById("btnActionSurveillance").addEventListener("click", async () => {
        if (!selectedCase) return;
        if (selectedCase.actions_taken?.surveillance_alert) return;

        const primaryAtm = selectedCase.prediction?.predicted_atms?.[0];
        const atmId = primaryAtm ? primaryAtm.atm_id : "ATM_000000";

        try {
            const res = await fetch("/api/lea/action/surveillance-alert", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${currentOfficerToken}`
                },
                body: JSON.stringify({
                    case_id: selectedCase.case_id,
                    atm_id: atmId,
                    notes: "Target suspect flagged on video surveillance."
                })
            });

            const data = await res.json();
            if (res.ok) {
                selectedCase.actions_taken.surveillance_alert = true;
                selectCase(selectedCase.case_id);
                logToTerminal(`[SURVEILLANCE CONFIRMED] ATM ${atmId} camera live facial-rec flagged.`);
            }
        } catch (e) {
            console.error(e);
            alert("Error sending surveillance alert.");
        }
    });

    // Map Filters
    document.getElementById("mapStateFilter").addEventListener("change", async () => {
        await fetchHeatmap();
        await fetchAtmMappings();
    });

    document.getElementById("toggleHeatmap").addEventListener("change", () => {
        if (heatLayer) {
            if (document.getElementById("toggleHeatmap").checked) {
                map.addLayer(heatLayer);
            } else {
                map.removeLayer(heatLayer);
            }
        }
    });

    document.getElementById("toggleAtmMappings").addEventListener("change", () => {
        if (document.getElementById("toggleAtmMappings").checked) {
            map.addLayer(atmMarkersLayer);
        } else {
            map.removeLayer(atmMarkersLayer);
        }
    });

    document.getElementById("filterCrimeType").addEventListener("change", () => {
        renderIncidentFeed();
    });

    document.getElementById("btnRefreshCases").addEventListener("click", async () => {
        await fetchCases();
        await fetchStats();
        logToTerminal("INCIDENT REPOSITORY RE-SYNCHRONIZED WITH NCRP NATIONAL QUEUE");
    });
}

function logToTerminal(msg) {
    const time = new Date().toTimeString().split(" ")[0];
    const ticker = document.getElementById("terminalTicker");
    ticker.innerText = `[${time} UTC] ${msg}`;
}

function startTelemetryPolling() {
    setInterval(async () => {
        try {
            const res = await fetch("/api/alerts/live");
            if (res.ok) {
                const data = await res.json();
                if (data.recent_tactical_events && data.recent_tactical_events.length > 0) {
                    const latest = data.recent_tactical_events[0];
                    logToTerminal(`${latest.event_type}: ${latest.message}`);
                }
            }
        } catch (e) {
            // Ignore background polling glitches
        }
    }, 5000);
}
