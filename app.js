// Interactive Application Logic for ML Inefficient Code Detector

document.addEventListener("DOMContentLoaded", () => {
    const codeEditor = document.getElementById("codeEditor");
    const thresholdSlider = document.getElementById("thresholdSlider");
    const thresholdDisplay = document.getElementById("thresholdDisplay");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const resultsContainer = document.getElementById("resultsContainer");
    const emptyResults = document.getElementById("emptyResults");
    const clearBtn = document.getElementById("clearBtn");
    const fileInput = document.getElementById("fileInput");
    const uploadBtn = document.getElementById("uploadBtn");
    const presetChips = document.querySelectorAll(".preset-chip");

    // Live update threshold percentage display
    if (thresholdSlider && thresholdDisplay) {
        thresholdSlider.addEventListener("input", (e) => {
            const val = Math.round(e.target.value * 100);
            thresholdDisplay.textContent = `${val}%`;
        });
    }

    // Preset chip selection
    presetChips.forEach(chip => {
        chip.addEventListener("click", async () => {
            presetChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");

            const presetKey = chip.getAttribute("data-preset");
            try {
                const res = await fetch(`/api/sample/${presetKey}`);
                if (res.ok) {
                    const data = await res.json();
                    codeEditor.value = data.code;
                    // Automatically trigger analysis on preset load
                    performAnalysis();
                }
            } catch (err) {
                console.error("Failed to load preset:", err);
            }
        });
    });

    // Clear editor button
    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            codeEditor.value = "";
            presetChips.forEach(c => c.classList.remove("active"));
            showEmptyState();
            codeEditor.focus();
        });
    }

    // Upload file trigger
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener("click", () => fileInput.click());
        fileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (event) => {
                codeEditor.value = event.target.result;
                presetChips.forEach(c => c.classList.remove("active"));
                performAnalysis();
            };
            reader.readAsText(file);
        });
    }

    // Analyze Button Click
    if (analyzeBtn) {
        analyzeBtn.addEventListener("click", () => {
            performAnalysis();
        });
    }

    // Keyboard shortcut: Ctrl + Enter / Cmd + Enter to run analysis
    codeEditor.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            performAnalysis();
        }
    });

    function showEmptyState() {
        if (resultsContainer) resultsContainer.style.display = "none";
        if (emptyResults) emptyResults.style.display = "flex";
    }

    async function performAnalysis() {
        const code = codeEditor.value.trim();
        if (!code) {
            alert("Please paste or type some C/C++ source code to analyze.");
            codeEditor.focus();
            return;
        }

        const threshold = parseFloat(thresholdSlider.value);

        // UI Loading state
        const originalBtnHTML = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = `
            <svg class="spin-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor"></path>
            </svg>
            Analyzing Code...
        `;
        analyzeBtn.disabled = true;

        try {
            const response = await fetch("/api/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, threshold })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || "Analysis failed");
            }

            const data = await response.json();
            renderResults(data);
        } catch (error) {
            alert(`Analysis Error: ${error.message}`);
        } finally {
            analyzeBtn.innerHTML = originalBtnHTML;
            analyzeBtn.disabled = false;
        }
    }

    function renderResults(data) {
        if (emptyResults) emptyResults.style.display = "none";
        if (resultsContainer) resultsContainer.style.display = "flex";

        const isIneff = data.is_inefficient;
        const banner = document.getElementById("predictionBanner");
        const bannerTag = document.getElementById("bannerTag");
        const bannerVerdict = document.getElementById("bannerVerdict");
        const bannerSubtext = document.getElementById("bannerSubtext");

        // Style Banner
        if (banner) {
            banner.className = `prediction-banner ${isIneff ? 'inefficient' : 'clean'}`;
        }

        if (bannerTag) {
            bannerTag.textContent = isIneff ? "CODE SMELL DETECTED" : "SUFFICIENT / OPTIMIZED";
        }

        if (bannerVerdict) {
            bannerVerdict.textContent = data.prediction;
        }

        if (bannerSubtext) {
            bannerSubtext.textContent = isIneff
                ? `Random Forest Model flagged this file as inefficient with ${data.risk_percentage}% risk confidence.`
                : `Random Forest Model detected no high-confidence inefficiency smells (${data.risk_percentage}% risk).`;
        }

        // Animate Radial Gauge Progress Meter
        const circleVal = document.getElementById("circleVal");
        const riskPercentageText = document.getElementById("riskPercentageText");
        const gaugeCaption = document.getElementById("gaugeCaption");

        if (riskPercentageText) {
            riskPercentageText.textContent = `${data.risk_percentage}%`;
        }

        if (gaugeCaption) {
            gaugeCaption.textContent = isIneff ? "High Risk" : "Low Risk";
        }

        if (circleVal) {
            const circumference = 2 * Math.PI * 34; // r=34 => ~213.6
            circleVal.style.strokeDasharray = circumference;
            const offset = circumference - (data.risk_percentage / 100) * circumference;
            circleVal.style.strokeDashoffset = offset;
        }

        // Static Heuristic Evidence List
        const evidenceList = document.getElementById("evidenceList");
        if (evidenceList) {
            evidenceList.innerHTML = "";
            if (data.evidence && data.evidence.length > 0) {
                data.evidence.forEach(item => {
                    const li = document.createElement("li");
                    const isClean = item.includes("clean") || item.includes("No strong heuristic");
                    const isDanger = item.includes("costly") || item.includes("Heap allocation");
                    const iconClass = isClean ? "check" : (isDanger ? "danger" : "warning");

                    li.className = `evidence-item ${iconClass}`;
                    li.innerHTML = `
                        <span class="evidence-icon">
                            ${isClean ? '✅' : (isDanger ? '⚠️' : '🔍')}
                        </span>
                        <span>${escapeHtml(item)}</span>
                    `;
                    evidenceList.appendChild(li);
                });
            }
        }

        // Actionable Recommendations
        const recommendText = document.getElementById("recommendText");
        if (recommendText) {
            recommendText.innerHTML = "";
            if (data.recommendations && data.recommendations.length > 0) {
                const ul = document.createElement("ul");
                ul.style.listStyle = "disc";
                ul.style.paddingLeft = "1.2rem";
                data.recommendations.forEach(r => {
                    const rli = document.createElement("li");
                    rli.textContent = r;
                    ul.appendChild(rli);
                });
                recommendText.appendChild(ul);
            }
        }

        // 13 Extracted Feature Metrics Grid
        const featuresGrid = document.getElementById("featuresGrid");
        if (featuresGrid && data.features) {
            featuresGrid.innerHTML = "";
            Object.entries(data.features).forEach(([key, value]) => {
                const tile = document.createElement("div");
                const isHighlight = (key === "costly_loop_call_count" && value > 0) ||
                                  (key === "repeated_expression_count" && value > 0) ||
                                  (key === "allocation_keyword_count" && value > 0);

                tile.className = `feature-tile ${isHighlight ? 'highlight' : ''}`;
                tile.innerHTML = `
                    <span class="feature-name" title="${key}">${formatFeatureName(key)}</span>
                    <span class="feature-value">${value}</span>
                `;
                featuresGrid.appendChild(tile);
            });
        }
    }

    function formatFeatureName(name) {
        return name
            .replace(/_count$/, '')
            .replace(/_/g, ' ');
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    // Auto-trigger default analysis on load
    performAnalysis();
});
