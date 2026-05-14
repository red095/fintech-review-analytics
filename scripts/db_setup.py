

import psycopg2
from psycopg2 import sql
import pandas as pd
import os


DB_CONFIG = {
    "host":     "localhost",
    "database": "bank_reviews",
    "user":     "bank_user",
    "password": "bank1234",
    "port":     5433
}


BANKS = [
    {"bank_name": "Commercial Bank of Ethiopia", "app_name": "CBE Mobile"},
    {"bank_name": "Bank of Abyssinia",           "app_name": "BOA Mobile Banking"},
    {"bank_name": "Dashen Bank",                 "app_name": "Dashen Mobile / Super App"},
]


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def create_tables(cur):
   
    
    print("🗄️  Creating tables...")

    cur.execute("DROP TABLE IF EXISTS reviews CASCADE;")
    cur.execute("DROP TABLE IF EXISTS banks CASCADE;")

    cur.execute("""
        CREATE TABLE banks (
            bank_id   SERIAL PRIMARY KEY,
            bank_name VARCHAR(100) NOT NULL UNIQUE,
            app_name  VARCHAR(100) NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE reviews (
            review_id       INTEGER PRIMARY KEY,
            bank_id         INTEGER REFERENCES banks(bank_id),
            review_text     TEXT,
            rating          INTEGER CHECK (rating BETWEEN 1 AND 5),
            review_date     DATE,
            sentiment_label VARCHAR(20),
            sentiment_score FLOAT,
            identified_theme VARCHAR(100),
            source          VARCHAR(50)
        );
    """)

    print("✅ Tables created.")


def insert_banks(cur) -> dict:
    print("🏦 Inserting banks...")
    bank_id_map = {}

    for bank in BANKS:
        cur.execute("""
            INSERT INTO banks (bank_name, app_name)
            VALUES (%s, %s)
            ON CONFLICT (bank_name) DO NOTHING
            RETURNING bank_id;
        """, (bank["bank_name"], bank["app_name"]))

        row = cur.fetchone()
        if row:
            bank_id_map[bank["bank_name"]] = row[0]

    cur.execute("SELECT bank_id, bank_name FROM banks;")
    for row in cur.fetchall():
        bank_id_map[row[1]] = row[0]

    print(f"  Inserted {len(bank_id_map)} banks: {list(bank_id_map.keys())}")
    return bank_id_map


def insert_reviews(cur, df: pd.DataFrame, bank_id_map: dict):
    print(f"📝 Inserting {len(df)} reviews...")
    inserted = 0
    skipped  = 0

    for _, row in df.iterrows():
        bank_id = bank_id_map.get(row["bank"])
        if bank_id is None:
            skipped += 1
            continue

        try:
            cur.execute("""
                INSERT INTO reviews (
                    review_id, bank_id, review_text, rating, review_date,
                    sentiment_label, sentiment_score, identified_theme, source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (review_id) DO NOTHING;
            """, (
                int(row["review_id"]),
                bank_id,
                str(row["review"]),
                int(row["rating"]),
                str(row["date"]),
                str(row["sentiment_label"]),
                float(row["sentiment_score"]),
                str(row["identified_theme"]),
                str(row["source"])
            ))
            inserted += 1

        except Exception as e:
            print(f"  ⚠️  Skipping row {row['review_id']}: {e}")
            skipped += 1

    print(f"  ✅ Inserted: {inserted} | Skipped: {skipped}")


def verify(cur):

    print("\n📊 Verification queries:")

    cur.execute("SELECT COUNT(*) FROM reviews;")
    print(f"  Total reviews in DB:      {cur.fetchone()[0]}")

    cur.execute("""
        SELECT b.bank_name, COUNT(r.review_id) as review_count
        FROM banks b
        LEFT JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_name
        ORDER BY review_count DESC;
    """)
    print("\n  Reviews per bank:")
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]}")

    cur.execute("""
        SELECT b.bank_name, ROUND(AVG(r.rating)::numeric, 2) as avg_rating
        FROM banks b
        JOIN reviews r ON b.bank_id = r.bank_id
        GROUP BY b.bank_name
        ORDER BY avg_rating DESC;
    """)
    print("\n  Average rating per bank:")
    for row in cur.fetchall():
        print(f"    {row[0]}: {row[1]} ⭐")

    cur.execute("""
        SELECT COUNT(*) FROM reviews
        WHERE review_text IS NULL
           OR rating IS NULL
           OR sentiment_label IS NULL;
    """)
    print(f"\n  Null values in key columns: {cur.fetchone()[0]}")


def main():

    input_path = "data/processed/reviews_final.csv"
    if not os.path.exists(input_path):
        print("❌ Run thematic_analysis.py first.")
        return

    df = pd.read_csv(input_path)
    print(f"📂 Loaded {len(df)} reviews from {input_path}\n")

    conn = None
    try:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor()

        create_tables(cur)
        bank_id_map = insert_banks(cur)
        insert_reviews(cur, df, bank_id_map)
        verify(cur)

        conn.commit()
        print("\n✅ All data committed to PostgreSQL successfully!")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\n❌ Database error: {e}")
        raise

    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()