import sqlite3
from datetime import datetime

DB_PATH = "ipo_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ipos (
        id TEXT PRIMARY KEY,
        name TEXT, symbol TEXT, type TEXT, status TEXT,
        open_date TEXT, close_date TEXT, listing_date TEXT,
        price_low REAL, price_high REAL, issue_size REAL,
        fresh_issue REAL, ofs REAL, lot_size INTEGER,
        overall_score REAL, risk_score REAL,
        data_confidence TEXT, ai_summary TEXT,
        last_updated TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS gmp_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ipo_id TEXT, gmp REAL, source TEXT, timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS sub_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ipo_id TEXT, qib REAL, nii REAL, retail REAL, total REAL,
        source TEXT, timestamp TEXT
    )''')
    conn.commit()
    conn.close()

def save_ipo(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO ipos 
                 (id, name, type, status, price_low, price_high, 
                 overall_score, risk_score, data_confidence, ai_summary, last_updated) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['id'], data['name'], data['type'], data['status'], 
               data['price_low'], data['price_high'], data.get('overall_score'), 
               data.get('risk_score'), data.get('data_confidence', 'UNVERIFIED'), 
               data.get('ai_summary', ''), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_gmp(ipo_id, gmp, source):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO gmp_history (ipo_id, gmp, source, timestamp) VALUES (?, ?, ?, ?)',
              (ipo_id, gmp, source, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_ipos():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ipos = conn.execute('SELECT * FROM ipos ORDER BY last_updated DESC').fetchall()
    conn.close()
    return [dict(ix) for ix in ipos]

def get_latest_gmp(ipo_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT gmp, timestamp FROM gmp_history WHERE ipo_id = ? ORDER BY timestamp DESC LIMIT 1', (ipo_id,)).fetchone()
    conn.close()
    return {"gmp": row[0], "time": row[1]} if row else {"gmp": None, "time": None}
