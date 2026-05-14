import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("📥 Downloading spaCy model...")
    os.system("python3 -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

THEMES = {
    "Account Access Issues":    [
        "login", "password", "otp", "verification", "sign in", "register",
        "account", "locked", "blocked", "access", "fingerprint", "biometric"
    ],
    "Transaction Performance":  [
        "transfer", "transaction", "payment", "send", "receive", "slow",
        "fast", "speed", "delay", "pending", "failed", "money", "fund"
    ],
    "App Stability & Performance": [
        "crash", "bug", "error", "freeze", "loading", "update", "install",
        "open", "close", "force", "stop", "fix", "issue", "problem", "work"
    ],
    "UI & User Experience":     [
        "interface", "design", "easy", "simple", "navigation", "button",
        "screen", "feature", "use", "user", "friendly", "look", "feel"
    ],
    "Customer Support":         [
        "support", "service", "help", "staff", "agent", "response",
        "contact", "complaint", "call", "branch", "resolve", "feedback"
    ],
}

def preprocess(text: str) -> str:
   
    doc = nlp(text.lower())
    tokens = [
        token.lemma_ for token in doc
        if not token.is_stop       
        and not token.is_punct      
        and not token.is_space      
        and len(token.lemma_) > 2  
    ]
    return " ".join(tokens)

def assign_theme(text: str) -> str:
    text_lower = text.lower()
    for theme, keywords in THEMES.items():
        if any(kw in text_lower for kw in keywords):
            return theme
    return "General Feedback"

def get_top_keywords(texts: list, n: int = 15) -> list:
    import re

    def clean_for_tfidf(text):
        text = re.sub(r'\b\w*\d\w*\b', '', text)
        text = re.sub(r'\b\w{1,2}\b', '', text)
        return text

    cleaned_texts = [clean_for_tfidf(t) for t in texts]

    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=3,          
        max_df=0.85,       
        token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b' 
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(cleaned_texts)
        scores = np.array(tfidf_matrix.sum(axis=0)).flatten()
        feature_names = vectorizer.get_feature_names_out()
        scored = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in scored[:n]]
    except ValueError:
        return ["insufficient data"]


def main():

    input_path = "data/processed/reviews_with_sentiment.csv"
    if not os.path.exists(input_path):
        print("❌ Run sentiment_analysis.py first.")
        return

    df = pd.read_csv(input_path)
    print(f"📂 Loaded {len(df)} reviews\n")

    print("🔤 Preprocessing text (lemmatization)...")
    df["cleaned_review"] = df["review"].astype(str).apply(preprocess)

    print("🏷️  Assigning themes...")
    df["identified_theme"] = df["review"].astype(str).apply(assign_theme)

    print("\n📊 Theme distribution per bank:")
    theme_counts = df.groupby(["bank", "identified_theme"]).size().unstack(fill_value=0)
    print(theme_counts)

    

    print("\n🔑 Top keywords by sentiment per bank:")
    for bank in df["bank"].unique():
        print(f"\n  📌 {bank}:")

        for sentiment in ["POSITIVE", "NEGATIVE"]:
            subset = df[(df["bank"] == bank) & (df["sentiment_label"] == sentiment)]
            if len(subset) < 5:
                continue
            texts = subset["cleaned_review"].tolist()
            keywords = get_top_keywords(texts, n=8)
            emoji = "😊" if sentiment == "POSITIVE" else "😠"
            print(f"    {emoji} {sentiment}: {', '.join(keywords)}")

    
    print("\n\n🏷️  Top keywords per theme per bank:")
    for bank in df["bank"].unique():
        print(f"\n  📌 {bank}:")
        for theme in THEMES.keys():
            subset = df[(df["bank"] == bank) & (df["identified_theme"] == theme)]
            if len(subset) < 3:
                continue
            texts = subset["cleaned_review"].tolist()
            keywords = get_top_keywords(texts, n=5)
            print(f"    [{theme}]: {', '.join(keywords)}")

    df.insert(0, "review_id", range(1, len(df) + 1))

    os.makedirs("data/processed", exist_ok=True)
    output_path = "data/processed/reviews_final.csv"

    df[["review_id", "review", "rating", "date", "bank", "source",
        "sentiment_label", "sentiment_score", "identified_theme"]].to_csv(
        output_path, index=False
    )
    print(f"\n💾 Saved final dataset to {output_path}")
    print(f"📝 Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()