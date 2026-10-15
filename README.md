# 📊 EduNexa — Academic Performance & Statistical Analytics Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-5.0%2B-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-ML-F7931E.svg?logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![Statsmodels](https://img.shields.io/badge/Statsmodels-Econometrics-blue.svg)](https://www.statsmodels.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

EduNexa is a full-stack educational data science platform developed for **Probability & Statistics (MA112)**. It provides end-to-end exploratory data analysis, inferential hypothesis testing, multicollinearity evaluation, and predictive machine learning to uncover how study habits, attendance, sleep hygiene, and extracurricular activities directly impact student examination outcomes.

---

## 🎯 Problem Statement

Academic institutions often rely on reactive grade monitoring—intervening only after a student has already failed an examination. Furthermore, students lack empirical visibility into how lifestyle habits (such as daily study hours, sleep duration, and social media screen time) mathematically correlate with their academic performance.

**EduNexa** bridges this gap by transforming raw student telemetry into rigorous inferential statistical models, empowering educators and students with predictive GPA forecasting and actionable pedagogical interventions before exams take place.

---

## 🔬 Core Features & Statistical Engine

### 1. Descriptive Analytics & Exploratory Dashboard
- Real-time KPIs: Class Mean Marks, Median Study Hours, Average Attendance Rate, and Sleep Variance.
- Distribution histograms, scatter plots, and Pearson correlation matrices quantifying feature associations.

### 2. Predictive Machine Learning (Multiple Linear Regression)
- Fits an Ordinary Least Squares (OLS) regression model predicting `Final Marks` based on multi-dimensional regressors:
  $$\hat{Y} = \beta_0 + \beta_1(\text{Study Hours}) + \beta_2(\text{Attendance}) + \beta_3(\text{Sleep Hours}) - \beta_4(\text{Social Media Hours})$$
- Automatically computes model validation metrics: **$R^2$ Score**, **Adjusted $R^2$**, and **Mean Squared Error (MSE)**.
- **Multicollinearity Diagnostics**: Computes **Variance Inflation Factor (VIF)** across predictors to safeguard against matrix instability ($VIF > 5$).

### 3. Inferential Hypothesis Testing
- **Two-Sample Independent T-Test**: Evaluates whether statistically significant performance differences exist between high-study cohorts ($\ge 4\text{ hrs/day}$) and control groups.
- **Two-Sample Z-Test**: Tests population proportion hypotheses across large sample distributions.
- **Bayesian Probability Modeling**: Calculates posterior probabilities using Bayes' Theorem:
  $$P(\text{High Marks} \mid \text{High Study}) = \frac{P(\text{High Study} \mid \text{High Marks}) \cdot P(\text{High Marks})}{P(\text{High Study})}$$

### 4. Interactive Simulation & GPA Predictor
- Sliders allowing students to simulate what-if scenarios (e.g., "If I increase study time by 2 hours and reduce social media by 1 hour, what is my projected final mark?").

### 5. Multi-Tenant Data Management & PDF Reporting
- Upload, edit, and validate custom student CSV datasets.
- Export comprehensive statistical summary briefs cleanly to PDF.
- Secure JWT-based user authentication supporting both PostgreSQL (production) and cross-platform SQLite (development).

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (React 18 + Vite + TS)            │
│  - Interactive Metric Cards & Distribution Visualizers  │
│  - Hypothesis Testing Controls (T-Test, Z-Test, Bayes)  │
│  - Live What-If Regression Simulator                    │
└────────────────────────────┬────────────────────────────┘
                             │ REST API (Bearer JWT)
                             ▼
┌─────────────────────────────────────────────────────────┐
│               Backend (FastAPI + Python 3.11)           │
│  ├── /api/auth/*         -> JWT Auth & User Management  │
│  ├── /api/data/*         -> Dataset Ingestion & CRUD    │
│  ├── /api/regression/*   -> OLS, R², MSE & VIF Engine   │
│  └── /api/statistics/*   -> T-Tests, Z-Tests, Bayes     │
└──────────────┬───────────────────────────┬──────────────┘
               │                           │
               ▼                           ▼
┌────────────────────────────┐ ┌──────────────────────────┐
│   Statistical Toolchain    │ │     Persistence Tier     │
│   - scikit-learn & pandas  │ │  - PostgreSQL (Neon)     │
│   - scipy.stats & numpy    │ │  - SQLite (Local Dev)    │
│   - statsmodels (OLS, VIF) │ │                          │
└────────────────────────────┘ └──────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend API** | FastAPI, Uvicorn, Python 3.11, Pydantic, Gunicorn |
| **Statistical & ML Engine** | Scikit-Learn, Statsmodels, SciPy Stats, NumPy, Pandas |
| **Authentication & Security** | PyJWT (HS256 tokens), Werkzeug security hashing, HTTP Bearer |
| **Database** | PostgreSQL (psycopg2-binary) / SQLite3 fallback |
| **Frontend UI** | React 18, TypeScript, Vite, CSS Modules / Modern CSS |
| **Deployment** | Render (`render.yaml`), Vercel (`vercel.json`) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- (Optional) PostgreSQL database instance (or use built-in SQLite for local dev)

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd EduNexa/backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in `EduNexa/` (or copy `.env.example`):
   ```env
   SECRET_KEY=your-development-jwt-secret
   # Optional: Omit DATABASE_URL to automatically use local SQLite
   # DATABASE_URL=postgresql://user:password@localhost:5432/edunexa
   ```

5. **Start the FastAPI backend server**:
   ```bash
   uvicorn app:app --reload --port 8000
   ```
   The backend API will be live at `http://127.0.0.1:8000`. You can inspect interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   The application UI will be available at `http://localhost:5173`.

---

## 📡 API Reference Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Healthcheck and server readiness | No |
| `POST` | `/api/register` | Register a new educator or student account | No |
| `POST` | `/api/login` | Authenticate user and return JWT bearer token | No |
| `GET` | `/api/correlation` | Compute feature Pearson correlation matrix | Yes |
| `POST` | `/api/predict` | Predict final marks via Multiple Linear Regression | Yes |
| `GET` | `/api/stats/ttest` | Run two-sample independent T-Test on study tiers | Yes |
| `GET` | `/api/stats/bayes` | Compute Bayes' Theorem conditional probabilities | Yes |
| `GET` | `/api/vif` | Calculate Variance Inflation Factors for regressors | Yes |
| `POST` | `/api/data/upload` | Upload custom CSV dataset for analysis | Yes |

---

## 📂 Project Structure

```
EduNexa/
├── backend/
│   ├── app.py                  # Core FastAPI application & statistical endpoints
│   ├── dataset.csv             # Baseline student academic dataset
│   ├── generate_data.py        # Synthetic student dataset generator
│   └── requirements.txt        # Backend Python dependencies
├── frontend/
│   ├── src/                    # React 18 TypeScript source code
│   │   ├── App.tsx             # Main application layout and dashboard router
│   │   ├── main.tsx            # React application entrypoint
│   │   └── App.css             # Component styles
│   ├── package.json            # Frontend NPM dependencies
│   ├── tsconfig.json           # TypeScript configuration
│   └── vite.config.ts          # Vite build config
├── dataset.csv                 # Root student performance dataset
├── render.yaml                 # Render cloud deployment specification
├── vercel.json                 # Vercel serverless deployment specification
├── .env.example                # Environment variables template
├── .gitignore                  # Git exclusions for DB, cache, and env files
├── LICENSE                     # MIT License
└── README.md                   # Complete project documentation
```

---

## 🔮 Limitations & Future Roadmap

- [ ] **Expanded ML Classifiers**: Incorporate Random Forests and Logistic Regression for binary at-risk student classification.
- [ ] **LMS Integrations**: Add automated ingestion webhooks for Canvas and Google Classroom.
- [ ] **Time-Series Telemetry**: Track student attendance and quiz progression over academic semesters rather than cross-sectional data alone.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
