// NCRP Sentinel LEA Command Center — Modern JS & GSAP Motion Controller

document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  // --- GSAP Entrance Animations ---
  gsap.from(".admin-header", {
    y: -30,
    opacity: 0,
    duration: 0.8,
    ease: "power3.out"
  });

  gsap.from(".welcome-header", {
    y: 20,
    opacity: 0,
    duration: 0.8,
    delay: 0.2,
    ease: "power3.out"
  });

  gsap.from(".metric-card", {
    y: 30,
    opacity: 0,
    stagger: 0.15,
    duration: 0.8,
    delay: 0.3,
    ease: "power3.out"
  });

  gsap.from(".surface-card", {
    y: 30,
    opacity: 0,
    stagger: 0.15,
    duration: 0.8,
    delay: 0.5,
    ease: "power3.out"
  });

  // State
  let casesCache = [];
  let mapInstance = null;
  let heatmapLayer = null;
  let markerGroup = null;

  // Build 6x7 Activity Heatmap Matrix (Matching Reference UI)
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
          gsap.fromTo(panel, { opacity: 0, y: 15 }, { opacity: 1, y: 0, duration: 0.35, ease: "power2.out" });
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

  // Load Data
  fetchDashboardSummary();
  fetchLiveCases();
  setInterval(fetchLiveCases, 5000); // Live polling every 5s for multi-machine demo

  // --- Build Peak Incident Hours Grid ---
  function buildActivityMatrix() {
    const container = document.getElementById("matrix-grid-cells");
    if (!container) return;
    container.innerHTML = "";

    // Simulated pattern with peak in the center (matching reference image)
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
        cell.title = `Activity Level: ${level}`;
        container.appendChild(cell);
      });
    });
  }

  // --- Fetch Summary Stats ---
  async function fetchDashboardSummary() {
    try {
      const res = await fetch("/api/admin/analytics/summary");
      if (res.ok) {
        const stats = await res.json();
        document.getElementById("stat-total-fraud").textContent = `₹${stats.total_fraud_reported_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        document.getElementById("stat-secured-funds").textContent = `₹${stats.total_funds_secured_inr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        document.getElementById("stat-monitored-atms").textContent = stats.monitored_atms.toLocaleString('en-IN');
      }
    } catch (err) {
      console.error("Failed to load analytics summary", err);
    }
  }

  // --- Fetch Live Cases ---
  async function fetchLiveCases() {
    try {
      const res = await fetch("/api/admin/cases");
      if (res.ok) {
        casesCache = await res.json();
        renderRecentCasesFeed(casesCache);
        renderCasesTable(casesCache);
        populateInterventionDropdowns(casesCache);
      }
    } catch (err) {
      console.error("Failed to fetch cases", err);
    }
  }

  // Render 5 recent cases on dashboard overview
  function renderRecentCasesFeed(cases) {
    const listEl = document.getElementById("dashboard-recent-cases");
    if (!listEl) return;
    listEl.innerHTML = "";

    const displayCases = cases.slice(0, 4);
    displayCases.forEach(c => {
      const row = document.createElement("div");
      row.className = "case-item-row";

      let dotClass = "phishing";
      if (c.crime_type.includes("Arrest")) dotClass = "arrest";
      if (c.crime_type.includes("Job")) dotClass = "job";

      const isFrozen = c.status.includes("FROZEN") || c.status.includes("SECURED");

      row.innerHTML = `
        <div class="case-main-col">
          <div class="case-dot ${dotClass}"></div>
          <div>
            <span class="case-id-text">${c.complaint_id}</span>
            <span class="case-city-text">${c.victim_name} • ${c.city}</span>
          </div>
        </div>
        <div class="case-amount-col">
          <div class="case-loss-val">₹${c.reported_amount.toLocaleString('en-IN')}</div>
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

    cases.forEach(c => {
      const tr = document.createElement("tr");
      const isFrozen = c.status.includes("FROZEN") || c.status.includes("SECURED");
      const targetAtm = c.prediction?.predicted_atms?.[0]?.atm_id || "ATM_CLUSTER";
      const targetCity = c.prediction?.primary_target_city || c.city;

      tr.innerHTML = `
        <td><b>${c.complaint_id}</b></td>
        <td>${c.victim_name}<br><small style="color:var(--text-muted)">${c.victim_phone}</small></td>
        <td><strong style="color:var(--accent-emerald-light)">₹${c.reported_amount.toLocaleString('en-IN')}</strong></td>
        <td>${c.crime_type}</td>
        <td>${c.city}, ${c.state}</td>
        <td><span style="color:#c084fc;font-weight:600">${targetCity}</span><br><small style="color:var(--text-muted)">${targetAtm}</small></td>
        <td><span class="case-status-chip ${isFrozen ? 'frozen' : 'live'}">${c.status.replace('_', ' ')}</span></td>
        <td>
          <button class="action-btn-sm" onclick="quickFreeze('${c.case_id}', '${c.scammer_upi_or_account || 'MULE_LAYER_1'}', 'HDFC')">
            Freeze
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Populate Dropdowns in Interventions Tab
  function populateInterventionDropdowns(cases) {
    const freezeSelect = document.getElementById("freeze-case-select");
    const dispatchSelect = document.getElementById("dispatch-case-select");
    if (!freezeSelect || !dispatchSelect) return;

    freezeSelect.innerHTML = "";
    dispatchSelect.innerHTML = "";

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
        showToast(`🔒 ${data.message}`);
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
    const account = document.getElementById("freeze-acc-input").value || "ICIC0009912-771823";
    const bank = document.getElementById("freeze-bank-input").value || "ICIC";
    await window.quickFreeze(caseId, account, bank);
  });

  document.getElementById("exec-dispatch-btn")?.addEventListener("click", async () => {
    const caseId = document.getElementById("dispatch-case-select").value;
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
        showToast(`🚨 ${data.message}`);
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

  // --- Leaflet Dark Map Initializer ---
  async function initLeafletMap() {
    const mapEl = document.getElementById("leaflet-map");
    if (!mapEl) return;

    if (!mapInstance) {
      // Initialize centered on India
      mapInstance = L.map('leaflet-map', {
        center: [19.0760, 72.8777],
        zoom: 6,
        zoomControl: false
      });

      L.control.zoom({ position: 'bottomright' }).addTo(mapInstance);

      // Dark Matter CartoDB Tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CartoDB &copy; OpenStreetMap',
        subdomains: 'abcd',
        maxZoom: 19
      }).addTo(mapInstance);

      markerGroup = L.layerGroup().addTo(mapInstance);
    } else {
      mapInstance.invalidateSize();
    }

    // Load ATM Hotspots & Prediction Markers
    try {
      const [hotspotRes, atmRes] = await Promise.all([
        fetch("/api/admin/gis/hotspots"),
        fetch("/api/admin/gis/atms?limit=80")
      ]);

      const hotspotData = await hotspotRes.json();
      const atmData = await atmRes.json();

      if (heatmapLayer) mapInstance.removeLayer(heatmapLayer);
      if (markerGroup) markerGroup.clearLayers();

      // Add Heat Layer
      if (window.L.heatLayer && hotspotData.points) {
        heatmapLayer = L.heatLayer(hotspotData.points, {
          radius: 25,
          blur: 15,
          maxZoom: 12,
          gradient: { 0.2: '#3b82f6', 0.5: '#8b5cf6', 0.8: '#ec4899', 1.0: '#ef4444' }
        }).addTo(mapInstance);
      }

      // Add High-Priority ATM Markers
      if (atmData.markers) {
        atmData.markers.slice(0, 30).forEach(atm => {
          const isCrit = atm.risk_zone > 80;
          const markerColor = isCrit ? "#f43f5e" : "#8b5cf6";

          const icon = L.divIcon({
            className: 'custom-atm-marker',
            html: `<div style="width:14px;height:14px;border-radius:50%;background:${markerColor};border:2px solid #fff;box-shadow:0 0 10px ${markerColor}"></div>`,
            iconSize: [14, 14]
          });

          const m = L.marker([atm.latitude, atm.longitude], { icon: icon });
          m.bindPopup(`
            <div style="color:#0f172a;font-family:sans-serif;font-size:12px;">
              <strong>${atm.atm_id} (${atm.bank_id})</strong><br>
              Location: ${atm.city}, ${atm.state}<br>
              Risk Zone Score: <b>${atm.risk_zone}/100</b><br>
              Status: <span style="color:${isCrit ? '#e11d48':'#4f46e5'}">${atm.status}</span>
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
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `<i data-lucide="check-circle"></i><span>${message}</span>`;
    container.appendChild(toast);
    if (window.lucide) lucide.createIcons();

    gsap.fromTo(toast, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.3 });
    setTimeout(() => {
      gsap.to(toast, { opacity: 0, y: -20, duration: 0.3, onComplete: () => toast.remove() });
    }, 4000);
  }
});
