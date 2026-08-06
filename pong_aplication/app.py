import os
import psycopg2
from fastapi import FastAPI, HTTPException

app = FastAPI()

DB_HOST = os.getenv("POSTGRES_HOST", "postgres-svc")
DB_NAME = os.getenv("POSTGRES_DB", "pingpong_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgrespassword")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port="5432"
    )

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pongs (
                id INT PRIMARY KEY,
                counter INT NOT NULL
            );
        """)
        cur.execute("""
            INSERT INTO pongs (id, counter)
            VALUES (1, 0)
            ON CONFLICT (id) DO NOTHING;
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database init exception: {e}")

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/pingpong")
def pingpong():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE pongs SET counter = counter + 1 WHERE id = 1 RETURNING counter;")
        counter = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return f"pong {counter}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/pongs")
def get_pongs():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT counter FROM pongs WHERE id = 1;")
        row = cur.fetchone()
        counter = row[0] if row else 0
        cur.close()
        conn.close()
        return {"pongs": counter}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/")
def root():
    return pingpong()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)