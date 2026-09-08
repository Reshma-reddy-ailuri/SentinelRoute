# Enterprise GenAI Security Gateway

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Bundler-Vite-646CFF.svg)](https://vitejs.dev/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![Groq](https://img.shields.io/badge/LLM%20Provider-Groq-orange.svg)](https://groq.com/)

An API-driven **Enterprise GenAI Security Gateway** designed to prevent employees and API clients from accidentally transmitting sensitive data (PII, credentials, API keys, passwords, organization-specific confidential projects, and internal infrastructure links) to external Cloud LLM services.

---

## Architectural Architecture & Request Flow

```
Employee / API Client
          │
          ▼
React Chat UI / REST API
          │
          ▼
FastAPI Security Gateway
          │
          ▼
Presidio + Custom Regex + Enterprise Confidentiality Detection
          │
          ▼
Unified Detection
          │
          ▼
Risk Assessment
          │
          ▼
Policy Engine
          │
  ┌───────┴───────┐
  ▼               ▼
ALLOW           BLOCK
  │               │
  ▼               ▼
Real External LLM Request Rejected
(Groq Cloud API) (LLM Not Contacted)
  │               │
  └───────┬───────┘
          ▼
SQLite Audit Log
          │
          ▼
Admin Dashboard
```

---

## Key Features

* **Real-Time Gateway Checkpoint**: Intercepts employee prompts and REST API requests before external cloud AI models receive any text.
* **Three-Layer Sensitive Data Detection Engine**:
  * **Microsoft Presidio NLP**: Context-aware NLP entity recognition for standard PII (Names, Emails, Phone numbers, Locations, Credit cards, IP addresses, SSN, IBAN).
  * **Custom Regex Rule Engine**: Precise pattern matching for technical credentials and secrets (AWS Keys, OpenAI Keys, Bearer tokens, hardcoded passwords, private RSA keys, database URIs, employee IDs).
  * **Enterprise Confidentiality Detector**: Configurable organization-specific detector (`confidential_detector.py` & `confidential_patterns.json`) scanning for confidentiality markers (`STRICTLY CONFIDENTIAL`, `INTERNAL USE ONLY`), internal project names (`Project Phoenix`, `Project Atlas`), internal network URLs (`*.internal.company.com`), and source code leakage.
* **Configurable Policy Engine**: Evaluates aggregated detection results, assigns risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and determines `ALLOW` vs. `BLOCK` decisions.
* **Strict Security Enforcement Boundary**: Blocked prompts NEVER trigger external LLM API calls.
* **Real External LLM Client**: Isolated integration layer communicating with real Cloud LLMs using **Groq** as the primary provider (`llama-3.3-70b-versatile`). Returns clear API errors when key is missing (no silent fake/mock fallbacks).
* **Reusable Standalone Analysis API**: Exposes `POST /api/analyze` for inspecting text sensitivity, risk level, and policy decisions without invoking the external LLM.
* **Privacy-Preserving Audit Log**: Stores audit records in SQLite without saving raw secrets or passwords.
* **Administrator Security Dashboard**: Real-time analytics cards, category distribution charts, risk breakdown, and searchable audit logs populated directly from SQLite.
* **Benchmark Evaluation Suite**: Automated script evaluating Accuracy, Precision, Recall, F1-Score, and Gateway Latency vs LLM Latency against an expanded synthetic dataset.

> **Note on Microsoft Presidio**: Microsoft Presidio is an open-source detection framework utilized for standard PII. Our project extends the Security Gateway with custom regex rules and organization-specific enterprise confidentiality detection.

---

## Project Structure

```
d:\deloittecapstone\
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point & CORS
│   │   ├── config.py                   # Environment settings & constants
│   │   ├── api/
│   │   │   ├── chat.py                 # POST /api/chat & POST /api/analyze endpoints
│   │   │   └── admin.py                # GET /api/admin/stats & GET /api/admin/logs
│   │   ├── detection/
│   │   │   ├── presidio_detector.py    # Presidio PII detector wrapper
│   │   │   ├── regex_detector.py       # Custom regex detector for secrets/keys
│   │   │   ├── confidential_detector.py# Enterprise internal & project detector
│   │   │   ├── confidential_patterns.json# Configurable enterprise indicators
│   │   │   └── unified_detector.py     # Aggregates all 3 detection layers
│   │   ├── policy/
│   │   │   └── policy_engine.py        # Risk assessment & ALLOW/BLOCK policy logic
│   │   ├── llm/
│   │   │   └── llm_client.py           # Real External LLM client (Groq / OpenAI)
│   │   └── database/
│   │       ├── db.py                   # SQLite connection setup
│   │       └── models.py               # AuditLog SQLite ORM schema
│   ├── tests/
│   │   ├── test_detection.py           # Unit tests for detectors
│   │   ├── test_policy.py              # Unit tests for policy engine
│   │   └── test_gateway_api.py         # Integration API tests (all scenarios)
│   ├── .env.example                    # Environment variable template
│   ├── .gitignore                      # Git ignore file (ignores .env & .db)
│   ├── requirements.txt                # Python backend dependencies
│   └── pytest.ini                      # Pytest config
├── frontend/
│   ├── src/
│   │   ├── components/                 # Navbar, SecurityBadge, CategoryChip
│   │   ├── pages/                      # ChatPage, AdminDashboard
│   │   ├── services/                   # Axios API service
│   │   ├── App.jsx                     # Routes & layout
│   │   └── App.css                     # Enterprise security styling
│   ├── package.json
│   └── vite.config.js
├── evaluation/
│   ├── dataset/
│   │   └── synthetic_dataset.json      # 40 synthetic test prompts across 5 categories
│   ├── evaluation_report.json          # Benchmark evaluation report artifact
│   └── evaluate.py                     # Precision/Recall benchmark script
├── PROJECT_EXPLANATION.md              # Student defense & architecture guide
├── VIVA_QUESTIONS.md                   # 30+ capstone viva questions & answers
└── README.md
```

---

## Installation & Setup Guide

### 1. Prerequisites
* Python 3.10+
* Node.js v18+ and npm

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create backend/.env file from template
cp .env.example .env

# Edit backend/.env and set your Groq API Key:
# LLM_PROVIDER=groq
# LLM_API_KEY=gsk_your_actual_groq_api_key_here
# LLM_MODEL=llama-3.3-70b-versatile

# Install backend dependencies
python -m pip install -r requirements.txt

# Run pytest backend unit tests
python -m pytest

# Start FastAPI backend server
python app/main.py
# Backend server starts at http://localhost:8000
```

### 3. Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
# Frontend interface starts at http://localhost:5173
```

### 4. Running the Benchmark Evaluation
```bash
# From project root directory
python evaluation/evaluate.py
```

---

## Demonstration Scenarios

### Demo 1 — Safe Request
* **Input**: `"Explain the difference between REST and SOAP."`
* **Flow**: Detection -> No sensitive data -> Policy = `ALLOW` -> Real LLM (Groq) Called -> Response displayed.

### Demo 2 — Sensitive PII Request
* **Input**: `"My email is test@example.com."`
* **Flow**: Detection -> `EMAIL_ADDRESS` -> Policy = `BLOCK` -> **LLM NOT CALLED**.

### Demo 3 — Sensitive Credential Request
* **Input**: `"My AWS access key is AKIAIOSFODNN7EXAMPLE."`
* **Flow**: Detection -> `API_KEY` (CRITICAL) -> Policy = `BLOCK` -> **LLM NOT CALLED**.

### Demo 4 — Confidential Project Request
* **Input**: `"This is a confidential internal architecture document for Project Phoenix."`
* **Flow**: Detection -> `CONFIDENTIAL_MARKER`, `INTERNAL_PROJECT_NAME` -> Policy = `BLOCK` -> **LLM NOT CALLED**.

### Demo 5 — Internal URL Request
* **Input**: `"The internal API is available at https://api.internal.company.com/."`
* **Flow**: Detection -> `INTERNAL_INFRASTRUCTURE_URL` -> Policy = `BLOCK` -> **LLM NOT CALLED**.

### Demo 6 — Admin Dashboard
* Open `http://localhost:5173/admin` to view summary cards, category distributions, risk breakdown, and searchable audit log table powered by SQLite.

---

## Defense & Review Documentation

* Read [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md) for a simple explanation of every component, algorithm, and flow.
* Read [VIVA_QUESTIONS.md](VIVA_QUESTIONS.md) to practice 30+ likely capstone viva questions.
