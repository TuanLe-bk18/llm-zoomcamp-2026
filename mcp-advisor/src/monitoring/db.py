import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "monitoring.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create interactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        user_query TEXT NOT NULL,
        rewritten_query TEXT,
        latency_ms REAL,
        recommended_server TEXT,
        top_k_candidates TEXT,
        feedback INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()

def log_interaction(user_query, rewritten_query, latency_ms, recommended_server, top_k_candidates):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    candidates_json = json.dumps(top_k_candidates) if top_k_candidates else "[]"
    
    cursor.execute('''
    INSERT INTO interactions (timestamp, user_query, rewritten_query, latency_ms, recommended_server, top_k_candidates)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, user_query, rewritten_query, latency_ms, recommended_server, candidates_json))
    
    interaction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return interaction_id

def update_feedback(interaction_id, feedback_value):
    # feedback_value: 1 for thumbs up, -1 for thumbs down
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE interactions
    SET feedback = ?
    WHERE id = ?
    ''', (feedback_value, interaction_id))
    
    conn.commit()
    conn.close()

def get_dashboard_metrics():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Basic metrics
    cursor.execute("SELECT COUNT(*) as total FROM interactions")
    total_requests = cursor.fetchone()['total']
    
    cursor.execute("SELECT AVG(latency_ms) as avg_lat FROM interactions")
    avg_latency = cursor.fetchone()['avg_lat'] or 0.0
    
    # Feedback ratio
    cursor.execute("SELECT COUNT(*) as positive FROM interactions WHERE feedback = 1")
    positive_feedback = cursor.fetchone()['positive']
    
    cursor.execute("SELECT COUNT(*) as negative FROM interactions WHERE feedback = -1")
    negative_feedback = cursor.fetchone()['negative']
    
    # Top recommended servers
    cursor.execute('''
    SELECT recommended_server, COUNT(*) as count 
    FROM interactions 
    WHERE recommended_server IS NOT NULL AND recommended_server != ''
    GROUP BY recommended_server 
    ORDER BY count DESC 
    LIMIT 5
    ''')
    top_servers = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_requests": total_requests,
        "avg_latency": avg_latency,
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback,
        "top_servers": top_servers
    }

def get_all_interactions_df():
    import pandas as pd
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM interactions", conn)
    conn.close()
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Initialize on import
init_db()
