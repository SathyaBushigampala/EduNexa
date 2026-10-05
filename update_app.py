import os

with open('backend/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace sqlite3 with psycopg2
code = code.replace("import sqlite3", "import psycopg2\nfrom psycopg2.extras import RealDictCursor\nimport urllib.parse")

# Update get_db
get_db_old = """def get_db():
    conn = sqlite3.connect("edunexa.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn"""

get_db_new = """def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required")
    # Neon might need sslmode=require
    if "?" not in db_url:
        db_url += "?sslmode=require"
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    return conn"""
code = code.replace(get_db_old, get_db_new)

# Update Table Creation
tables_old = """with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT, 
        email TEXT UNIQUE, 
        password TEXT
    )''')
    conn.commit()"""

tables_new = """try:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute('''CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, 
                name TEXT, 
                email TEXT UNIQUE, 
                password TEXT
            )''')
            cur.execute('''CREATE TABLE IF NOT EXISTS datasets (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE,
                csv_data TEXT
            )''')
        conn.commit()
except Exception as e:
    print("Database init warning:", e)"""
code = code.replace(tables_old, tables_new)

# Fix register
register_old = """    with get_db() as conn:
        existing = conn.execute("SELECT * FROM users WHERE email=?", (req.email,)).fetchone()
        if existing: raise HTTPException(status_code=400, detail="Email already registered")
        hashed = generate_password_hash(req.password)
        conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (req.name, req.email, hashed))
        conn.commit()"""

register_new = """    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (req.email,))
            existing = cur.fetchone()
            if existing: raise HTTPException(status_code=400, detail="Email already registered")
            hashed = generate_password_hash(req.password)
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (req.name, req.email, hashed))
        conn.commit()"""
code = code.replace(register_old, register_new)

# Fix login
login_old = """    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE email=?", (req.email,)).fetchone()
        if not user or not check_password_hash(user["password"], req.password):"""
login_new = """    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (req.email,))
            user = cur.fetchone()
        if not user or not check_password_hash(user["password"], req.password):"""
code = code.replace(login_old, login_new)

# Update get_user_dataset_path / get_data / generate_new_dataset / upload_dataset
dataset_old = """def get_user_dataset_path(email: str):
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

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    path = get_user_dataset_path(user['email'])
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"message": "File uploaded successfully"}"""

dataset_new = """def get_data(user: dict):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT csv_data FROM datasets WHERE email=%s", (user['email'],))
            row = cur.fetchone()
            if row and row['csv_data']:
                return pd.read_csv(io.StringIO(row['csv_data']))
    
    # Fallback/Generate if not in Postgres
    import generate_data
    path = "/tmp/dataset.csv"
    generate_data.generate_dataset(path)
    df = pd.read_csv(path)
    csv_data = df.to_csv(index=False)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO datasets (email, csv_data) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET csv_data = EXCLUDED.csv_data", (user['email'], csv_data))
        conn.commit()
    return df

@app.post("/api/generate")
def generate_new_dataset(user: dict = Depends(get_current_user)):
    import generate_data
    path = "/tmp/dataset_new.csv"
    generate_data.generate_dataset(path)
    with open(path, 'r', encoding='utf-8') as f:
        csv_data = f.read()
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO datasets (email, csv_data) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET csv_data = EXCLUDED.csv_data", (user['email'], csv_data))
        conn.commit()
    return {"message": "Dataset generated successfully"}

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    content = await file.read()
    csv_data = content.decode('utf-8')
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO datasets (email, csv_data) VALUES (%s, %s) ON CONFLICT (email) DO UPDATE SET csv_data = EXCLUDED.csv_data", (user['email'], csv_data))
        conn.commit()
    return {"message": "File uploaded successfully"}"""
code = code.replace(dataset_old, dataset_new)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated backend/app.py")
