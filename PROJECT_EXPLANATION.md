# Project Explanation Guide: Enterprise GenAI Security Gateway

> **Final Year Capstone Project Defense & Review Guide**  
> *Written in simple, accessible language for viva preparation and technical review.*

---

## 1. Project Objective & Problem Statement

### The Problem
In modern corporate environments, employees frequently utilize Artificial Intelligence (AI) and Large Language Model (LLM) tools such as ChatGPT, Claude, or Copilot to write emails, draft documentation, analyze code, and summarize enterprise documents. However, employees frequently copy and paste sensitive information directly into these external public cloud tools. 

Examples of leaked data include:
* **Personally Identifiable Information (PII)**: Customer names, personal email addresses, phone numbers, home addresses, IP addresses, SSNs.
* **Security Credentials**: Passwords, API keys (AWS, OpenAI, Stripe), secret access tokens, cryptographic private keys, database connection strings.
* **Internal Business Secrets**: Internal project code names (`Project Phoenix`, `Project Atlas`), internal URLs (`api.internal.company.com`), confidential markers (`STRICTLY CONFIDENTIAL`, `INTERNAL USE ONLY`), proprietary source code.

Once submitted to external public LLMs, this sensitive data leaves the enterprise network boundary, posing severe data breach risks, compliance violations (GDPR, HIPAA, SOC2), and corporate intellectual property loss.

### The Solution
The **Enterprise GenAI Security Gateway** acts as a mandatory security checkpoint positioned between employee web browsers / API clients and external LLM services. Employees never communicate directly with external AI services. Instead:
1. The prompt is sent to our Gateway backend (`POST /api/chat`).
2. Three-layer sensitive data inspection (Microsoft Presidio PII + Custom Regex Secrets + Enterprise Confidentiality Detector) scans the prompt.
3. The Policy Engine computes a risk score (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) and decides whether to `ALLOW` or `BLOCK` the prompt.
4. **If BLOCKED**: The prompt is rejected immediately. **The external LLM API is NEVER called.**
5. **If ALLOWED**: The prompt is forwarded to the real external LLM (Groq Cloud API), and the response is safely returned.
6. An immutable Audit Log is stored in SQLite for security admin monitoring.

---

## 2. System Architecture & Complete Request Flow

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

## 3. Major Component Breakdown

For each major component, we explain: **What is it?**, **Why did we use it?**, and **How does it work in OUR project?**

---

### A. Frontend (React + Vite)
* **What is it?** A fast, single-page web application interface built with React 18 and Vite.
* **Why did we use it?** React provides a component-driven architecture that makes building interactive forms, loading indicators, and admin dashboards simple and responsive. Vite provides lightning-fast local development and instant hot-module replacement.
* **How does it work in OUR project?**
  * **Employee Chat Page (`ChatPage.jsx`)**: Provides prompt input, synthetic sample buttons for rapid testing, and real-time security decision banners (Green `ALLOW` vs Red `BLOCKED`).
  * **Admin Dashboard (`AdminDashboard.jsx`)**: Displays key security metrics (Total Requests, Allowed, Blocked, Block Rate %), category distribution charts, risk breakdown, and searchable audit logs.

---

### B. Backend Framework (FastAPI)
* **What is it?** A high-performance Python web framework for building modern RESTful APIs.
* **Why did we use it?** FastAPI provides asynchronous request handling, automatic data validation using Pydantic, speed comparable to NodeJS/Go, and simple Python syntax.
* **How does it work in OUR project?**
  * Serves as the Gateway entry point (`main.py`).
  * Exposes `POST /api/chat` to process prompts, `POST /api/analyze` for standalone text inspection, and `GET /api/admin/stats` & `GET /api/admin/logs` for the administrator dashboard.

---

### C. Three-Layer Sensitive Data Detection Engine
* **What is it?** A hybrid multi-layer detection architecture combining Presidio NLP, Custom Regex rules, and Enterprise Confidentiality patterns.
* **Why did we use it?** 
  * **Microsoft Presidio** excels at context-aware Named Entity Recognition (NER) for standard PII (person names, locations, email addresses, phone numbers). *(Note: Presidio is an open-source detection framework which our gateway extends).*
  * **Custom Regex Rule Engine** excels at matching specific, structured technical secrets (AWS keys, OpenAI keys, Bearer tokens, hardcoded passwords, private RSA keys, database URIs).
  * **Enterprise Confidentiality Detector (`confidential_detector.py`)** handles organization-specific confidential markers (`INTERNAL USE ONLY`), project code names (`Project Phoenix`), internal network domains (`*.internal.company.com`), and source code leakage.
* **How does it work in OUR project?**
  * `presidio_detector.py` scans for standard PII.
  * `regex_detector.py` scans for credentials.
  * `confidential_detector.py` scans rules from `confidential_patterns.json`.
  * `unified_detector.py` merges findings from all three detectors, deduplicates overlapping character ranges, computes highest severity risk level, and creates safe redacted snippets.

---

### D. Policy Engine (`policy_engine.py`)
* **What is it?** A rule-based decision module that evaluates detection findings.
* **Why did we use it?** To decouple sensitive data detection from policy decision logic, making governance rules easy to customize and explain.
* **How does it work in OUR project?**
  * Assigns Risk Levels:
    * `LOW`: No sensitive data detected. -> Decision: `ALLOW`
    * `MEDIUM`: General PII detected. -> Decision: `BLOCK`
    * `HIGH`: Multiple PII or internal enterprise confidential markers detected. -> Decision: `BLOCK`
    * `CRITICAL`: Passwords, API keys, private keys, or DB credentials detected. -> Decision: `BLOCK`

---

### E. Real External LLM Integration Layer (`llm_client.py`)
* **What is it?** An isolated backend module that manages communication with real external Cloud LLM providers.
* **Why did we use it?** Isolating LLM communication ensures that prompt filtering and LLM invocation are strictly separated.
* **How does it work in OUR project?**
  * Primary provider is **Groq Cloud API** (`LLM_PROVIDER=groq`, model `llama-3.3-70b-versatile`).
  * Uses environment variables stored in `backend/.env`.
  * **Strict Security Enforcement Boundary**: The LLM client function is executed **ONLY IF** the Policy Engine decision equals `ALLOW`. For `BLOCKED` prompts, execution halts immediately and the LLM is NOT called.
  * If the API key is missing or invalid, an explicit error is returned. Fake/mock fallback in production is eliminated.

---

### F. Database & Audit Logging (SQLite + SQLAlchemy)
* **What is it?** A lightweight embedded SQL database managed via Python SQLAlchemy ORM.
* **Why did we use it?** Requires zero external database server setup while ensuring persistent, structured audit records.
* **How does it work in OUR project?**
  * Table `audit_logs` records every request: `request_id`, `timestamp`, `user_id`, `prompt_snippet` (redacted), `is_sensitive`, `detected_entities` (JSON array), `risk_level`, `policy_decision`, `llm_called`, `latency_ms`.
  * **Security Principle**: Raw passwords and secret keys are **NEVER** stored in the database.

---

## 4. Evaluation Methodology & Metrics

We created an automated evaluation script (`evaluate.py`) that tests our Security Gateway against a synthetic dataset of 40 prompts across 5 categories (Safe, PII, Credentials, Enterprise Confidential, Internal Infrastructure).

### Key Metrics:

1. **True Positive (TP)**: A sensitive prompt that was correctly detected and **BLOCKED**.
2. **True Negative (TN)**: A safe prompt that was correctly identified and **ALLOWED**.
3. **False Positive (FP)**: A safe prompt that was incorrectly **BLOCKED**.
4. **False Negative (FN)**: A sensitive prompt that was incorrectly **ALLOWED** (Critical Risk!).
5. **Precision**: Out of all prompts our system blocked, how many were actually sensitive?
6. **Recall**: Out of all sensitive prompts present, how many did our system successfully block?
7. **F1-Score**: The harmonic mean of Precision and Recall.
8. **Gateway Latency vs LLM Latency**: Detection & policy evaluation takes ~1-5ms, whereas external Groq LLM API invocation takes ~500-1500ms.

---

## 5. Security & Architectural Considerations

1. **No API Keys in Frontend**: All external API keys reside securely in backend `.env` files.
2. **Deterministic Block Boundary**: The LLM caller function is structurally unreachable when decision == `BLOCK`.
3. **Privacy-Preserving Audit Log**: Raw secrets are masked with placeholders before saving to disk.
4. **Graceful Fallback**: If spaCy NLP fails, regex & confidential rules ensure continuous detection.
