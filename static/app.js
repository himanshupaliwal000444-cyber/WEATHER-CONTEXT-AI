/**
 * Weather Context AI — Modern Interactive Controller V3
 * ======================================================
 * Enhancements:
 * - Chat Memory: Last 5 messages sent to Gemini for multi-turn context
 * - Rate Limit UX: Friendly cooldown message when limit hit
 * - Smart Error UI: AI city suggestions instead of raw error messages
 */

(function () {
    "use strict";

    // ── Global State ──
    let activeWeatherData = null;
    let currentAlerts = [];
    let chatHistory = []; // Conversational memory: array of {role, text}

    // ── DOM Elements ──
    const searchForm = document.getElementById("search-form");
    const cityInput = document.getElementById("city-input");
    const btnLocate = document.getElementById("btn-locate");
    const locationLabel = document.getElementById("location-label");
    const localTimeEl = document.getElementById("local-time");
    const loader = document.getElementById("loader");
    const errorBanner = document.getElementById("error-banner");
    const dashboard = document.getElementById("dashboard");

    // Weather Hero
    const weatherIcon = document.getElementById("weather-icon");
    const tempValue = document.getElementById("temp-value");
    const weatherCondition = document.getElementById("weather-condition");
    const feelslike = document.getElementById("feelslike");
    const humidity = document.getElementById("humidity");
    const wind = document.getElementById("wind");
    const uv = document.getElementById("uv");
    const visibility = document.getElementById("visibility");
    const metricPressure = document.getElementById("metric-pressure");

    // Forecast
    const highlow = document.getElementById("highlow");
    const minTempLabel = document.getElementById("min-temp-label");
    const maxTempLabel = document.getElementById("max-temp-label");
    const rainChance = document.getElementById("rain-chance");
    const rainBar = document.getElementById("rain-bar");
    const precip = document.getElementById("precip");
    const avgHumidity = document.getElementById("avg-humidity");
    const humidityBar = document.getElementById("humidity-bar");

    // AQI
    const aqiBadge = document.getElementById("aqi-badge");
    const aqiSteps = document.querySelectorAll(".aqi-step");
    const pm25 = document.getElementById("pm25");
    const pm10 = document.getElementById("pm10");
    const co = document.getElementById("co");
    const no2 = document.getElementById("no2");
    const o3 = document.getElementById("o3");

    // AI Advisory
    const aiAdvisoryText = document.getElementById("ai-advisory");
    const btnSpeak = document.getElementById("btn-speak");
    const btnCopyAdvisory = document.getElementById("btn-copy-advisory");

    // Alerts
    const alertsCountBadge = document.getElementById("alerts-count-badge");
    const alertsList = document.getElementById("alerts-list");
    const filterBtns = document.querySelectorAll(".filter-btn");

    // Chatbot
    const chatToggleBtn = document.getElementById("chat-toggle-btn");
    const chatWindow = document.getElementById("chat-window");
    const chatCloseBtn = document.getElementById("chat-close-btn");
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatTyping = document.getElementById("chat-typing");
    const suggestionChips = document.querySelectorAll(".suggestion-chip");
    const cityChips = document.querySelectorAll(".city-chip");

    // ── UI Helpers ──
    function showLoading() {
        loader.classList.remove("hidden");
        dashboard.classList.add("hidden");
        errorBanner.classList.add("hidden");
    }

    function hideLoading() {
        loader.classList.add("hidden");
    }

    /**
     * Smart Error Display: Shows AI-generated city suggestions
     * when a city is not found, with clickable suggestion links.
     */
    function showError(msg, errorType) {
        hideLoading();

        if (errorType === "city_not_found") {
            // Parse AI suggestion text: look for lines starting with "•" or "-"
            const lines = msg.split("\n");
            let html = "";

            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
                    // Extract city name (strip bullet and clean up)
                    const cityName = trimmed.replace(/^[•\-]\s*/, "").trim();
                    // Make it a clickable suggestion button
                    html += `<div class="suggestion-city" onclick="window.__searchCity('${cityName.replace(/'/g, "\\'")}')">`
                        + `<span class="suggestion-bullet">→</span> ${cityName}`
                        + `</div>`;
                } else if (trimmed) {
                    html += `<div>${trimmed}</div>`;
                }
            }

            errorBanner.innerHTML = `
                <div class="error-smart">
                    <div class="error-smart__header">🤖 Aero couldn't find that location</div>
                    <div class="error-smart__body">${html}</div>
                    <div class="error-smart__hint">Click any suggestion above to search it instantly.</div>
                </div>
            `;
        } else {
            errorBanner.innerHTML = `<div>⚠️ ${msg}</div>`;
        }

        errorBanner.classList.remove("hidden");
    }

    // Expose search function globally for inline onclick handlers
    window.__searchCity = function (cityName) {
        cityInput.value = cityName;
        fetchWeatherByQuery(cityName);
    };

    // ── AQI Visuals ──
    function updateAqiVisuals(epaIndex) {
        const aqiMap = {
            1: { text: "Good", cls: "aqi-pill--good" },
            2: { text: "Moderate", cls: "aqi-pill--moderate" },
            3: { text: "Unhealthy for Sensitive", cls: "aqi-pill--unhealthy" },
            4: { text: "Unhealthy", cls: "aqi-pill--unhealthy" },
            5: { text: "Hazardous", cls: "aqi-pill--hazardous" },
            6: { text: "Hazardous", cls: "aqi-pill--hazardous" },
        };

        const config = aqiMap[epaIndex] || { text: "Moderate", cls: "aqi-pill--moderate" };
        aqiBadge.textContent = `EPA ${epaIndex || 1} • ${config.text}`;
        aqiBadge.className = `aqi-pill ${config.cls}`;

        const stepNum = Math.min(Math.max(epaIndex || 1, 1), 5);
        aqiSteps.forEach((step) => {
            const lvl = parseInt(step.dataset.level, 10);
            step.classList.toggle("active", lvl === stepNum);
        });
    }

    // ── Render Weather ──
    function renderWeather(data) {
        activeWeatherData = data;
        const { location, current, forecast, air_quality, alerts, ai_advisory } = data;

        locationLabel.innerHTML = `📍 <strong>${location.name}</strong>, ${location.region ? location.region + ", " : ""}${location.country}`;
        localTimeEl.textContent = location.localtime ? `Local Time: ${location.localtime}` : "";

        weatherIcon.src = current.condition_icon.startsWith("//")
            ? "https:" + current.condition_icon
            : current.condition_icon;
        weatherIcon.alt = current.condition;
        tempValue.textContent = Math.round(current.temp_c);
        weatherCondition.textContent = current.condition;
        feelslike.textContent = `${Math.round(current.feelslike_c)}°C`;
        humidity.textContent = `${current.humidity}%`;
        wind.textContent = `${Math.round(current.wind_kph)} km/h ${current.wind_dir}`;
        uv.textContent = current.uv;
        visibility.textContent = `${current.vis_km} km`;
        metricPressure.textContent = `${current.pressure_mb} mb`;

        highlow.textContent = `${Math.round(forecast.maxtemp_c)}° / ${Math.round(forecast.mintemp_c)}°C`;
        minTempLabel.textContent = `${Math.round(forecast.mintemp_c)}°C`;
        maxTempLabel.textContent = `${Math.round(forecast.maxtemp_c)}°C`;

        const rainVal = forecast.rain_chance || 0;
        rainChance.textContent = `${rainVal}%`;
        rainBar.style.width = `${Math.min(rainVal, 100)}%`;
        precip.textContent = `${forecast.totalprecip_mm || 0} mm`;

        const humVal = forecast.avghumidity || current.humidity || 0;
        avgHumidity.textContent = `${humVal}%`;
        humidityBar.style.width = `${Math.min(humVal, 100)}%`;

        updateAqiVisuals(air_quality.us_epa_index);
        pm25.textContent = air_quality.pm2_5;
        pm10.textContent = air_quality.pm10;
        co.textContent = air_quality.co;
        no2.textContent = air_quality.no2;
        o3.textContent = air_quality.o3;

        aiAdvisoryText.textContent = ai_advisory;

        currentAlerts = alerts || [];
        alertsCountBadge.textContent = `${currentAlerts.length} Directives`;
        renderAlerts("all");

        hideLoading();
        dashboard.classList.remove("hidden");
    }

    // ── Render Alerts ──
    function renderAlerts(filter) {
        const filtered =
            filter === "all"
                ? currentAlerts
                : currentAlerts.filter((a) => a.category === filter);

        if (filtered.length === 0) {
            alertsList.innerHTML =
                '<p class="alerts-list__empty">✅ No adverse alerts for this category. Conditions are optimal.</p>';
            return;
        }

        alertsList.innerHTML = filtered
            .map(
                (a) => `
            <div class="alert-item alert-item--${a.type}">
                <span class="alert-item__icon">${a.icon}</span>
                <div class="alert-item__body">
                    <div class="alert-item__title-row">
                        <span class="alert-item__title">${a.title || a.category.toUpperCase()}</span>
                        <span class="alert-item__category">${a.category}</span>
                    </div>
                    <p class="alert-item__message">${a.message}</p>
                </div>
            </div>
        `
            )
            .join("");
    }

    // ── Fetch Weather ──
    async function fetchWeatherByQuery(queryStr) {
        showLoading();
        try {
            const resp = await fetch(`/api/weather?q=${encodeURIComponent(queryStr)}`);
            const data = await resp.json();

            if (!resp.ok) {
                // Smart error: check if it's a city_not_found with AI suggestions
                if (data.error_type === "city_not_found") {
                    showError(data.detail, "city_not_found");
                } else {
                    showError(data.detail || `Server error (${resp.status})`);
                }
                return;
            }

            renderWeather(data);
        } catch (err) {
            showError(err.message);
        }
    }

    async function fetchWeatherByCoords(lat, lon) {
        showLoading();
        try {
            const resp = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                throw new Error(errData.detail || `Server status ${resp.status}`);
            }
            const data = await resp.json();
            renderWeather(data);
        } catch (err) {
            showError(err.message);
        }
    }

    // ── Geolocation ──
    function handleLocate() {
        if (!navigator.geolocation) {
            showError("Geolocation is not supported by your browser.");
            return;
        }
        btnLocate.disabled = true;
        locationLabel.textContent = "📡 Acquiring GPS coordinates...";

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                btnLocate.disabled = false;
                fetchWeatherByCoords(pos.coords.latitude, pos.coords.longitude);
            },
            (err) => {
                btnLocate.disabled = false;
                const errMap = {
                    1: "Location access denied. Search a city manually above.",
                    2: "Location unavailable. Please check device GPS.",
                    3: "Location request timed out. Please retry.",
                };
                showError(errMap[err.code] || "Could not detect location.");
            },
            { enableHighAccuracy: false, timeout: 10000 }
        );
    }

    // ── TTS & Copy ──
    function speakAdvisory() {
        if (!("speechSynthesis" in window)) {
            alert("Speech synthesis is not supported on your browser.");
            return;
        }
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(aiAdvisoryText.textContent);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }

    function copyAdvisory() {
        navigator.clipboard.writeText(aiAdvisoryText.textContent).then(() => {
            btnCopyAdvisory.textContent = "✅ Copied!";
            setTimeout(() => {
                btnCopyAdvisory.innerHTML = '<span class="action-icon">📋</span> Copy';
            }, 2000);
        });
    }

    // ──────────────────────────────────────────
    //  Chatbot with Conversational Memory
    // ──────────────────────────────────────────
    function appendChatMessage(sender, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `chat-msg chat-msg--${sender}`;
        msgDiv.innerHTML = `<div class="chat-msg__bubble">${text}</div>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendUserMessage(msgText) {
        if (!msgText.trim()) return;

        appendChatMessage("user", msgText);
        chatInput.value = "";

        // Add to conversation memory
        chatHistory.push({ role: "user", text: msgText });

        // Show typing
        chatTyping.classList.remove("hidden");
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const resp = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: msgText,
                    history: chatHistory.slice(-5), // Send last 5 messages for memory
                    weather_context: activeWeatherData,
                }),
            });

            if (resp.status === 429) {
                // Rate limit hit
                chatTyping.classList.add("hidden");
                appendChatMessage(
                    "bot",
                    "⏳ <strong>Whoa, slow down!</strong> You've hit the rate limit (10 messages/minute). " +
                    "Please wait a moment and try again. This protects our AI quota so the service stays free for everyone! 🙏"
                );
                return;
            }

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || "Unable to reach Aero.");
            }

            const data = await resp.json();
            chatTyping.classList.add("hidden");

            // Add bot reply to memory
            chatHistory.push({ role: "bot", text: data.reply });

            appendChatMessage("bot", data.reply);
        } catch (err) {
            chatTyping.classList.add("hidden");
            appendChatMessage("bot", `⚠️ ${err.message}`);
        }
    }

    // ── Event Listeners ──
    searchForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const val = cityInput.value.trim();
        if (val) fetchWeatherByQuery(val);
    });

    btnLocate.addEventListener("click", handleLocate);

    cityChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const city = chip.dataset.city;
            cityInput.value = city;
            fetchWeatherByQuery(city);
        });
    });

    filterBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            filterBtns.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            renderAlerts(btn.dataset.filter);
        });
    });

    btnSpeak.addEventListener("click", speakAdvisory);
    btnCopyAdvisory.addEventListener("click", copyAdvisory);

    chatToggleBtn.addEventListener("click", () => {
        chatWindow.classList.toggle("hidden");
        if (!chatWindow.classList.contains("hidden")) chatInput.focus();
    });

    chatCloseBtn.addEventListener("click", () => {
        chatWindow.classList.add("hidden");
    });

    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        sendUserMessage(chatInput.value);
    });

    suggestionChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            sendUserMessage(chip.dataset.prompt);
        });
    });

    // ── Initial Load ──
    fetchWeatherByQuery("Kota");
})();
