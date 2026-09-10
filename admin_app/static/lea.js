// NCRP Sentinel LEA Command Center — Tactical GIS & Multi-Agency Dispatch Controller

document.addEventListener("DOMContentLoaded", () => {
  // --- GSAP Entrance Animations ---
  if (window.gsap) {
    gsap.from(".admin-header", { y: -30, opacity: 0, duration: 0.8, ease: "power3.out" });
    gsap.from(".welcome-header", { y: 20, opacity: 0, duration: 0.8, delay: 0.2, ease: "power3.out" });
    gsap.from(".metric-card", { y: 30, opacity: 0, stagger: 0.15, duration: 0.8, delay: 0.3, ease: "power3.out" });
    gsap.from(".surface-card", { y: 30, opacity: 0, stagger: 0.15, duration: 0.8, delay: 0.5, ease: "power3.out" });
  }

  // City coordinate map for fallback routing
  const CITY_COORDS = {
    "Mumbai": [19.0760, 72.8777],
    "Pune": [18.5204, 73.8567],
    "Nashik": [19.9975, 73.7898],
    "Surat": [21.1702, 72.8311],
    "Ahmedabad": [23.0225, 72.5714],
    "Bengaluru": [12.9716, 77.5946],
    "Hosur": [12.7409, 77.8253],
    "Delhi": [28.7041, 77.1025],
    "Hyderabad": [17.3850, 78.4867],
    "Chennai": [13.0827, 80.2707],
    "Kolkata": [22.5726, 88.3639],
    "Jaipur": [26.9124, 75.7873]
  };

  // State
  let casesCache = [];
  let previousCaseCount = 0;
  let mapInstance = null;
  let heatmapLayer = null;
  let markerGroup = null;
  let vectorLayerGroup = null;
  let atmDataCache = null;

  // Build 6x7 Activity Heatmap Matrix
  buildActivityMatrix();

  // Tab Switching
  const pillBtns = document.querySelectorAll(".pill-btn");
  const viewPanels = document.querySelectorAll(".view-panel");

  pillBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      pillBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const targetId = btn.getAttribute("data-tab");
      viewPanels.forEach(panel => {
        if (panel.id === targetId) {
          panel.classList.remove("hidden");
          if (window.gsap) {
            gsap.fromTo(panel, { opacity: 0, y: 15 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out" });
          }
        } else {
          panel.classList.add("hidden");
        }
      });

      if (targetId === "gis-view") {
        setTimeout(initLeafletMap, 150);
      } else if (targetId === "audit-view") {
        loadAuditLogs();
      }
    });
  });

  // Refresh cases button
  document.getElementById("refresh-cases-btn")?.addEventListener("click", () => {
    fetchLiveCases();
    showToast("Case feed refreshed.");
  });

  // Center Map button
  document.getElementById("center-map-btn")?.addEventListener("click", () => {
    if (mapInstance) {
      mapInstance.setView([20.5937, 78.9629], 5);
      if (vectorLayerGroup) vectorLayerGroup.clearLayers();
    }
  });

  // Map Filter Change Listeners
  document.getElementById("map-case-selector")?.addEventListener("change", (e) => {
    const selectedCaseId = e.target.value;
    if (selectedCaseId === "all") {
      if (vectorLayerGroup) vectorLayerGroup.clearLayers();
      if (mapInstance) mapInstance.setView([20.5937, 78.9629], 5);
    } else {
      const caseObj = casesCache.find(c => c.case_id === selectedCaseId);
      if (caseObj) plotCaseTrajectoryVector(caseObj);
    }
  });

  document.getElementById("map-city-filter")?.addEventListener("change", (e) => {
    const city = e.target.value;
    if (city === "all") {
      if (mapInstance) mapInstance.setView([20.5937, 78.9629], 5);
    } else if (CITY_COORDS[city] && mapInstance) {
      mapInstance.setView(CITY_COORDS[city], 12);
    }
  });

  // Threat Banner Listeners
  const banner = document.getElementById("live-threat-banner");
  document.getElementById("banner-dismiss-btn")?.addEventListener("click", () => {
    banner.classList.add("hidden");
  });

  document.getElementById("banner-view-map-btn")?.addEventListener("click", () => {
    banner.classList.add("hidden");
    document.querySelector('[data-tab="gis-view"]').click();
    if (casesCache.length > 0) {
      setTimeout(() => plotCaseTrajectoryVector(casesCache[0]), 300);
    }
  });

  // Broadcast Modal Close Listeners
  const broadcastModal = document.getElementById("broadcast-modal");
  document.getElementById("close-broadcast-btn")?.addEventListener("click", () => broadcastModal.classList.add("hidden"));
  document.getElementById("broadcast-done-btn")?.addEventListener("click", () => broadcastModal.classList.add("hidden"));

  // Initial Data Fetch & Polling
  fetchLiveCases();
  setInterval(fetchLiveCases, 4000);

  // --- Build Peak Incident Hours Grid ---
  function buildActivityMatrix() {
    const container = document.getElementById("matrix-grid-cells");
    if (!container) return;
    container.innerHTML = "";

    const levels = [
      [0, 1, 1, 2, 1, 0, 0],
      [1, 1, 2, 3, 2, 1, 0],
      [1, 2, 3, 4, 3, 2, 1],
      [2, 3, 4, 4, 4, 3, 1],
      [1, 2, 3, 4, 3, 2, 1],
      [0, 1, 2, 3, 2, 1, 0]
    ];

    levels.forEach(row => {
      row.forEach(level => {
        const cell = document.createElement("div");
        cell.className = `matrix-cell l-${level}`;
        cell.title = `Incident Risk Level: ${level}`;
        container.appendChild(cell);
      });
    });
  }

  // --- Fetch Live Cases ---
  async function fetchLiveCases() {
    try {
      const res = await fetch("/api/admin/cases");
      if (res.ok) {
        casesCache = await res.json();
        
        // Detect new case ingestion for Tactical Alert Banner
        if (casesCache.length > previousCaseCount && previousCaseCount > 0) {
          const newestCase = casesCache[0];
          triggerTacticalAlertBanner(newestCase);
        }
        previousCaseCount = casesCache.length;

        // Update metric counters dynamically
        let totalAmount = 0;
        let securedAmount = 0;
        casesCache.forEach(c => {
          totalAmount += (c.reported_amount || 0);
          if (c.status.includes("FROZEN") || c.status.includes("SECURED")) {
            securedAmount += (c.reported_amount || 0);
          }
        });

        const statTotalEl = document.getElementById("stat-total-fraud");
        const statSecuredEl = document.getElementById("stat-secured-funds");
        const statAiEl = document.getElementById("stat-ai-trajectories");

        if (statTotalEl) statTotalEl.textContent = `₹${totalAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        if (statSecuredEl) statSecuredEl.textContent = `₹${securedAmount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        if (statAiEl) statAiEl.textContent = casesCache.length.toString();

        renderRecentCasesFeed(casesCache);
        renderCasesTable(casesCache);
        populateInterventionDropdowns(casesCache);
        populateMapCaseSelector(casesCache);
      }
    } catch (err) {
      console.error("Failed to fetch cases", err);
    }
  }

  // Trigger Emergency Alert Banner
  function triggerTacticalAlertBanner(c) {
    if (!banner) return;
    const targetCity = c.prediction?.primary_target_city || c.city;
    const atmId = c.prediction?.predicted_atms?.[0]?.atm_id || "ATM";
    const amountStr = `₹${c.reported_amount.toLocaleString('en-IN')}`;

    document.getElementById("banner-complaint-id").textContent = c.complaint_id;
    document.getElementById("banner-msg").textContent = `Critical Fraud Ingested (${amountStr}) — AI Predicted Target: ${targetCity} (${atmId}) in ~20 mins!`;

    banner.classList.remove("hidden");
    showToast(`🚨 NEW LIVE COMPLAINT: ${c.complaint_id} (${amountStr})`);
  }

  // Render recent cases on dashboard overview
  function renderRecentCasesFeed(cases) {
    const listEl = document.getElementById("dashboard-recent-cases");
    if (!listEl) return;
    listEl.innerHTML = "";

    if (cases.length === 0) {
      listEl.innerHTML = `
        <div style="text-align:center;padding:32px 16px;color:var(--text-muted);font-size:0.85rem;">
          No incoming cyber threat cases yet.<br>
          <span style="color:#94a3b8;font-size:0.78rem;">Submit a complaint on Citizen Portal (Port 8000) to test live stream.</span>
        </div>
      `;
      return;
    }

    const displayCases = cases.slice(0, 4);
    displayCases.forEach(c => {
      const row = document.createElement("div");
      row.className = "recent-case-row";

      const isFrozen = c.status.includes("FROZEN") || c.status.includes("SECURED");

      row.innerHTML = `
        <div>
          <div class="case-id-tag">${c.complaint_id}</div>
          <div class="case-modality">${c.victim_name} • ${c.city}</div>
        </div>
        <div style="text-align:right;">
          <div class="case-amount-tag">₹${c.reported_amount.toLocaleString('en-IN')}</div>
          <span class="case-status-chip ${isFrozen ? 'frozen' : 'live'}">${c.status.replace('_', ' ')}</span>
        </div>
      `;
      listEl.appendChild(row);
    });
  }

  // Render Full Cases Queue Table
  function renderCasesTable(cases) {
    const tbody = document.getElementById("cases-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (cases.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align:center;padding:48px 16px;color:var(--text-muted);font-size:0.88rem;">
            <strong>Investigation Queue is Clear (0 Active Cases)</strong><br>
            <span style="font-size:0.8rem;color:#94a3b8;">When citizens submit complaints on Port 8000, they will appear here in real time.</span>
          </td>
        </tr>
      `;
      return;
    }

    cases.forEach(c => {
      const tr = document.createElement("tr");
      const isFrozen = c.status.includes("FROZEN") || c.status.includes("SECURED");
      const targetAtm = c.prediction?.predicted_atms?.[0]?.atm_id || "ATM_CLUSTER";
      const targetCity = c.prediction?.primary_target_city || c.city;

      tr.innerHTML = `
        <td><b>${c.complaint_id}</b></td>
        <td>${c.victim_name}<br><small style="color:var(--text-muted)">${c.victim_phone}</small></td>
        <td><strong style="color:var(--accent-emerald)">₹${c.reported_amount.toLocaleString('en-IN')}</strong></td>
        <td>${c.crime_type}</td>
        <td>${c.city}, ${c.state}</td>
        <td><span style="color:var(--gov-blue);font-weight:700">${targetCity}</span><br><small style="color:var(--text-muted)">${targetAtm}</small></td>
        <td><span class="case-status-chip ${isFrozen ? 'frozen' : 'live'}">${c.status.replace('_', ' ')}</span></td>
        <td>
          <div class="table-actions-cell">
            <button class="action-btn-sm" onclick="quickFreeze('${c.case_id}', '${c.scammer_upi_or_account || 'MULE_LAYER_1'}', 'HDFC')">
              ${isFrozen ? 'Re-Freeze' : 'Freeze'}
            </button>
            <button class="btn-plot-map" onclick="openAndPlotCase('${c.case_id}')">
              Map Vector
            </button>
            <a href="/dossier?id=${encodeURIComponent(c.case_id)}" target="_blank" class="btn-dossier">
              Dossier
            </a>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Populate Dropdown for Map Case Selector
  function populateMapCaseSelector(cases) {
    const select = document.getElementById("map-case-selector");
    if (!select) return;
    const currentVal = select.value;
    select.innerHTML = '<option value="all">Plot: All Monitored Clusters</option>';

    cases.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.case_id;
      opt.textContent = `Vector: ${c.complaint_id} (${c.city} → ${c.prediction?.primary_target_city || 'Target'})`;
      select.appendChild(opt);
    });

    if (currentVal && Array.from(select.options).some(o => o.value === currentVal)) {
      select.value = currentVal;
    }
  }

  // Populate Dropdowns in Interventions Tab
  function populateInterventionDropdowns(cases) {
    const freezeSelect = document.getElementById("freeze-case-select");
    const dispatchSelect = document.getElementById("dispatch-case-select");
    if (!freezeSelect || !dispatchSelect) return;

    freezeSelect.innerHTML = "";
    dispatchSelect.innerHTML = "";

    if (cases.length === 0) {
      const opt = document.createElement("option");
      opt.textContent = "No active cases available";
      freezeSelect.appendChild(opt);
      dispatchSelect.appendChild(opt.cloneNode(true));
      return;
    }

    cases.forEach(c => {
      const opt1 = document.createElement("option");
      opt1.value = c.case_id;
      opt1.textContent = `${c.complaint_id} — ₹${c.reported_amount.toLocaleString('en-IN')} (${c.victim_name})`;
      freezeSelect.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = c.case_id;
      opt2.textContent = `${c.complaint_id} — Target: ${c.prediction?.primary_target_city || c.city}`;
      dispatchSelect.appendChild(opt2);
    });
  }

  // Open Map Tab and Plot specific Case Vector
  window.openAndPlotCase = function(caseId) {
    document.querySelector('[data-tab="gis-view"]').click();
    setTimeout(() => {
      const caseObj = casesCache.find(c => c.case_id === caseId);
      if (caseObj) {
        plotCaseTrajectoryVector(caseObj);
        const sel = document.getElementById("map-case-selector");
        if (sel) sel.value = caseId;
      }
    }, 200);
  };

  // --- Tactical Attack Vector Plotter ---
  function plotCaseTrajectoryVector(caseObj) {
    if (!mapInstance) return;
    if (vectorLayerGroup) vectorLayerGroup.clearLayers();
    else vectorLayerGroup = L.layerGroup().addTo(mapInstance);

    const hops = caseObj.digital_hops || [];
    const pred = caseObj.prediction;
    const pathPoints = [];

    // 1. Victim Origin Point
    const victimCity = caseObj.city;
    const originCoords = CITY_COORDS[victimCity] || [19.0760, 72.8777];
    pathPoints.push(originCoords);

    // Marker for Victim Origin
    const victimIcon = L.divIcon({
      className: 'custom-atm-marker',
      html: `<div style="background:#2563eb;color:#fff;font-size:10px;font-weight:800;padding:2px 6px;border-radius:4px;border:1.5px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);white-space:nowrap;">SOURCE: ${victimCity}</div>`,
      iconSize: [80, 20]
    });
    L.marker(originCoords, { icon: victimIcon }).bindPopup(`<b>Victim Origin</b><br>${caseObj.victim_name} (₹${caseObj.reported_amount.toLocaleString('en-IN')})`).addTo(vectorLayerGroup);

    // 2. Mule Account Intermediaries
    hops.slice(1).forEach((h, idx) => {
      const mCity = h.city || victimCity;
      const mCoords = CITY_COORDS[mCity] || [originCoords[0] + 0.5 * (idx + 1), originCoords[1] + 0.5 * (idx + 1)];
      pathPoints.push(mCoords);

      const muleIcon = L.divIcon({
        className: 'custom-atm-marker',
        html: `<div style="background:#7c3aed;color:#fff;font-size:10px;font-weight:800;padding:2px 6px;border-radius:4px;border:1.5px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);white-space:nowrap;">MULE HOP #${h.hop_seq} (${h.bank_id})</div>`,
        iconSize: [80, 20]
      });
      L.marker(mCoords, { icon: muleIcon }).bindPopup(`<b>Mule Layer ${idx + 1}</b><br>Account: ${h.account_id}<br>Amount: ₹${(h.amount||0).toLocaleString('en-IN')}`).addTo(vectorLayerGroup);
    });

    // 3. Predicted Target ATM
    let targetCoords = null;
    let targetAtmId = "ATM_CLUSTER";
    if (pred && pred.predicted_atms && pred.predicted_atms.length > 0) {
      const topAtm = pred.predicted_atms[0];
      targetCoords = [topAtm.latitude, topAtm.longitude];
      targetAtmId = topAtm.atm_id;
    } else if (pred && pred.mathematical_coords) {
      targetCoords = [pred.mathematical_coords.latitude, pred.mathematical_coords.longitude];
    } else {
      targetCoords = [originCoords[0] + 1.2, originCoords[1] + 1.2];
    }
    pathPoints.push(targetCoords);

    // Target ATM Marker
    const targetIcon = L.divIcon({
      className: 'custom-atm-marker',
      html: `<div style="background:#dc2626;color:#fff;font-size:11px;font-weight:800;padding:4px 8px;border-radius:6px;border:2px solid #fff;box-shadow:0 0 14px rgba(220,38,38,0.8);white-space:nowrap;">🚨 TARGET ATM: ${targetAtmId}</div>`,
      iconSize: [120, 24]
    });
    L.marker(targetCoords, { icon: targetIcon }).bindPopup(`
      <div style="font-size:12px;color:#0f172a;">
        <b style="color:#dc2626;">AI PREDICTED CASHOUT POINT</b><br>
        ATM ID: <b>${targetAtmId}</b><br>
        City: ${pred?.primary_target_city || 'Unknown'}<br>
        Interception Window: <b>15-35 mins</b><br>
        <button onclick="document.querySelector('[data-tab=interventions-view]').click()" style="margin-top:6px;padding:4px 8px;background:#002244;color:#fff;border:none;border-radius:4px;cursor:pointer;">Dispatch PCR Unit</button>
      </div>
    `).addTo(vectorLayerGroup);

    // 4. Tactical Intercept Geofence (1.5 km radius)
    L.circle(targetCoords, {
      color: '#dc2626',
      fillColor: '#ef4444',
      fillOpacity: 0.18,
      radius: 1500,
      weight: 2,
      dashArray: '6, 6'
    }).bindPopup("<b>1.5 km Tactical Intercept Perimeter</b><br>Deploy PCR Units within this perimeter to prevent cashout.").addTo(vectorLayerGroup);

    // 5. Draw Digital Hops Lines
    if (pathPoints.length >= 2) {
      // Solid digital trail
      L.polyline(pathPoints.slice(0, -1), {
        color: '#2563eb',
        weight: 4,
        opacity: 0.8
      }).addTo(vectorLayerGroup);

      // Dashed predictive cashout vector
      L.polyline(pathPoints.slice(-2), {
        color: '#dc2626',
        weight: 4,
        dashArray: '8, 8',
        opacity: 0.95
      }).addTo(vectorLayerGroup);

      // Fit Map Bounds
      mapInstance.fitBounds(L.latLngBounds(pathPoints), { padding: [60, 60], maxZoom: 13 });
    }
  }

  // --- Tactical Interventions Actions ---
  window.quickFreeze = async function(caseId, account, bank) {
    try {
      const res = await fetch("/api/admin/interventions/freeze-mule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: caseId,
          account_id: account || "ICIC0009912-771823",
          bank_id: bank || "ICIC",
          operator_id: "OFFICER_DELHI_007"
        })
      });
      const data = await res.json();
      if (res.ok) {
        document.getElementById("bstep-bank-msg").textContent = `HTTP 200 OK — Account ${account} debits suspended at ${bank} Core Banking.`;
        broadcastModal.classList.remove("hidden");
        fetchLiveCases();
      } else {
        alert(data.detail || "Action failed.");
      }
    } catch (err) {
      alert("Error executing freeze.");
    }
  };

  document.getElementById("exec-freeze-btn")?.addEventListener("click", async () => {
    const caseId = document.getElementById("freeze-case-select").value;
    if (!caseId || caseId.includes("No active")) {
      alert("No active case selected.");
      return;
    }
    const account = document.getElementById("freeze-acc-input").value || "ICIC0009912-771823";
    const bank = document.getElementById("freeze-bank-input").value || "ICIC";
    await window.quickFreeze(caseId, account, bank);
  });

  document.getElementById("exec-dispatch-btn")?.addEventListener("click", async () => {
    const caseId = document.getElementById("dispatch-case-select").value;
    if (!caseId || caseId.includes("No active")) {
      alert("No active case selected.");
      return;
    }
    const atmId = document.getElementById("dispatch-atm-input").value || "ATM_GJ_SRT_041";
    const city = document.getElementById("dispatch-city-input").value || "Surat";

    try {
      const res = await fetch("/api/admin/interventions/dispatch-patrol", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: caseId,
          atm_id: atmId,
          target_city: city,
          unit_callsign: "PCR-DELTA-4"
        })
      });
      const data = await res.json();
      if (res.ok) {
        document.getElementById("bstep-cad-msg").textContent = `Priority 1 Intercept Dispatched to PCR-DELTA-4 for ${atmId} (${city}).`;
        broadcastModal.classList.remove("hidden");
        fetchLiveCases();
      }
    } catch (err) {
      alert("Error dispatching patrol.");
    }
  });

  // Open Modals from Dashboard
  document.getElementById("open-freeze-modal-btn")?.addEventListener("click", () => {
    document.querySelector('[data-tab="interventions-view"]').click();
  });
  document.getElementById("open-dispatch-modal-btn")?.addEventListener("click", () => {
    document.querySelector('[data-tab="interventions-view"]').click();
  });

  // --- Leaflet Light Map Initializer (CartoDB Voyager Light Tiles) ---
  async function initLeafletMap() {
    const mapEl = document.getElementById("leaflet-map");
    if (!mapEl) return;

    if (!mapInstance) {
      mapInstance = L.map('leaflet-map', {
        center: [20.5937, 78.9629],
        zoom: 5,
        zoomControl: false
      });

      L.control.zoom({ position: 'bottomright' }).addTo(mapInstance);

      // Light CartoDB Voyager Tiles (No API key needed)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19
      }).addTo(mapInstance);

      markerGroup = L.layerGroup().addTo(mapInstance);
      vectorLayerGroup = L.layerGroup().addTo(mapInstance);
    } else {
      mapInstance.invalidateSize();
    }

    // Load ATM Hotspots & Prediction Markers
    try {
      const [hotspotRes, atmRes] = await Promise.all([
        fetch("/api/admin/gis/hotspots"),
        fetch("/api/admin/gis/atms?limit=120")
      ]);

      const hotspotData = await hotspotRes.json();
      const atmData = await atmRes.json();
      atmDataCache = atmData;

      if (heatmapLayer) mapInstance.removeLayer(heatmapLayer);
      if (markerGroup) markerGroup.clearLayers();

      // Add Heat Layer
      if (window.L.heatLayer && hotspotData.points) {
        heatmapLayer = L.heatLayer(hotspotData.points, {
          radius: 25,
          blur: 15,
          maxZoom: 12,
          gradient: { 0.2: '#0284c7', 0.5: '#2563eb', 0.8: '#d97706', 1.0: '#dc2626' }
        }).addTo(mapInstance);
      }

      // Add High-Priority ATM Markers
      if (atmData.markers) {
        atmData.markers.slice(0, 40).forEach(atm => {
          const isCrit = atm.risk_zone > 80;
          const markerColor = isCrit ? "#dc2626" : "#0284c7";

          const icon = L.divIcon({
            className: 'custom-atm-marker',
            html: `<div style="width:12px;height:12px;border-radius:50%;background:${markerColor};border:2px solid #ffffff;box-shadow:0 1px 4px rgba(0,0,0,0.3)"></div>`,
            iconSize: [12, 12]
          });

          const m = L.marker([atm.latitude, atm.longitude], { icon: icon });
          m.bindPopup(`
            <div style="color:#0f172a;font-family:sans-serif;font-size:12px;">
              <strong>${atm.atm_id} (${atm.bank_id})</strong><br>
              Location: ${atm.city}, ${atm.state}<br>
              Risk Zone Score: <b>${atm.risk_zone}/100</b><br>
              Status: <span style="color:${isCrit ? '#dc2626':'#0284c7'};font-weight:700">${atm.status}</span>
            </div>
          `);
          markerGroup.addLayer(m);
        });
      }
    } catch (err) {
      console.error("Failed to load map data", err);
    }
  }

  // --- Audit Logs View ---
  async function loadAuditLogs() {
    const listEl = document.getElementById("audit-stream-list");
    if (!listEl) return;
    try {
      const res = await fetch("/api/admin/audit/logs");
      if (res.ok) {
        const logs = await res.json();
        listEl.innerHTML = "";
        if (logs.length === 0) {
          listEl.innerHTML = `<div style="text-align:center;padding:24px;color:var(--text-muted);font-size:0.85rem;">No tactical logs recorded yet.</div>`;
          return;
        }
        logs.forEach(l => {
          const item = document.createElement("div");
          item.className = "audit-item";
          item.innerHTML = `
            <div>
              <span class="audit-event-type">${l.event_type}</span>
              <span class="audit-msg" style="margin-left:10px">${l.message}</span>
            </div>
            <span class="audit-time">${new Date(l.timestamp).toLocaleTimeString()}</span>
          `;
          listEl.appendChild(item);
        });
      }
    } catch (err) {
      console.error("Failed to load logs", err);
    }
  }

  // Toast Notification Helper
  function showToast(message) {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    container.appendChild(toast);

    if (window.gsap) {
      gsap.fromTo(toast, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3 });
      setTimeout(() => {
        gsap.to(toast, { opacity: 0, y: -20, duration: 0.3, onComplete: () => toast.remove() });
      }, 4000);
    } else {
      setTimeout(() => toast.remove(), 4000);
    }
  }
});
