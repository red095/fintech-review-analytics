CREATE TABLE banks (
    bank_id   SERIAL PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL UNIQUE,
    app_name  VARCHAR(100) NOT NULL
);

CREATE TABLE reviews (
    review_id        INTEGER PRIMARY KEY,
    bank_id          INTEGER REFERENCES banks(bank_id),
    review_text      TEXT,
    rating           INTEGER CHECK (rating BETWEEN 1 AND 5),
    review_date      DATE,
    sentiment_label  VARCHAR(20),
    sentiment_score  FLOAT,
    identified_theme VARCHAR(100),
    source           VARCHAR(50)
);