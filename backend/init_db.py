import psycopg2
import os

conn = psycopg2.connect(
    host="team18-phase2-database.cuvgicoyg2el.us-east-1.rds.amazonaws.com",
    port=5432,
    database="Team18_Model_Registry",
    user="Team18",
    password="ElwaAsteroidFoob18"
)

cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS artifacts (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
""")
conn.commit()
cur.close()
conn.close()
print("✅ Table created successfully!")
