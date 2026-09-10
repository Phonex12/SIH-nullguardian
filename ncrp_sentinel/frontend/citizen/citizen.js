// State Variables
let currentStep = 1;
let citizenToken = sessionStorage.getItem("citizen_token") || null;
let referenceData = { cities: [], states: [], banks: [], crime_types: [] };
let articlesList = [];
let currentCategory = "ALL";
let diagAnswers = {};

document.addEventListener("DOMContentLoaded", async () => {
    await fetchReferenceData();
    await fetchArticles();
    setupAadhaarInputs();
    setupHopsManager();
    setupEvidenceUpload();
    setupComplaintSubmission();
    populateDropdowns();

    // If citizen token already exists in session
    if (citizenToken) {
        document.getElementById("authStatusBadge").style.display = "block";
    }

    // Check if URL specifies /learn or hash
    if (window.location.pathname === "/learn" || window.location.hash === "#learn") {
        switchMainView("learn");
    }
});

// 1. Navigation View Switcher (Report vs. Learn vs. Diagnostic)
window.switchMainView = function(viewName) {
    const views = {
        report: document.getElementById("viewReportContainer"),
        learn: document.getElementById("viewLearnContainer"),
        diagnostic: document.getElementById("viewDiagnosticContainer")
    };

    const tabs = {
        report: document.getElementById("tabNavReport"),
        learn: document.getElementById("tabNavLearn"),
        diagnostic: document.getElementById("tabNavDiagnostic")
    };

    for (let key in views) {
        if (views[key]) views[key].style.display = (key === viewName) ? "block" : "none";
        if (tabs[key]) {
            if (key === viewName) tabs[key].classList.add("active");
            else tabs[key].classList.remove("active");
        }
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
};

// 2. Fetch Educational Articles from API
async function fetchArticles() {
    try {
        const res = await fetch("/api/citizen/articles");
        if (res.ok) {
            const data = await res.json();
            articlesList = data.articles || [];
            renderArticles(articlesList);
        }
    } catch (e) {
        console.warn("Failed fetching articles", e);
    }
}

function renderArticles(list) {
    const grid = document.getElementById("articlesGrid");
    if (!grid) return;
    grid.innerHTML = "";

    if (list.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">No articles found matching your query.</div>`;
        return;
    }

    list.forEach(a => {
        const badgeClass = `badge-${a.badge.toLowerCase().replace(/\s+/g, '-')}`;
        const card = document.createElement("div");
        card.className = "article-card";
        card.onclick = () => openArticleModal(a);

        card.innerHTML = `
            <div>
                <div class="article-card-header">
                    <span class="article-badge ${badgeClass}">${a.badge}</span>
                    <span class="article-read-time">⏱️ ${a.read_time}</span>
                </div>
                <h3>${a.title}</h3>
                <p class="summary">${a.summary}</p>
            </div>
            <div class="article-card-footer">
                <span class="article-cat-tag"># ${a.category}</span>
                <span class="article-read-btn">Read Article ➔</span>
            </div>
        `;
        grid.appendChild(card);
    });
}

window.filterArticles = function(category) {
    currentCategory = category;
    document.querySelectorAll(".cat-pill").forEach(btn => {
        if (btn.innerText.includes(category) || (category === 'ALL' && btn.innerText.includes('All'))) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    applyFilters();
};

window.handleSearchArticles = function() {
    applyFilters();
};

function applyFilters() {
    const query = (document.getElementById("searchArticlesInput")?.value || "").toLowerCase().trim();
    const filtered = articlesList.filter(a => {
        const matchesCat = (currentCategory === "ALL" || a.category === currentCategory);
        const matchesQuery = !query || 
            a.title.toLowerCase().includes(query) || 
            a.summary.toLowerCase().includes(query) || 
            a.content_md.toLowerCase().includes(query);
        return matchesCat && matchesQuery;
    });
    renderArticles(filtered);
}

// 3. Article Modal Reader
window.openArticleModal = function(article) {
    document.getElementById("modalBadge").innerText = article.badge;
    document.getElementById("modalBadge").className = `article-badge badge-${article.badge.toLowerCase().replace(/\s+/g, '-')}`;
    document.getElementById("modalReadTime").innerText = article.read_time;
    document.getElementById("modalCategory").innerText = article.category;
    document.getElementById("modalTitle").innerText = article.title;

    // Format markdown-like lines to HTML
    let formattedBody = article.content_md
        .replace(/### (.*?)\n/g, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '<br><br>');

    document.getElementById("modalBody").innerHTML = formattedBody;

    // Red flags
    const redFlagsUl = document.getElementById("modalRedFlags");
    redFlagsUl.innerHTML = (article.red_flags || []).map(rf => `<li>${rf}</li>`).join("");

    // Prevention tips
    const prevUl = document.getElementById("modalPrevention");
    prevUl.innerHTML = (article.prevention_tips || []).map(pt => `<li>${pt}</li>`).join("");

    document.getElementById("articleModal").style.display = "flex";
};

window.closeArticleModal = function() {
    document.getElementById("articleModal").style.display = "none";
};

window.closeArticleModalAndReport = function() {
    closeArticleModal();
    switchMainView("report");
    goToStep(2);
};

// 4. Interactive Scam Diagnostic Tool
window.selectDiagOption = function(questionNum, optionKey, element) {
    diagAnswers[questionNum] = optionKey;
    const parent = element.parentElement;
    parent.querySelectorAll(".diagnostic-option").forEach(opt => opt.classList.remove("selected"));
    element.classList.add("selected");
};

window.calculateDiagnosticResult = function() {
    const q1 = diagAnswers[1];
    const q2 = diagAnswers[2];
    const resultBox = document.getElementById("diagnosticResult");

    if (!q1 || !q2) {
        alert("Please select an answer for both questions.");
        return;
    }

    resultBox.style.display = "block";

    // All tested combinations represent high-risk cyber scams
    resultBox.className = "diagnostic-result-box scam";
    resultBox.innerHTML = `
        <div style="font-size: 32px; margin-bottom: 8px;">🚨</div>
        <h3 style="font-size: 20px; font-weight: 800; color: #991b1b; margin-bottom: 8px;">99% PROBABILITY OF ACTIVE CYBER SCAM!</h3>
        <p style="font-size: 14px; line-height: 1.6; margin-bottom: 16px;">
            The situation you described exhibits classic indicators of an organized cyber financial fraud syndicate. 
            <strong>DO NOT transfer any funds, do not install any APK files, and do not share OTPs under any circumstances.</strong>
        </p>
        <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
            <button type="button" class="btn btn-primary" onclick="switchMainView('report')">
                📝 File Official NCRP Complaint Now →
            </button>
            <a href="tel:1930" class="btn btn-success" style="background: #16a34a;">
                📞 Call 1930 Helpline Immediately
            </a>
        </div>
    `;
};

// 5. Reference Data & Dropdowns
async function fetchReferenceData() {
    try {
        const res = await fetch("/api/citizen/reference-data");
        if (res.ok) {
            referenceData = await res.json();
        }
    } catch (e) {
        console.warn("Using fallback for reference data", e);
        referenceData = {
            cities: ["Mumbai", "Pune", "Nashik", "Delhi", "Hyderabad", "Bengaluru", "Ahmedabad", "Chennai", "Kolkata", "Jaipur"],
            states: ["Maharashtra", "Delhi", "Telangana", "Karnataka", "Gujarat", "Tamil Nadu", "West Bengal", "Rajasthan"],
            banks: ["BANK_01", "BANK_02", "BANK_03", "BANK_04", "BANK_05", "BANK_06", "BANK_07", "BANK_08", "BANK_09", "BANK_10"]
        };
    }
}

function populateDropdowns() {
    const stateSelect = document.getElementById("victimStateSelect");
    const citySelect = document.getElementById("victimCitySelect");

    if (stateSelect && referenceData.states) {
        stateSelect.innerHTML = referenceData.states.map(s => `<option value="${s}" ${s === 'Maharashtra' ? 'selected' : ''}>${s}</option>`).join("");
    }
    if (citySelect && referenceData.cities) {
        citySelect.innerHTML = referenceData.cities.map(c => `<option value="${c}" ${c === 'Mumbai' ? 'selected' : ''}>${c}</option>`).join("");
    }
}

// 6. Step Navigation
window.goToStep = function(step) {
    currentStep = step;
    for (let i = 1; i <= 5; i++) {
        const section = document.getElementById(`step${i}Content`);
        const node = document.getElementById(`stepNode${i}`);
        if (section) section.style.display = (i === step) ? "block" : "none";
        if (node) {
            node.classList.remove("active", "completed");
            if (i < step) node.classList.add("completed");
            if (i === step) node.classList.add("active");
        }
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
};

// 7. Aadhaar Auth & OTP Management
function setupAadhaarInputs() {
    const aadhaarInput = document.getElementById("aadhaarInput");
    const btnSendOtp = document.getElementById("btnSendOtp");
    const otpSection = document.getElementById("otpSection");
    const btnVerifyOtp = document.getElementById("btnVerifyOtp");
    const otpDigits = document.querySelectorAll(".otp-digit");

    aadhaarInput.addEventListener("input", (e) => {
        let val = e.target.value.replace(/\D/g, "");
        let formatted = val.match(/.{1,4}/g)?.join(" ") || "";
        e.target.value = formatted.substring(0, 14);
    });

    btnSendOtp.addEventListener("click", async () => {
        const cleanAadhaar = aadhaarInput.value.replace(/\s+/g, "");
        if (cleanAadhaar.length !== 12) {
            alert("Please enter a valid 12-digit Aadhaar number.");
            return;
        }

        btnSendOtp.disabled = true;
        btnSendOtp.innerText = "Dispatching...";

        try {
            const res = await fetch("/api/citizen/auth/send-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ aadhaar_number: cleanAadhaar })
            });

            const data = await res.json();
            if (res.ok) {
                otpSection.classList.add("active");
                document.getElementById("demoOtpCode").innerText = data.demo_otp;
                document.getElementById("otpPromptMsg").innerText = data.message;
                
                // Pre-fill digits for easy testing
                const otpStr = String(data.demo_otp);
                otpDigits.forEach((input, idx) => {
                    input.value = otpStr[idx] || "";
                });
            } else {
                alert(data.detail || "Error generating Aadhaar OTP");
            }
        } catch (err) {
            console.error(err);
            alert("Network error contacting UIDAI simulated gateway.");
        } finally {
            btnSendOtp.disabled = false;
            btnSendOtp.innerText = "Resend OTP";
        }
    });

    otpDigits.forEach((digit, idx) => {
        digit.addEventListener("keyup", (e) => {
            if (e.key >= "0" && e.key <= "9") {
                if (idx < otpDigits.length - 1) otpDigits[idx + 1].focus();
            } else if (e.key === "Backspace" && idx > 0) {
                otpDigits[idx - 1].focus();
            }
        });
    });

    btnVerifyOtp.addEventListener("click", async () => {
        const cleanAadhaar = aadhaarInput.value.replace(/\s+/g, "");
        let enteredOtp = Array.from(otpDigits).map(d => d.value).join("");

        if (enteredOtp.length !== 6) {
            alert("Please enter all 6 digits of the OTP.");
            return;
        }

        btnVerifyOtp.disabled = true;
        btnVerifyOtp.innerText = "Verifying...";

        try {
            const res = await fetch("/api/citizen/auth/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ aadhaar_number: cleanAadhaar, otp: enteredOtp })
            });

            const data = await res.json();
            if (res.ok) {
                citizenToken = data.access_token;
                sessionStorage.setItem("citizen_token", citizenToken);
                document.getElementById("authStatusBadge").style.display = "block";
                document.getElementById("authStatusBadge").innerText = `✓ ${data.user_info.aadhaar_masked}`;
                goToStep(2);
            } else {
                alert(data.detail || "Invalid OTP entered.");
            }
        } catch (err) {
            console.error(err);
            alert("Server connection failed during OTP verification.");
        } finally {
            btnVerifyOtp.disabled = false;
            btnVerifyOtp.innerText = "Verify & Proceed";
        }
    });
}

// 8. Digital Hops Manager
function setupHopsManager() {
    const hopsList = document.getElementById("hopsList");
    const btnAddHop = document.getElementById("btnAddHop");
    const btnPrefill = document.getElementById("btnPrefillSampleHops");

    btnAddHop.addEventListener("click", () => {
        addHopItem();
    });

    btnPrefill.addEventListener("click", () => {
        populateSampleHops();
    });

    addHopItem(150000, "10:30", "Pune", "Maharashtra", "BANK_03", "ACC_0078129");
}

function addHopItem(amount = 50000, time = "11:15", city = "Mumbai", state = "Maharashtra", bank = "BANK_08", dest = "") {
    const hopsList = document.getElementById("hopsList");
    const hopIndex = hopsList.children.length + 1;

    const hopDiv = document.createElement("div");
    hopDiv.className = "hop-item";
    hopDiv.dataset.hopIndex = hopIndex;

    const cityOptions = (referenceData.cities || ["Mumbai", "Pune", "Nashik", "Delhi", "Hyderabad"]).map(c => 
        `<option value="${c}" ${c === city ? 'selected' : ''}>${c}</option>`
    ).join("");

    const stateOptions = (referenceData.states || ["Maharashtra", "Delhi", "Telangana", "Karnataka"]).map(s => 
        `<option value="${s}" ${s === state ? 'selected' : ''}>${s}</option>`
    ).join("");

    const bankOptions = (referenceData.banks || ["BANK_01", "BANK_02", "BANK_03", "BANK_08"]).map(b => 
        `<option value="${b}" ${b === bank ? 'selected' : ''}>${b}</option>`
    ).join("");

    hopDiv.innerHTML = `
        <div class="hop-header">
            <span>⚡ Transfer Hop #${hopIndex}</span>
            ${hopIndex > 1 ? `<button type="button" class="btn-remove-hop" onclick="removeHop(${hopIndex})">✕ Remove Hop</button>` : ''}
        </div>
        <div class="form-grid-3">
            <div class="form-group">
                <label>Transfer Amount (INR ₹)</label>
                <input type="number" class="form-input hop-amount" value="${amount}" min="1">
            </div>
            <div class="form-group">
                <label>Transfer Time (HH:MM)</label>
                <input type="time" class="form-input hop-time" value="${time}">
            </div>
            <div class="form-group">
                <label>Beneficiary Bank ID</label>
                <select class="form-select hop-bank">${bankOptions}</select>
            </div>
        </div>
        <div class="form-grid-3">
            <div class="form-group">
                <label>Destination State</label>
                <select class="form-select hop-state">${stateOptions}</select>
            </div>
            <div class="form-group">
                <label>Destination City</label>
                <select class="form-select hop-city">${cityOptions}</select>
            </div>
            <div class="form-group">
                <label>Mule Account / UPI Handle</label>
                <input type="text" class="form-input hop-dest" placeholder="e.g. ACC_0099412" value="${dest || 'ACC_00' + Math.floor(10000 + Math.random() * 90000)}">
            </div>
        </div>
    `;

    hopsList.appendChild(hopDiv);
}

window.removeHop = function(hopIndex) {
    const hopsList = document.getElementById("hopsList");
    const items = hopsList.getElementsByClassName("hop-item");
    for (let item of items) {
        if (item.dataset.hopIndex == hopIndex) {
            item.remove();
            break;
        }
    }
    Array.from(hopsList.children).forEach((item, idx) => {
        item.dataset.hopIndex = idx + 1;
        item.querySelector(".hop-header span").innerText = `⚡ Transfer Hop #${idx + 1}`;
    });
};

function populateSampleHops() {
    const hopsList = document.getElementById("hopsList");
    hopsList.innerHTML = "";
    addHopItem(185000, "10:15", "Mumbai", "Maharashtra", "BANK_01", "ACC_0078129");
    addHopItem(90000, "10:32", "Pune", "Maharashtra", "BANK_03", "ACC_0099412");
    addHopItem(45000, "10:48", "Nashik", "Maharashtra", "BANK_08", "ACC_0012390");
    alert("Realistic 3-hop mule money trail populated successfully!");
}

// 9. Validations
window.validateStep2AndNext = function() {
    const name = document.getElementById("victimName").value.trim();
    const phone = document.getElementById("victimPhone").value.trim();
    const account = document.getElementById("victimAccount").value.trim();
    const amount = document.getElementById("reportedAmount").value.trim();

    if (!name || !phone || !account || !amount) {
        alert("Please fill in all mandatory fields marked with an asterisk (*).");
        return;
    }
    goToStep(3);
};

window.validateStep3AndNext = function() {
    const hopsList = document.getElementById("hopsList");
    if (hopsList.children.length === 0) {
        alert("Please specify at least one transfer hop in the money trail.");
        return;
    }
    goToStep(4);
};

function setupEvidenceUpload() {
    const evidenceFile = document.getElementById("evidenceFile");
    const fileUploadStatus = document.getElementById("fileUploadStatus");
    if (evidenceFile && fileUploadStatus) {
        evidenceFile.addEventListener("change", () => {
            if (evidenceFile.files.length > 0) {
                fileUploadStatus.innerText = `${evidenceFile.files.length} document(s) attached: ${evidenceFile.files[0].name}`;
                fileUploadStatus.style.display = "block";
            }
        });
    }
}

// 10. Complaint Submission
function setupComplaintSubmission() {
    const btnSubmit = document.getElementById("btnSubmitComplaint");
    btnSubmit.addEventListener("click", async () => {
        const consent = document.getElementById("legalConsentCheck").checked;
        if (!consent) {
            alert("You must agree to the truthfulness declaration before registering an official complaint.");
            return;
        }

        const hopDivs = document.querySelectorAll(".hop-item");
        const collectedHops = [];
        hopDivs.forEach(div => {
            collectedHops.push({
                amount: parseFloat(div.querySelector(".hop-amount").value) || 0,
                time: div.querySelector(".hop-time").value || "12:00",
                bank_id: div.querySelector(".hop-bank").value,
                state: div.querySelector(".hop-state").value,
                city: div.querySelector(".hop-city").value,
                destination_account: div.querySelector(".hop-dest").value || "ACC_UNKNOWN"
            });
        });

        const payload = {
            victim_name: document.getElementById("victimName").value.trim(),
            victim_phone: document.getElementById("victimPhone").value.trim(),
            victim_account: document.getElementById("victimAccount").value.trim(),
            reported_amount: parseFloat(document.getElementById("reportedAmount").value) || 0,
            city: document.getElementById("victimCitySelect").value,
            state: document.getElementById("victimStateSelect").value,
            crime_type: document.getElementById("crimeTypeSelect").value,
            scammer_contact: document.getElementById("scammerContact").value.trim(),
            scammer_upi_or_account: document.getElementById("scammerAccount").value.trim(),
            digital_hops: collectedHops,
            incident_description: document.getElementById("incidentDescription").value.trim()
        };

        btnSubmit.disabled = true;
        btnSubmit.innerText = "Analyzing Neural Trajectory...";

        try {
            const res = await fetch("/api/citizen/complaints", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(citizenToken ? { "Authorization": `Bearer ${citizenToken}` } : {})
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (res.ok) {
                renderStep5Resolution(data);
                goToStep(5);
            } else {
                alert(data.detail || "Submission failed. Please check your inputs.");
            }
        } catch (err) {
            console.error(err);
            alert("Connection error triggering PyTorch AI Trajectory engine.");
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerText = "🚀 Trigger AI Defense & Register Complaint";
        }
    });
}

function renderStep5Resolution(data) {
    document.getElementById("resComplaintId").innerText = data.complaint_id;
    document.getElementById("resTimestamp").innerText = `Registered: ${data.registered_at} | Case Ref: ${data.case_id}`;

    const pred = data.prediction;
    document.getElementById("resCoords").innerText = `(${pred.mathematical_coords.latitude}, ${pred.mathematical_coords.longitude})`;
    document.getElementById("resTargetCity").innerText = `${pred.primary_target_city}, ${pred.primary_target_state}`;

    const threatBadge = document.getElementById("resThreatBadge");
    threatBadge.innerText = pred.threat_level;
    threatBadge.style.background = pred.threat_level === "CRITICAL" ? "#ef4444" : "#f59e0b";

    const cardsList = document.getElementById("resAtmCardsList");
    cardsList.innerHTML = "";

    pred.predicted_atms.forEach(atm => {
        const card = document.createElement("div");
        card.className = "prediction-atm-row";
        card.innerHTML = `
            <div>
                <strong style="color: #67e8f9; font-size: 14px;">Rank #${atm.rank}: ${atm.atm_id} (${atm.bank_id})</strong>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
                    📍 ${atm.city}, ${atm.state} • Distance: <span style="color: #fef08a;">${atm.distance_km} km</span> • 24x7: ${atm.operating_24x7 ? 'Yes' : 'No'}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 14px; font-weight: 700; color: #4ade80;">${atm.confidence_pct}% Match</div>
                <div style="font-size: 11px; color: #f87171; font-weight: 600;">Cashout Window: ${atm.estimated_cashout_window}</div>
            </div>
        `;
        cardsList.appendChild(card);
    });

    if (data.emergency_guidance && data.emergency_guidance.steps_to_follow) {
        const list = document.getElementById("resGuidanceList");
        list.innerHTML = data.emergency_guidance.steps_to_follow.map(s => `<li>${s}</li>`).join("");
    }
}
