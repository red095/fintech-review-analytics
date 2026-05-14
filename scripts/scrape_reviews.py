

from google_play_scraper import reviews, Sort
import pandas as pd
import os
from datetime import datetime


APPS = {
    "Commercial Bank of Ethiopia": "com.combanketh.mobilebanking",
    "Bank of Abyssinia":           "com.boa.boaMobileBanking",
    "Dashen Bank":                 "com.cr2.amolelight",
    "Dashen Bank Super App":       "com.dashen.dashensuperapp",
}

def scrape_bank(bank_name: str, app_id: str, target: int = 600) -> list:
    
    print(f"\n📱 Scraping: {bank_name} ({app_id})")
    
    all_reviews = []
    continuation_token = None  # Used to paginate through results

    while len(all_reviews) < target:
        try:
            # Fetch a batch of reviews (max 200 per call)
            batch, continuation_token = reviews(
                app_id,
                lang="en",
                country="et",       # Ethiopia
                sort=Sort.NEWEST,
                count=200,
                continuation_token=continuation_token
            )

            if not batch:
                print(f"  ⚠️  No more reviews available after {len(all_reviews)}")
                break

            all_reviews.extend(batch)
            print(f"  ✅ Collected so far: {len(all_reviews)}")

            # If there's no token to continue, we've hit the end
            if continuation_token is None:
                break

        except Exception as e:
            print(f"  ❌ Error while scraping {bank_name}: {e}")
            break

    #  Clean and reshape each review 
    cleaned = []
    for r in all_reviews:
        cleaned.append({
            "review":  r.get("content", ""),         # The review text
            "rating":  r.get("score", None),          # 1–5 stars
            "date":    r.get("at", None),             # datetime object
            "bank":    bank_name,
            "source":  "Google Play"
        })

    return cleaned


def main():
    all_data = []

    for bank_name, app_id in APPS.items():
        bank_reviews = scrape_bank(bank_name, app_id, target=600)
        all_data.extend(bank_reviews)

    #  Build a DataFrame 
    df = pd.DataFrame(all_data)

    # Normalize the date column to YYYY-MM-DD string format
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["bank"] = df["bank"].replace("Dashen Bank Super App", "Dashen Bank")

    # Remove duplicates
    before = len(df)
    df.drop_duplicates(subset=["review", "bank"], inplace=True)
    print(f"\n🗑️  Removed {before - len(df)} duplicate reviews")

    # Handle missing values
    missing_before = df[["review", "rating"]].isnull().sum()
    print(f"\n⚠️  Missing values before drop:\n{missing_before}")
    df.dropna(subset=["review", "rating"], inplace=True)

    #  Summary 
    print(f"\n📊 Final review counts per bank:")
    print(df["bank"].value_counts())
    print(f"\n📝 Total reviews: {len(df)}")

    
    #  Save to CSV 
    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/reviews_raw.csv"
    df.to_csv(output_path, index=False)
    print(f"\n💾 Saved to {output_path}")


if __name__ == "__main__":
    main()