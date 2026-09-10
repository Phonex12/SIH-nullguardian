// NCRP Sentinel Citizen Portal — Interactive UI Controller (Official Government Light Theme)

document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  // --- Modal Open / Close Controller ---
  const complaintModal = document.getElementById("complaint-modal");
  const closeModalBtn = document.getElementById("close-modal-btn");
  const modalDoneBtn = document.getElementById("modal-done-btn");

  const openTriggers = [
    document.getElementById("open-complaint-btn-nav"),
    document.getElementById("hero-file-complaint-btn"),
    document.getElementById("banner-complaint-btn")
  ];

  openTriggers.forEach(btn => {
    if (btn) {
      btn.addEventListener("click", () => {
        openComplaintModal();
      });
    }
  });

  if (closeModalBtn) closeModalBtn.addEventListener("click", closeComplaintModal);
  if (modalDoneBtn) modalDoneBtn.addEventListener("click", closeComplaintModal);

  // Close modal when clicking on backdrop outside modal window
  complaintModal.addEventListener("click", (e) => {
    if (e.target === complaintModal) {
      closeComplaintModal();
    }
  });

  function openComplaintModal() {
    complaintModal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
    goToFormStep(1);
    if (window.lucide) lucide.createIcons();
  }

  function closeComplaintModal() {
    complaintModal.classList.add("hidden");
    document.body.style.overflow = "auto";
  }

  // --- Multi-Step Form Navigation ---
  let citizenAuthToken = null;

  function goToFormStep(stepNum) {
    [1, 2, 3, 4].forEach(s => {
      const panel = document.getElementById(`form-step-${s}`);
      const dot = document.getElementById(`step-dot-${s}`);

      if (s === stepNum) {
        panel.classList.remove("hidden");
        dot.classList.add("active");
        dot.classList.remove("completed");
      } else {
        panel.classList.add("hidden");
        dot.classList.remove("active");
        if (s < stepNum) dot.classList.add("completed");
      }
    });
    if (window.lucide) lucide.createIcons();
  }

  // --- STEP 1: Aadhaar e-KYC Verification ---
  const modalSendOtpBtn = document.getElementById("modal-send-otp-btn");
  const modalVerifyOtpBtn = document.getElementById("modal-verify-otp-btn");
  const modalOtpGroup = document.getElementById("modal-otp-group");
  const modalOtpStatus = document.getElementById("modal-otp-status-msg");
  const modalAadhaarInput = document.getElementById("modal-aadhaar-input");
  const modalOtpDigits = document.querySelectorAll(".modal-otp-digit");

  // Auto-focus next input in OTP boxes
  modalOtpDigits.forEach((input, idx) => {
    input.addEventListener("input", (e) => {
      if (e.target.value.length === 1 && idx < modalOtpDigits.length - 1) {
        modalOtpDigits[idx + 1].focus();
      }
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !e.target.value && idx > 0) {
        modalOtpDigits[idx - 1].focus();
      }
    });
  });

  modalSendOtpBtn.addEventListener("click", async () => {
    const rawAadhaar = modalAadhaarInput.value.replace(/\s+/g, "");
    if (rawAadhaar.length !== 12 || !/^\d+$/.test(rawAadhaar)) {
      alert("Please enter a valid 12-digit Aadhaar number.");
      return;
    }

    modalSendOtpBtn.disabled = true;
    modalSendOtpBtn.innerHTML = "<span>Dispatching UIDAI OTP...</span>";

    try {
      const res = await fetch("/api/citizen/auth/request-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aadhaar_number: rawAadhaar })
      });
      const data = await res.json();

      if (res.ok) {
        modalOtpGroup.classList.remove("hidden");
        modalSendOtpBtn.classList.add("hidden");
        modalVerifyOtpBtn.classList.remove("hidden");
        modalOtpStatus.textContent = `✓ OTP sent to Aadhaar mobile [Demo Code: ${data.demo_otp_hint}]`;

        // Auto-fill demo OTP for student demo convenience
        if (data.demo_otp_hint) {
          const chars = data.demo_otp_hint.split("");
          modalOtpDigits.forEach((digitBox, i) => {
            digitBox.value = chars[i] || "";
          });
        }
        modalOtpDigits[0].focus();
      } else {
        alert(data.detail || "Failed to generate OTP.");
        modalSendOtpBtn.disabled = false;
        modalSendOtpBtn.innerHTML = "<i data-lucide='send'></i><span>Send Aadhaar OTP</span>";
        if (window.lucide) lucide.createIcons();
      }
    } catch (err) {
      alert("Network error connecting to verification gateway.");
      modalSendOtpBtn.disabled = false;
      modalSendOtpBtn.innerHTML = "<span>Retry OTP</span>";
    }
  });

  modalVerifyOtpBtn.addEventListener("click", async () => {
    const rawAadhaar = modalAadhaarInput.value.replace(/\s+/g, "");
    let enteredOtp = "";
    modalOtpDigits.forEach(d => enteredOtp += d.value);

    if (enteredOtp.length !== 6) {
      alert("Please enter the complete 6-digit OTP.");
      return;
    }

    modalVerifyOtpBtn.disabled = true;
    modalVerifyOtpBtn.innerHTML = "<span>Verifying e-KYC...</span>";

    try {
      const res = await fetch("/api/citizen/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ aadhaar_number: rawAadhaar, otp_code: enteredOtp })
      });
      const data = await res.json();

      if (res.ok) {
        citizenAuthToken = data.token;
        goToFormStep(2);
      } else {
        alert(data.detail || "Incorrect OTP entered.");
        modalVerifyOtpBtn.disabled = false;
        modalVerifyOtpBtn.innerHTML = "<span>Verify OTP & Proceed</span>";
      }
    } catch (err) {
      alert("Error verifying OTP code.");
      modalVerifyOtpBtn.disabled = false;
    }
  });

  // --- STEP 2: Complainant Details ---
  const modalStep2Back = document.getElementById("modal-step2-back");
  const modalStep2Next = document.getElementById("modal-step2-next");

  modalStep2Back.addEventListener("click", () => goToFormStep(1));
  modalStep2Next.addEventListener("click", () => {
    const name = document.getElementById("modal-victim-name").value.trim();
    const phone = document.getElementById("modal-victim-phone").value.trim();
    const account = document.getElementById("modal-victim-account").value.trim();
    const city = document.getElementById("modal-victim-city").value.trim();
    const state = document.getElementById("modal-victim-state").value.trim();

    if (!name || !phone || !account || !city || !state) {
      alert("Please fill in all mandatory fields.");
      return;
    }
    goToFormStep(3);
  });

  // --- STEP 3: Incident Details & Submission ---
  const modalStep3Back = document.getElementById("modal-step3-back");
  const modalSubmitBtn = document.getElementById("modal-submit-complaint-btn");

  modalStep3Back.addEventListener("click", () => goToFormStep(2));

  modalSubmitBtn.addEventListener("click", async () => {
    const amount = parseFloat(document.getElementById("modal-fraud-amount").value);
    const category = document.getElementById("modal-crime-category").value;
    const scammer = document.getElementById("modal-scammer-account").value.trim();
    const desc = document.getElementById("modal-incident-desc").value.trim();

    if (isNaN(amount) || amount <= 0 || !desc) {
      alert("Please enter a valid defrauded amount and narrative description.");
      return;
    }

    modalSubmitBtn.disabled = true;
    modalSubmitBtn.innerHTML = "<span>Transmitting & Running AI Trajectory Model...</span>";

    const payload = {
      victim_name: document.getElementById("modal-victim-name").value.trim(),
      victim_phone: document.getElementById("modal-victim-phone").value.trim(),
      victim_account: document.getElementById("modal-victim-account").value.trim(),
      reported_amount: amount,
      city: document.getElementById("modal-victim-city").value.trim(),
      state: document.getElementById("modal-victim-state").value.trim(),
      crime_type: category,
      scammer_contact: scammer,
      scammer_upi_or_account: scammer,
      incident_description: desc
    };

    try {
      const headers = { "Content-Type": "application/json" };
      if (citizenAuthToken) headers["Authorization"] = `Bearer ${citizenAuthToken}`;

      const res = await fetch("/api/citizen/complaints", {
        method: "POST",
        headers: headers,
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok) {
        // Display Official Acknowledgment Slip (Step 4)
        document.getElementById("modal-ack-id-display").textContent = data.complaint_id;
        document.getElementById("slip-name").textContent = payload.victim_name;
        document.getElementById("slip-amount").textContent = `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
        document.getElementById("slip-predicted-zone").textContent = `${data.case_summary.predicted_city} (Nearest ATM: ${data.case_summary.nearest_atm})`;

        // Copy button setup
        document.getElementById("modal-copy-ack-btn").onclick = () => {
          navigator.clipboard.writeText(data.complaint_id);
          alert(`Copied Acknowledgment Number: ${data.complaint_id}`);
        };

        // Track Now button
        document.getElementById("modal-track-now-btn").onclick = () => {
          closeComplaintModal();
          const trackInput = document.getElementById("track-ack-number");
          trackInput.value = data.complaint_id;
          document.getElementById("track-section").scrollIntoView({ behavior: "smooth" });
          document.getElementById("track-submit-btn").click();
        };

        goToFormStep(4);
      } else {
        alert(data.detail || "Failed to register complaint.");
        modalSubmitBtn.disabled = false;
        modalSubmitBtn.innerHTML = "<span>Submit & Transmit Complaint</span>";
      }
    } catch (err) {
      alert("Submission Error: " + (err.message || "Could not connect to NCRP gateway."));
      modalSubmitBtn.disabled = false;
      modalSubmitBtn.innerHTML = "<span>Submit & Transmit Complaint</span>";
    }
  });

  // --- SECTION 2: Tracking Existing Complaint ---
  const trackSubmitBtn = document.getElementById("track-submit-btn");
  const trackAckNumberInput = document.getElementById("track-ack-number");
  const trackingResultBox = document.getElementById("tracking-result-box");

  trackSubmitBtn.addEventListener("click", async () => {
    const ackNo = trackAckNumberInput.value.trim();
    if (!ackNo) {
      alert("Please enter a valid NCRP Acknowledgment Number.");
      return;
    }

    try {
      const res = await fetch(`/api/citizen/complaints/track/${encodeURIComponent(ackNo)}`);
      if (res.ok) {
        const caseData = await res.json();
        renderCaseTracking(caseData);
      } else {
        alert("No active case record found for this Acknowledgment Number.");
      }
    } catch (err) {
      alert("Error retrieving case status from Sentinel database.");
    }
  });

  function renderCaseTracking(caseData) {
    trackingResultBox.classList.remove("hidden");

    document.getElementById("res-ack-id").textContent = caseData.complaint_id;
    document.getElementById("res-victim-name").textContent = caseData.victim_name;
    document.getElementById("res-amount").textContent = `₹${caseData.reported_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById("res-crime-type").textContent = caseData.crime_type;
    document.getElementById("res-registered-at").textContent = caseData.registered_at;

    const statusBadge = document.getElementById("res-status-badge");
    statusBadge.textContent = caseData.status.replace(/_/g, " ");

    if (caseData.status.includes("FROZEN") || caseData.status.includes("SECURED")) {
      statusBadge.className = "status-pill frozen";
    } else {
      statusBadge.className = "status-pill live";
    }

    // Render Timeline Steps
    const timelineEl = document.getElementById("res-timeline");
    timelineEl.innerHTML = "";

    const actions = caseData.actions_timeline || [];
    actions.forEach((act, idx) => {
      const isLatest = idx === actions.length - 1;
      const stepDiv = document.createElement("div");
      stepDiv.className = `gov-timeline-step ${isLatest ? 'latest' : ''}`;
      stepDiv.innerHTML = `
        <div class="timeline-marker"></div>
        <div class="timeline-content-box">
          <div class="timeline-top-row">
            <span class="timeline-action-title">${act.action}</span>
            <span class="timeline-action-meta">${act.timestamp} (${act.operator})</span>
          </div>
          <p class="timeline-action-details">${act.details}</p>
        </div>
      `;
      timelineEl.appendChild(stepDiv);
    });

    if (window.lucide) lucide.createIcons();
    trackingResultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
});
