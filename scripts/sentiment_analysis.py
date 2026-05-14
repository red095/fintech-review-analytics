from transformers import pipeline
import pandas as pd
import os

print("⏳ Loading sentiment model (first run downloads ~250MB)...")
sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    truncation=True,      # Reviews longer than 512 tokens get truncated
    max_length=512
)
print("✅ Model loaded!\n")

def get_sentiment(text:str)-> tuple:
    try:
        result = sentiment_model(text)[0]
        label = result["label"]   
        score = round(result["score"], 4)
        if score < 0.70:
            label = "NEUTRAL"

        return label, score

    except Exception as e:
        print(f"  ⚠️  Error on review: {e}")
        return "NEUTRAL", 0.0
def main():
  
    input_path = "data/raw/reviews_raw.csv"
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        print("   Please run scrape_reviews.py first.")
        return

    df = pd.read_csv(input_path)
    print(f"📂 Loaded {len(df)} reviews from {input_path}\n")


    from tqdm import tqdm
    tqdm.pandas(desc="🔍 Analyzing sentiment")

    results = []
    batch_size = 32

    for i in tqdm(range(0, len(df), batch_size)):
        batch = df["review"].iloc[i:i+batch_size].tolist()
        for text in batch:
            label, score = get_sentiment(str(text))
            results.append((label, score))

    df["sentiment_label"] = [r[0] for r in results]
    df["sentiment_score"] = [r[1] for r in results]

    print("\n📊 Sentiment distribution overall:")
    print(df["sentiment_label"].value_counts())

    print("\n📊 Sentiment by bank:")
    print(df.groupby("bank")["sentiment_label"].value_counts())

    print("\n⭐ Average sentiment score by star rating:")
    print(df.groupby("rating")["sentiment_score"].mean().round(3))

    os.makedirs("data/processed", exist_ok=True)
    output_path = "data/processed/reviews_with_sentiment.csv"
    df.to_csv(output_path, index=False)
    print(f"\n💾 Saved to {output_path}")


if __name__ == "__main__":
    main()