# 💍 Wedding Planner App

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15--Alpine-336791?style=flat-square&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Multi--Container-2496ED?style=flat-square&logo=docker)

A reactive Full-Stack platform designed for multi-tenant wedding event planning, automated guest CRM, and real-time financial ledger tracking.

---

## 📋 Table of Contents
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Key Architectural Features](#-key-architectural-features)
- [Database & Financial Engine](#-database--financial-engine)
- [Installation & Development Setup](#-installation--development-setup)
- [Testing Suite](#-testing-suite)
- [License & Contact](#-license--contact)

---

## 🛠️ Architecture & Tech Stack

### Backend (Asynchronous API)
* **Framework:** `FastAPI` (Async I/O, ASGI, Native OpenAPI/Swagger generation).
* **Data Access:** `SQLAlchemy 2.0 (Async)` using `asyncpg` driver.
* **Migrations:** `Alembic`.
* **Security:** `Argon2id` password hashing + stateless `JWT (OAuth2)` Bearer architecture.

### Frontend (SPA)
* **Framework:** `React 18` + `TypeScript`.
* **Build Tool:** `Vite`.
* **State Management:** `Zustand` (Unidirectional decoupled state).
* **Forms:** `React Hook Form` + Zod schema validation.

---

## 🚀 Key Architectural Features

* 🔐 **Strict Multi-Tenancy Isolation:** Resource access control is verified at the database query layer. Unauthorized resource requests return `HTTP 404 Not Found` to prevent resource enumeration attacks.
* 👥 **Guest CRM Lifecycle:** Manages transactional invitation states (`PENDING`, `CONFIRMED`, `REJECTED`) paired with strict relational metadata validations (dietary profiles, accommodation capacity, and table mapping).
* 📊 **Optimized Data Aggregation:** Solves the *N+1 query* problem by leveraging PostgreSQL Database Views (`wp.event_guest_summary`) for heavy analytical queries, removing compute overhead from the Python application layer.

---

## 🧮 Financial Engine Matrix

Building on the aggregated PostgreSQL views (see *Optimized Data Aggregation*), a deterministic Python engine handles all financial operations – from budget tracking to final settlements. The logic operates on the smallest currency unit to avoid floating-point errors and is fully isolated for unit testing, guaranteeing mathematical consistency across the entire platform.

---

## ⚙️ Installation & Development Setup

### Prerequisites
* Docker & Docker Compose
* Python 3.13+ (for local linting/testing outside containers)
* Node.js 18+ (for running the frontend outside Docker)

### 1. Quickstart (Docker Compose - Recommended)
To spin up the entire development ecosystem (Frontend with HMR, API with auto-reload, and isolated PostgreSQL instance):
```bash
docker-compose -f docker-compose.dev.yml up --build
```
* Interactive API Docs: http://localhost:8000/docs
* Frontend Client: http://localhost:5173

### 2. Manual Local Backend Setup (Bare-Metal)
If you need to run the backend service outside Docker for active debugging while utilizing the containerized database:

Start only the database container:
```bash
docker-compose -f docker-compose.dev.yml up db -d
```

Configure and run the local Python virtual environment (note the local port 5433 mapped from the development container):
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Override database URL to target the exposed host port
export DATABASE_URL="postgresql+asyncpg://dev_user:dev_password@localhost:5433/wedding_db_dev"

alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Manual Local Frontend Setup
If you need to run the React client outside Docker (e.g. for debugging) while using the containerized API:

```bash
cd frontend
npm install
npm run dev
```

Make sure Node.js 18+ is available. The development server will start at http://localhost:5173 and will proxy API requests to the backend running on http://localhost:8000 (adjust vite.config.ts if needed).

---

## 🧪 Testing Suite

Automated testing is implemented using `pytest` and `pytest-asyncio` utilizing an isolated database schema strategy per test session.

### Execution
To run the full suite (including cross-boundary multi-tenancy checks and financial integration pipeline tests):
```bash
cd backend
python -m pytest
```

---

## 📄 License & Contact

Copyright (c) 2026 Bartosz Wawrzyk. All rights reserved.
Proprietary software developed strictly for portfolio demonstration.

* Author: Bartosz Wawrzyk
* Email: bartoszwawrzyk888@gmail.com