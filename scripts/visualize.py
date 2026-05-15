

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os


sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
COLORS = {
    "POSITIVE": "#2ecc71",
    "NEUTRAL":  "#f39c12",
    "NEGATIVE": "#e74c3c",
}
BANK_COLORS = {
    "Commercial Bank of Ethiopia": "#2980b9",
    "Bank of Abyssinia":           "#e74c3c",
    "Dashen Bank":                 "#8e44ad",
}
OUTPUT_DIR = "data/visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data() -> pd.DataFrame:
    path = "data/processed/reviews_final.csv"
    if not os.path.exists(path):
        raise FileNotFoundError("Run thematic_analysis.py first.")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df



def plot_sentiment_distribution(df):
    fig, ax = plt.subplots(figsize=(10, 6))

    banks   = df["bank"].unique()
    labels  = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
    data    = {
        label: [
            len(df[(df["bank"] == b) & (df["sentiment_label"] == label)])
            for b in banks
        ]
        for label in labels
    }

    bottoms = [0] * len(banks)
    for label in labels:
        bars = ax.bar(banks, data[label], bottom=bottoms,
                      color=COLORS[label], label=label, edgecolor="white", linewidth=0.5)
        
        for bar, val in zip(bars, data[label]):
            if val > 10:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    str(val), ha="center", va="center",
                    color="white", fontsize=10, fontweight="bold"
                )
        bottoms = [b + d for b, d in zip(bottoms, data[label])]

    ax.set_title("Sentiment Distribution by Bank", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Bank", fontsize=12)
    ax.set_ylabel("Number of Reviews", fontsize=12)
    ax.legend(title="Sentiment", loc="upper right")
    ax.set_xticks(range(len(banks)))
    ax.set_xticklabels(banks, rotation=15, ha="right")
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/plot1_sentiment_distribution.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"✅ Saved: {path}")



def plot_rating_distribution(df):
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
    banks = sorted(df["bank"].unique())

    for ax, bank in zip(axes, banks):
        subset = df[df["bank"] == bank]["rating"]
        counts = subset.value_counts().sort_index()
        color  = BANK_COLORS[bank]

        bars = ax.bar(counts.index, counts.values, color=color,
                      edgecolor="white", linewidth=0.5)
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                str(int(bar.get_height())),
                ha="center", va="bottom", fontsize=9
            )

        avg = subset.mean()
        ax.set_title(f"{bank}\n(avg rating: {avg:.2f})", fontsize=10, fontweight="bold")
        ax.set_xlabel("Star Rating")
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xlim(0.4, 5.6)

    axes[0].set_ylabel("Number of Reviews")
    fig.suptitle("Rating Distribution per Bank", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/plot2_rating_distribution.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved: {path}")


def plot_theme_frequency(df):
    fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=False)
    banks = sorted(df["bank"].unique())

    for ax, bank in zip(axes, banks):
        subset = df[df["bank"] == bank]["identified_theme"].value_counts()
        color  = BANK_COLORS[bank]

        bars = ax.barh(subset.index, subset.values, color=color,
                       edgecolor="white", linewidth=0.5)
        for bar in bars:
            ax.text(
                bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(int(bar.get_width())),
                va="center", fontsize=9
            )

        ax.set_title(bank, fontsize=10, fontweight="bold")
        ax.set_xlabel("Number of Reviews")
        ax.invert_yaxis()

    fig.suptitle("Theme Frequency per Bank", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/plot3_theme_frequency.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved: {path}")


def plot_sentiment_trend(df):
    fig, ax = plt.subplots(figsize=(12, 6))

    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

    for bank, color in BANK_COLORS.items():
        subset = df[df["bank"] == bank].copy()
        subset["sentiment_num"] = subset["sentiment_label"].map(
            {"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": -1}
        )
        monthly = subset.groupby("month")["sentiment_num"].mean()
        ax.plot(monthly.index, monthly.values, label=bank,
                color=color, linewidth=2, marker="o", markersize=4)

    ax.axhline(0, color="gray", linestyle="--", linewidth=1, alpha=0.6)
    ax.set_title("Monthly Sentiment Trend by Bank", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Month")
    ax.set_ylabel("Average Sentiment\n(+1 = Positive, -1 = Negative)")
    ax.legend(title="Bank")
    ax.set_ylim(-1.1, 1.1)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/plot4_sentiment_trend.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"✅ Saved: {path}")


def plot_rating_vs_sentiment(df):
    fig, ax = plt.subplots(figsize=(9, 6))

    for bank, color in BANK_COLORS.items():
        subset = df[df["bank"] == bank]
        avg_rating    = subset["rating"].mean()
        avg_sentiment = subset["sentiment_score"].mean()
        count         = len(subset)

        ax.scatter(avg_rating, avg_sentiment, color=color,
                   s=count / 2, alpha=0.85, edgecolors="white", linewidth=1.5,
                   label=f"{bank} (n={count})", zorder=3)
        ax.annotate(bank.split()[0],  # First word only to avoid overlap
                    (avg_rating, avg_sentiment),
                    textcoords="offset points", xytext=(10, 5), fontsize=9)

    ax.set_title("Avg Star Rating vs Avg Sentiment Score by Bank\n(bubble size = number of reviews)",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Average Star Rating (1–5)")
    ax.set_ylabel("Average Sentiment Score (0–1)")
    ax.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/plot5_rating_vs_sentiment.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"✅ Saved: {path}")


def main():
    print("📂 Loading data...")
    df = load_data()
    print(f"  Loaded {len(df)} reviews\n")

    print("🎨 Generating plots...")
    plot_sentiment_distribution(df)
    plot_rating_distribution(df)
    plot_theme_frequency(df)
    plot_sentiment_trend(df)
    plot_rating_vs_sentiment(df)

    print(f"\n🖼️  All 5 plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()