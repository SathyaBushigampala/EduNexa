import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import sqlite3
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import io

load_dotenv()

app = FastAPI(title="EduNexa API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# ----------------- AUTH & DB -----------------
SECRET_KEY = os.getenv("SECRET_KEY")
security = HTTPBearer()

def get_db():
    conn = sqlite3.connect("edunexa.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT, 
        email TEXT UNIQUE, 
        password TEXT
    )''')
    conn.commit()

def create_token(email: str, name: str):
    payload = {"email": email, "name": name, "exp": datetime.utcnow() + timedelta(days=1)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

class RegisterReq(BaseModel):
    name: str
    email: str
    password: str

class LoginReq(BaseModel):
    email: str
    password: str

@app.post("/api/register")
def register(req: RegisterReq):
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM users WHERE email=?", (req.email,)).fetchone()
        if existing: raise HTTPException(status_code=400, detail="Email already registered")
        hashed = generate_password_hash(req.password)
        conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (req.name, req.email, hashed))
        conn.commit()
    return {"message": "Registration successful"}

@app.post("/api/login")
def login(req: LoginReq):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=?", (req.email,)).fetchone()
        if not user or not check_password_hash(user["password"], req.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = create_token(user["email"], user["name"])
        return {"token": token, "name": user["name"], "email": user["email"]}

@app.get("/api/me")
def get_me(user: dict = Depends(get_current_user)):
    return user

@app.post("/api/logout")
def logout():
    return {"message": "Logged out successfully"}

# ----------------- DATASET MANAGEMENT -----------------
def get_user_dataset_path(email: str):
    safe_email = "".join([c if c.isalnum() else "_" for c in email])
    return f"dataset_{safe_email}.csv"

def get_data(user: dict):
    path = get_user_dataset_path(user['email'])
    if not os.path.exists(path):
        path = "dataset.csv"
        if not os.path.exists(path):
            import generate_data
            generate_data.generate_dataset(path)
    try:
        return pd.read_csv(path)
    except Exception:
        raise HTTPException(status_code=500, detail="Dataset not found or couldn't be loaded.")

@app.post("/api/generate")
def generate_new_dataset(user: dict = Depends(get_current_user)):
    import generate_data
    path = get_user_dataset_path(user['email'])
    generate_data.generate_dataset(path)
    return {"message": "Dataset generated successfully"}

@app.get("/api/template")
def download_template():
    csv_content = "student_id,study_hours,attendance,sleep_hours,marks\n1,6.5,85,7.0,72.5\n2,4.0,60,6.0,45.0\n"
    return PlainTextResponse(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=template.csv"})

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")

    aliases = {
        "study_hours_per_day": ["study_hours", "study hours", "hours", "study", "study_hours_per_day"],
        "attendance_percentage": ["attendance", "attendance %", "attendance_percentage", "att"],
        "sleep_hours": ["sleep_hours", "sleep hours", "sleep"],
        "marks": ["marks", "score", "grade"]
    }
    
    col_mapping = {}
    lower_cols = {c.strip().lower(): c for c in df.columns}
    
    for std_name, alias_list in aliases.items():
        found = False
        for alias in alias_list:
            if alias.lower() in lower_cols:
                col_mapping[lower_cols[alias.lower()]] = std_name
                found = True
                break
        if not found:
            raise HTTPException(status_code=400, detail=f"Missing column: {std_name} (checked aliases: {', '.join(alias_list)})")

    df = df.rename(columns=col_mapping)
    
    required = ["study_hours_per_day", "attendance_percentage", "sleep_hours", "marks"]
    for r in required:
        if r not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing column: {r}")

    orig_len = len(df)
    df = df.dropna(subset=required)
    df = df.drop_duplicates()
    
    for c in required:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=required)
    
    df = df[
        (df["attendance_percentage"] >= 0) & (df["attendance_percentage"] <= 100) &
        (df["marks"] >= 0) & (df["marks"] <= 100) &
        (df["sleep_hours"] >= 0) & (df["sleep_hours"] <= 24) &
        (df["study_hours_per_day"] >= 0) & (df["study_hours_per_day"] <= 24)
    ]
    
    removed = orig_len - len(df)
    if len(df) < 30:
        raise HTTPException(status_code=400, detail=f"Dataset must have at least 30 valid rows. Found {len(df)} after cleaning.")
    
    if "pass_fail" not in df.columns:
        df["pass_fail"] = (df["marks"] >= 40).astype(int)
        
    if "student_id" not in df.columns:
        df["student_id"] = np.arange(1, len(df) + 1)
        
    path = get_user_dataset_path(user['email'])
    df.to_csv(path, index=False)
    
    preview = df.head(10).to_dict(orient="records")
    return {
        "message": f"Loaded {len(df)} rows, {removed} removed during cleaning.",
        "removed": removed,
        "total": len(df),
        "preview": preview
    }

# ----------------- STATS ENDPOINTS -----------------
@app.get("/api/data")
def get_dataset(user: dict = Depends(get_current_user)):
    df = get_data(user)
    return {"data": df.to_dict(orient="records")}

@app.get("/api/descriptive")
def get_descriptive_stats(user: dict = Depends(get_current_user)):
    df = get_data(user)
    cols = ["marks", "study_hours_per_day", "attendance_percentage"]
    stats_dict = {}
    
    for col in cols:
        series = df[col]
        mode_val = series.mode().iloc[0] if not series.mode().empty else series.mean()
        
        # Confidence interval (95%)
        n = len(series)
        m = series.mean()
        se = series.std() / np.sqrt(n) if n > 0 else 0
        h = se * stats.t.ppf((1 + 0.95) / 2., n-1) if n > 1 else 0
        ci = [round(m - h, 2), round(m + h, 2)] if not np.isnan(m - h) else [0, 0]
        
        stats_dict[col] = {
            "mean": round(float(series.mean()) if not np.isnan(series.mean()) else 0.0, 2),
            "median": round(float(series.median()) if not np.isnan(series.median()) else 0.0, 2),
            "mode": round(float(mode_val) if not np.isnan(mode_val) else 0.0, 2),
            "variance": round(float(series.var()) if not np.isnan(series.var()) else 0.0, 2),
            "std_dev": round(float(series.std()) if not np.isnan(series.std()) else 0.0, 2),
            "range": round(float(series.max() - series.min()) if not np.isnan(series.max() - series.min()) else 0.0, 2),
            "ci_95": ci
        }
        
    marks_skew = df["marks"].skew()
    marks_skewness = round(float(marks_skew) if not np.isnan(marks_skew) else 0.0, 4)
    marks_kurt = df["marks"].kurtosis()
    marks_kurtosis = round(float(marks_kurt) if not np.isnan(marks_kurt) else 0.0, 4)
    
    # Shapiro-Wilk on Marks
    if len(df["marks"]) >= 3:
        w, p_sw = stats.shapiro(df["marks"])
        shapiro = {"w": round(w, 4), "p_value": p_sw}
    else:
        shapiro = {"w": 0, "p_value": 1.0}
        
    counts, bins = np.histogram(df["marks"], bins=[0, 20, 40, 60, 80, 100])
    hist_data = [{"bin": f"{bins[i]}-{bins[i+1]}", "count": int(counts[i])} for i in range(len(counts))]

    return {
        "stats": stats_dict,
        "marks_skewness": marks_skewness,
        "marks_kurtosis": marks_kurtosis,
        "shapiro_wilk": shapiro,
        "histogram": hist_data,
        "explanation": "Descriptive statistics computed."
    }

@app.get("/api/probability")
def get_probability(user: dict = Depends(get_current_user)):
    df = get_data(user)
    n = len(df)
    
    p_marks_gt_75 = len(df[df["marks"] > 75]) / n if n > 0 else 0
    p_att_gt_90 = len(df[df["attendance_percentage"] > 90]) / n if n > 0 else 0
    p_both = len(df[(df["marks"] > 75) & (df["attendance_percentage"] > 90)]) / n if n > 0 else 0
    
    p_marks_given_att = p_both / p_att_gt_90 if p_att_gt_90 > 0 else 0
    p_att_given_marks = p_both / p_marks_gt_75 if p_marks_gt_75 > 0 else 0
    
    return {
        "p_marks_gt_75": round(p_marks_gt_75, 4),
        "p_att_gt_90": round(p_att_gt_90, 4),
        "p_marks_given_att": round(p_marks_given_att, 4),
        "p_att_given_marks": round(p_att_given_marks, 4),
        "bayes_formula": "P(A|B) = [P(B|A) * P(A)] / P(B)",
        "bayes_substituted": f"[{round(p_marks_given_att,4)} * {round(p_att_gt_90,4)}] / {round(p_marks_gt_75,4)} = {round(p_att_given_marks,4)}"
    }

@app.get("/api/hypothesis-testing")
def get_hypothesis_testing(user: dict = Depends(get_current_user)):
    df = get_data(user)
    
    # 1. Welch's T-Test
    high_study = df[df["study_hours_per_day"] > 5]["marks"]
    low_study = df[df["study_hours_per_day"] <= 5]["marks"]
    
    t_test_res = {}
    if len(high_study) > 1 and len(low_study) > 1 and high_study.var() > 0 and low_study.var() > 0:
        t_stat, p_two = stats.ttest_ind(high_study, low_study, equal_var=False)
        df_t = len(high_study) + len(low_study) - 2
        p_greater = stats.t.sf(t_stat, df_t)
        p_less = stats.t.cdf(t_stat, df_t)
        
        t_test_res = {
            "valid": True,
            "t_statistic": round(float(t_stat), 4) if not np.isnan(t_stat) else 0.0,
            "p_two": float(p_two) if not np.isnan(p_two) else 1.0,
            "p_right": float(p_greater) if not np.isnan(p_greater) else 1.0,
            "p_left": float(p_less) if not np.isnan(p_less) else 1.0
        }
    else:
        t_test_res = {"valid": False, "error_msg": "Insufficient groups or zero variance."}
    
    # 2. Z-Test for proportions
    high_att = df[df["attendance_percentage"] >= 80]
    low_att = df[df["attendance_percentage"] < 80]
    successes = np.array([high_att["pass_fail"].sum(), low_att["pass_fail"].sum()])
    nobs = np.array([len(high_att), len(low_att)])
    
    z_test_res = {}
    if np.all(nobs > 0):
        from statsmodels.stats.proportion import proportions_ztest
        from scipy.stats import norm
        try:
            z_stat, p_two = proportions_ztest(successes, nobs)
            if np.isnan(z_stat): raise ValueError()
            z_right = 1 - norm.cdf(z_stat)
            z_left = norm.cdf(z_stat)
            z_test_res = {
                "valid": True,
                "z_statistic": round(float(z_stat), 4),
                "p_two": float(p_two),
                "p_right": float(z_right),
                "p_left": float(z_left)
            }
        except:
            z_test_res = {"valid": False, "error_msg": "Groups are identical or have 0 variance."}
    else:
        z_test_res = {"valid": False, "error_msg": "One or both groups are empty."}
        
    # 3. Chi-square
    df_copy = df.copy()
    df_copy['att_group'] = np.where(df_copy['attendance_percentage'] >= 80, 'High', 'Low')
    df_copy['pf_str'] = np.where(df_copy['pass_fail'] == 1, 'Pass', 'Fail')
    contingency = pd.crosstab(df_copy['att_group'], df_copy['pf_str'])
    
    chi_res = {}
    if contingency.shape[0] > 1 and contingency.shape[1] > 1:
        chi2, p_chi, _, _ = stats.chi2_contingency(contingency, correction=False)
        chi_res = {
            "valid": True,
            "chi2_statistic": round(float(chi2), 4) if not np.isnan(chi2) else 0.0,
            "p_value": float(p_chi) if not np.isnan(p_chi) else 1.0
        }
    else:
        chi_res = {"valid": False, "error_msg": "Need sufficient data in all categories (empty groups detected)."}
        
    # 4. ANOVA
    df_copy['study_group'] = pd.cut(df_copy['study_hours_per_day'], bins=[-1, 4, 7, 25], labels=['Low', 'Medium', 'High'])
    groups = [group['marks'].values for name, group in df_copy.groupby('study_group', observed=True) if len(group) > 0]
    
    anova_res = {}
    if len(groups) >= 2:
        f_stat, p_anova = stats.f_oneway(*groups)
        anova_res = {
            "valid": True,
            "f_statistic": round(float(f_stat), 4) if not np.isnan(f_stat) else 0.0,
            "p_value": float(p_anova) if not np.isnan(p_anova) else 1.0
        }
    else:
        anova_res = {"valid": False, "error_msg": "Insufficient groups (need >= 2)."}
        
    return {
        "t_test": t_test_res,
        "z_test_proportions": z_test_res,
        "chi_square": chi_res,
        "anova": anova_res
    }

@app.get("/api/correlation")
def get_correlation(user: dict = Depends(get_current_user)):
    df = get_data(user)
    cols = ["study_hours_per_day", "attendance_percentage", "sleep_hours", "marks"]
    df_subset = df[cols]
    return {
        "pearson": df_subset.corr(method="pearson").fillna(0).to_dict(),
        "spearman": df_subset.corr(method="spearman").fillna(0).to_dict()
    }

@app.get("/api/regression")
def get_regression(user: dict = Depends(get_current_user)):
    df = get_data(user)
    try:
        X_simple = sm.add_constant(df["study_hours_per_day"])
        y = df["marks"]
        model_simple = sm.OLS(y, X_simple).fit()
        r_squared_simple = model_simple.rsquared
    except Exception:
        r_squared_simple = 0.0

    try:
        X_mult = df[["study_hours_per_day", "attendance_percentage", "sleep_hours"]]
        X_mult_const = sm.add_constant(X_mult)
        model_mult = sm.OLS(y, X_mult_const).fit()
        r_squared_mult = model_mult.rsquared
        adj_r2 = model_mult.rsquared_adj
        model_rmse = np.sqrt(model_mult.mse_resid)
        
        # 80/20 train/test split
        X_train, X_test, y_train, y_test = train_test_split(X_mult_const, y, test_size=0.2, random_state=42)
        m2 = sm.OLS(y_train, X_train).fit()
        preds = m2.predict(X_test)
        test_r2 = r2_score(y_test, preds)
        test_rmse = np.sqrt(mean_squared_error(y_test, preds))
        
        # VIF
        vifs = [variance_inflation_factor(X_mult_const.values, i) for i in range(X_mult_const.shape[1])]
        vif_dict = {
            "study_hours": round(vifs[1], 4),
            "attendance": round(vifs[2], 4),
            "sleep_hours": round(vifs[3], 4)
        }
    except Exception:
        r_squared_mult = 0.0
        adj_r2 = 0.0
        model_rmse = 0.0
        test_r2 = 0.0
        test_rmse = 0.0
        vif_dict = {}
    
    return {
        "simple_linear": {"r_squared": round(r_squared_simple, 4)},
        "multiple_linear": {
            "r_squared": round(r_squared_mult, 4),
            "adjusted_r_squared": round(adj_r2, 4),
            "model_rmse": round(model_rmse, 4),
            "test_r_squared": round(test_r2, 4),
            "test_rmse": round(test_rmse, 4),
            "vif": vif_dict
        }
    }

class PredictionRequest(BaseModel):
    study_hours: float
    attendance: float
    sleep_hours: float

@app.post("/api/predict")
def predict_marks(req: PredictionRequest, user: dict = Depends(get_current_user)):
    df = get_data(user)
    try:
        X = df[["study_hours_per_day", "attendance_percentage", "sleep_hours"]]
        X = sm.add_constant(X)
        y = df["marks"]
        model = sm.OLS(y, X).fit()
        
        new_data = [1, req.study_hours, req.attendance, req.sleep_hours]
        pred = model.get_prediction(new_data)
        summary = pred.summary_frame(alpha=0.05)
        
        prediction = summary.loc[0, 'mean']
        pi_lower = summary.loc[0, 'obs_ci_lower']
        pi_upper = summary.loc[0, 'obs_ci_upper']
    except Exception:
        prediction = 0
        pi_lower = 0
        pi_upper = 0
    
    # Clip to bounds
    prediction = min(max(prediction, 0), 100)
    pi_lower = min(max(pi_lower, 0), 100)
    pi_upper = min(max(pi_upper, 0), 100)
    
    return {
        "predicted_marks": round(prediction, 2),
        "prediction_interval": [round(pi_lower, 2), round(pi_upper, 2)]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
