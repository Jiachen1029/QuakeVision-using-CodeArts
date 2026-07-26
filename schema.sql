-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'ROLE_USER'
);

-- Earthquakes table
CREATE TABLE IF NOT EXISTS earthquakes (
    id SERIAL PRIMARY KEY,
    original_id INTEGER, -- To store the '序号' from the excel
    time TIMESTAMP NOT NULL,
    longitude FLOAT NOT NULL,
    latitude FLOAT NOT NULL,
    depth FLOAT NOT NULL,
    magnitude FLOAT NOT NULL,
    location VARCHAR(255),
    event_type VARCHAR(50)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_earthquakes_time ON earthquakes(time);
CREATE INDEX IF NOT EXISTS idx_earthquakes_magnitude ON earthquakes(magnitude);
CREATE INDEX IF NOT EXISTS idx_earthquakes_longitude ON earthquakes(longitude);
CREATE INDEX IF NOT EXISTS idx_earthquakes_latitude ON earthquakes(latitude);

-- Cities table (Geocoding cache)
CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cities_name ON cities(name);

-- Favorites table (User's favorited earthquakes)
CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER NOT NULL,
    earthquake_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, earthquake_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (earthquake_id) REFERENCES earthquakes(id)
);

-- Upload logs table
CREATE TABLE IF NOT EXISTS upload_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    records_count INTEGER,
    status VARCHAR(50) DEFAULT 'success',
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_upload_logs_user_id ON upload_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_logs_created_at ON upload_logs(created_at);
