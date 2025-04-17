-- SQL script to create tables in Supabase for the Space Weather Timeline app

-- Create the dates table
CREATE TABLE IF NOT EXISTS dates (
    id BIGSERIAL PRIMARY KEY,
    date TEXT UNIQUE NOT NULL,
    url TEXT,
    error TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced BOOLEAN DEFAULT FALSE
);

-- Create indexes for the dates table
CREATE INDEX IF NOT EXISTS idx_dates_date ON dates (date);

-- Create the events table
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    date_id BIGINT NOT NULL,
    category TEXT NOT NULL,
    tone TEXT,
    event_date TEXT,
    predicted_arrival TEXT,
    detail TEXT,
    image_url TEXT,
    is_significant BOOLEAN DEFAULT FALSE,
    synced BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (date_id) REFERENCES dates (id) ON DELETE CASCADE
);

-- Create indexes for the events table
CREATE INDEX IF NOT EXISTS idx_events_date_id ON events (date_id);
CREATE INDEX IF NOT EXISTS idx_events_category ON events (category);
