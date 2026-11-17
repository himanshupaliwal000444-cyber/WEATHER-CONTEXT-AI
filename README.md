# 🌤️ Weather Context AI

**AI-powered weather web application** that translates complex, quantitative weather forecasts into real-time, qualitative guidance for **health**, **agriculture**, and **daily lifestyle**.

## Architecture

```
┌─────────────┐    HTML5 Geolocation    ┌──────────────┐
│   Browser   │ ──── fetch() ──────────▶│  FastAPI      │
│  (HTML/CSS  │                         │  Backend      │
│   /JS)      │◀──── JSON response ─────│  (main.py)    │
└─────────────┘                         └──────┬───────┘
                                               │
                              ┌─────────────────┼─────────────────┐
                              ▼                 ▼                 ▼
                      ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
                      │ WeatherAPI   │  │ Rule Engine  │  │ Gemini 1.5   │
                      │ (raw data)   │  │ (if/else)    │  │ Flash (LLM)  │
                      └──────────────┘  └─────────────┘  └──────────────┘
                                                                │
                                                         ┌──────────────┐
                                                         │ SQLite Cache │
                                                         │ (30-min TTL) │
                                                         └──────────────┘
```

## Quick Start

### 1. Get API Keys

| Service | URL | Plan |
|---------|-----|------|
| WeatherAPI | https://www.weatherapi.com/signup.aspx | Free (1M calls/month) |
| Google Gemini | https://aistudio.google.com/apikey | Free tier available |

### 2. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` and paste your keys:
```
WEATHERAPI_KEY=your_actual_key
GEMINI_API_KEY=your_actual_key
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

### 5. Open in Browser

Navigate to: **http://localhost:8000**

Click "📍 Detect My Location" and allow location access.

## Project Structure

```
Project/
├── main.py              # FastAPI backend (rule engine + Gemini + cache)
├── requirements.txt     # Python dependencies
├── .env.example         # Template for API keys
├── .gitignore
├── README.md
└── static/
    ├── index.html       # Frontend dashboard
    ├── style.css        # Responsive CSS
    └── app.js           # Geolocation + fetch + rendering
```

## Features

### Rule Engine Alerts
| Condition | Category | Action |
|-----------|----------|--------|
| AQI ≥ 4 (EPA) | Health | N95 mask warning |
| PM2.5 > 35 µg/m³ | Health | Respiratory caution |
| UV ≥ 11 | Health | Avoid sun exposure |
| Temp ≥ 42°C | Health | Heatstroke warning |
| Rain > 60% | Agriculture | Postpone pesticide spraying |
| Wind > 25 km/h | Agriculture | Delay spraying (drift risk) |
| Min Temp ≤ 2°C | Agriculture | Frost protection advisory |
| Humidity < 30% | Agriculture | Irrigation recommendation |
| Visibility < 1 km | Lifestyle | Fog driving warning |
| Wind > 50 km/h | Lifestyle | Secure outdoor items |

### AI Advisory
- Gemini 1.5 Flash generates a 2-sentence summary
- Covers health + agriculture + lifestyle in one advisory
- Cached in SQLite for 30 minutes to save API costs

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Backend | Python 3.11+, FastAPI |
| Database | SQLite (caching) |
| Weather Data | WeatherAPI.com |
| AI Engine | Google Gemini 1.5 Flash |
