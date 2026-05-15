

import pytest
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def raw_df():
    path = "data/raw/reviews_raw.csv"
    if not os.path.exists(path):
        pytest.skip("Raw data not found — run scrape_reviews.py first")
    return pd.read_csv(path)


@pytest.fixture
def final_df():
    path = "data/processed/reviews_final.csv"
    if not os.path.exists(path):
        pytest.skip("Processed data not found — run thematic_analysis.py first")
    return pd.read_csv(path)



class TestDataCollection:

    def test_minimum_review_count(self, raw_df):
        """Must have at least 1200 reviews total."""
        assert len(raw_df) >= 1200, (
            f"Expected 1200+ reviews, got {len(raw_df)}"
        )

    def test_all_three_banks_present(self, raw_df):
        """All three banks must appear in the dataset."""
        expected_banks = {
            "Commercial Bank of Ethiopia",
            "Bank of Abyssinia",
            "Dashen Bank"
        }
        actual_banks = set(raw_df["bank"].unique())
        assert expected_banks.issubset(actual_banks), (
            f"Missing banks: {expected_banks - actual_banks}"
        )

    def test_minimum_reviews_per_bank(self, raw_df):
        """Each bank must have at least 400 reviews."""
        counts = raw_df["bank"].value_counts()
        for bank, count in counts.items():
            assert count >= 400, (
                f"{bank} has only {count} reviews (minimum: 400)"
            )

    def test_required_columns_exist(self, raw_df):
        """Raw CSV must have all 5 required columns."""
        required = {"review", "rating", "date", "bank", "source"}
        missing  = required - set(raw_df.columns)
        assert not missing, f"Missing columns: {missing}"

    def test_no_missing_review_text(self, raw_df):
        """No review should have empty text."""
        null_count = raw_df["review"].isnull().sum()
        assert null_count == 0, f"Found {null_count} reviews with missing text"

    def test_no_missing_ratings(self, raw_df):
        """No review should have a missing rating."""
        null_count = raw_df["rating"].isnull().sum()
        assert null_count == 0, f"Found {null_count} reviews with missing rating"

    def test_rating_range(self, raw_df):
        """All ratings must be between 1 and 5."""
        invalid = raw_df[~raw_df["rating"].between(1, 5)]
        assert len(invalid) == 0, (
            f"Found {len(invalid)} reviews with invalid ratings"
        )

    def test_date_format(self, raw_df):
        """Dates must be parseable as YYYY-MM-DD."""
        try:
            pd.to_datetime(raw_df["date"], format="%Y-%m-%d")
        except Exception as e:
            pytest.fail(f"Date format is invalid: {e}")

    def test_source_column_value(self, raw_df):
        """All reviews must have source = 'Google Play'."""
        invalid = raw_df[raw_df["source"] != "Google Play"]
        assert len(invalid) == 0, (
            f"Found {len(invalid)} reviews with unexpected source"
        )

    def test_no_duplicate_reviews(self, raw_df):
        """No two reviews from the same bank should have identical text."""
        dupes = raw_df.duplicated(subset=["review", "bank"]).sum()
        assert dupes == 0, f"Found {dupes} duplicate reviews"



class TestSentimentAnalysis:

    def test_sentiment_columns_exist(self, final_df):
        """Processed CSV must have sentiment columns."""
        for col in ["sentiment_label", "sentiment_score"]:
            assert col in final_df.columns, f"Missing column: {col}"

    def test_sentiment_labels_valid(self, final_df):
        """Sentiment labels must only be POSITIVE, NEGATIVE, or NEUTRAL."""
        valid  = {"POSITIVE", "NEGATIVE", "NEUTRAL"}
        actual = set(final_df["sentiment_label"].unique())
        invalid = actual - valid
        assert not invalid, f"Unexpected sentiment labels: {invalid}"

    def test_sentiment_coverage(self, final_df):
        """At least 90% of reviews must have a sentiment label."""
        coverage = final_df["sentiment_label"].notna().mean()
        assert coverage >= 0.90, (
            f"Sentiment coverage is {coverage:.1%}, expected 90%+"
        )

    def test_sentiment_score_range(self, final_df):
        """Sentiment scores must be between 0.0 and 1.0."""
        invalid = final_df[
            ~final_df["sentiment_score"].between(0.0, 1.0)
        ]
        assert len(invalid) == 0, (
            f"Found {len(invalid)} reviews with out-of-range sentiment scores"
        )

    def test_theme_column_exists(self, final_df):
        """Processed CSV must have an identified_theme column."""
        assert "identified_theme" in final_df.columns

    def test_minimum_themes_per_bank(self, final_df):
        """Each bank must have at least 3 distinct themes."""
        for bank in final_df["bank"].unique():
            themes = final_df[final_df["bank"] == bank]["identified_theme"].nunique()
            assert themes >= 3, (
                f"{bank} has only {themes} themes (minimum: 3)"
            )

    def test_no_null_themes(self, final_df):
        """Every review must be assigned a theme."""
        null_count = final_df["identified_theme"].isnull().sum()
        assert null_count == 0, f"Found {null_count} reviews with no theme"

    def test_review_id_unique(self, final_df):
        """Every review must have a unique review_id."""
        dupes = final_df["review_id"].duplicated().sum()
        assert dupes == 0, f"Found {dupes} duplicate review IDs"

    def test_positive_reviews_higher_rating(self, final_df):
        """
        On average, POSITIVE sentiment reviews should have
        a higher star rating than NEGATIVE ones.
        This validates that the model aligns with human ratings.
        """
        avg_pos = final_df[final_df["sentiment_label"] == "POSITIVE"]["rating"].mean()
        avg_neg = final_df[final_df["sentiment_label"] == "NEGATIVE"]["rating"].mean()
        assert avg_pos > avg_neg, (
            f"Expected positive reviews to have higher avg rating. "
            f"Got POSITIVE={avg_pos:.2f}, NEGATIVE={avg_neg:.2f}"
        )


class TestDatabase:

    @pytest.fixture
    def db_connection(self):
        """Create a test database connection. Skip if DB is unavailable."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                database="bank_reviews",
                user="bank_user",
                password="bank1234",
                port=5432
            )
            yield conn
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_banks_table_has_three_rows(self, db_connection):
        """Banks table must have exactly 3 rows."""
        cur = db_connection.cursor()
        cur.execute("SELECT COUNT(*) FROM banks;")
        count = cur.fetchone()[0]
        assert count == 3, f"Expected 3 banks, found {count}"

    def test_reviews_table_has_enough_rows(self, db_connection):
        """Reviews table must have at least 1200 rows."""
        cur = db_connection.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews;")
        count = cur.fetchone()[0]
        assert count >= 1200, f"Expected 1200+ reviews, found {count}"

    def test_no_orphan_reviews(self, db_connection):
        """Every review must have a valid bank_id (no broken foreign keys)."""
        cur = db_connection.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM reviews r
            LEFT JOIN banks b ON r.bank_id = b.bank_id
            WHERE b.bank_id IS NULL;
        """)
        orphans = cur.fetchone()[0]
        assert orphans == 0, f"Found {orphans} reviews with invalid bank_id"

    def test_ratings_in_valid_range_db(self, db_connection):
        """All ratings in DB must be 1–5."""
        cur = db_connection.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM reviews
            WHERE rating < 1 OR rating > 5;
        """)
        invalid = cur.fetchone()[0]
        assert invalid == 0, f"Found {invalid} out-of-range ratings in DB"

    def test_no_null_review_text_db(self, db_connection):
        """No review in the DB should have null text."""
        cur = db_connection.cursor()
        cur.execute("SELECT COUNT(*) FROM reviews WHERE review_text IS NULL;")
        nulls = cur.fetchone()[0]
        assert nulls == 0, f"Found {nulls} null review texts in DB"