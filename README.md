# 🌤️ Weather Context AI

> **An Intelligent Meteorological Companion for Health, Agriculture & Daily Living**  
> Translating complex, quantitative meteorological metrics into real-time, qualitative guidance powered by a deterministic **Rule Engine** and **Google Gemini AI**.

---

## 📌 Architecture & System Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                  │
│   • HTML5 Geolocation API  /  Global City Search Bar                  │
│   • Glassmorphic Dashboard with Live Ambient Visual Meters             │
│   • Interactive "Aero" AI Chatbot (Multi-Turn Conversational Memory)   │
│   • Text-to-Speech (Web Speech API) & Smart Error Suggestion Cards     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ fetch() JSON
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND (main.py)                       │
│   • Asynchronous Request Routing & CORS Middleware                     │
│   • API Rate Limiting (slowapi: 10 chat requests/min per IP)          │
│   • Secure Server-Side API Key Concealment                             │
└──────────┬────────────────────────┬───────────────────────┬────────────┘
           │                        │                       │
           ▼                        ▼                       ▼
 ┌───────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
 │   WeatherAPI.com  │    │   Rule Engine    │    │   Google Gemini AI   │
 │   Raw Metrics     │    │   (Deterministic │    │   Qualitative        │
 │   • Temp / Feels  │    │   if/else logic) │    │   Advisory & Aero    │
 │   • AQI (EPA/PM)  │    │   • Health       │    │   Contextual Chat    │
 │   • Rain / UV     │    │   • Agriculture  │    └──────────┬───────────┘
 └───────────────────┘    │   • Lifestyle    │               │
                          └──────────────────┘               ▼
                                                  ┌──────────────────────┐
                                                  │     SQLite Cache     │
                                                  │   (30-minute TTL)    │
                                                  └──────────────────────┘
```

---

## ✨ Key Features

### 1. 🧠 Conversational AI Weather Assistant ("Aero")
* **Multi-Turn Context Memory**: Remembers your previous statements across the last 5 messages (e.g., if you say *"I'm growing wheat in Kota"*, and then ask *"Should I spray today?"*, Aero remembers your crop and evaluates the weather specifically for wheat).
* **Context-Aware Responses**: Directly integrates live temperature, precipitation chance, humidity, wind, and AQI into advice.

### 2. 🛡️ API Rate Limiting (`slowapi`)
* Prevents API quota exhaustion by limiting chat messages to **10 requests per minute per IP**.
* Emits a user-friendly cooldown response if the threshold is exceeded.

### 3. 🔍 Smart Error UI & AI City Suggestions
* If a user misspells or enters an unlisted city name (e.g., `Xyzqwerty123`), the app does not throw a raw 500 error.
* Instead, **Gemini generates friendly, clickable city suggestions** that can be searched with a single click.

### 4. ⚡ Deterministic Rule Engine
Runs before the LLM to provide immediate, zero-latency safety directives:
* **Health**: Hazardous AQI / PM2.5 alerts, N95 mask recommendations, extreme UV index warnings, heatstroke hydration alerts.
* **Agriculture**: Rain-based pesticide spray cancellation, wind-drift warnings, optimal spray windows, evapotranspiration irrigation advisories, frost protection alerts.
* **Lifestyle**: Downpour / umbrella alerts, gale-force wind warnings, dense fog / road safety advisories.

### 5. 🔊 Interactive Dashboard UX
* **Dual Location Modes**: One-click GPS auto-detection or instant city search worldwide.
* **Ambient Lighting & Live Meters**: Animated rain probability bars, humidity bars, and a 5-stage AQI hazard scale.
* **Text-to-Speech**: Listen to the Gemini advisory read aloud with a single click.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **Frontend** | HTML5, Modern CSS (Glassmorphism), Vanilla JavaScript | Responsive UI, Geolocation API, SpeechSynthesis |
| **Backend** | Python 3.10+, FastAPI, Uvicorn | High-performance asynchronous API orchestration |
| **Rate Limiter** | `slowapi` | In-memory token bucket rate limiting |
| **AI / LLM** | Google Gemini 3.1 Flash / 3.5 Flash | Qualitative synthesis & conversational companion |
| **Weather Engine** | WeatherAPI.com | Hyper-local raw forecast and air quality metrics |
| **Caching Engine** | SQLite (WAL mode) | 30-minute TTL caching of LLM outputs |

---

## 🚀 Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/himanshupaliwal000444-cyber/WEATHER-CONTEXT-AI.git
cd WEATHER-CONTEXT-AI
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
WEATHERAPI_KEY=your_weatherapi_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application

**Option A — One-Click (Windows):**
Double-click `run.bat` in the project folder.

**Option B — Terminal:**
```bash
python -m uvicorn main:app --reload --port 8000
```

Open your browser at: **http://localhost:8000**

---

## 📁 Project Structure

```
WEATHER-CONTEXT-AI/
├── main.py                  # FastAPI server, rule engine, Gemini calls, rate limiting
├── requirements.txt         # Project dependencies (FastAPI, uvicorn, slowapi, etc.)
├── Procfile                 # Cloud deployment instructions (Render/Railway)
├── run.bat                  # One-click Windows runner
├── .env.example             # Template for API credentials
├── .gitignore               # Ignores sensitive .env and database files
├── README.md                # Project documentation
└── static/
    ├── index.html           # Semantic, accessible dashboard interface
    ├── style.css            # Glassmorphism styling, ambient lighting & animations
    └── app.js               # Geolocation, chat memory, search & DOM controller
```

---

## 🌐 Cloud Deployment (Render.com)

1. Push your code to GitHub:
   ```bash
   git add .
   git commit -m "Update"
   git push origin main
   ```
2. Connect your GitHub repository to [Render](https://render.com) as a **Web Service**.
3. Set the following build options:
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add your `WEATHERAPI_KEY` and `GEMINI_API_KEY` under **Environment Variables**.
5. Deploy! Render will provide your public HTTPS URL automatically.

---

## 👨‍💻 Author & Academic Details

* **Project Title:** Weather Context AI
* **Student Name:** Himanshu Paliwal
* **Enrollment No.:** K26760
* **Course / Branch:** B.Tech / CSE (3rd Semester)
* **Institution:** Career Point University
* **Project Guide:** Mr. Harsh Verma (Assistant Professor)
