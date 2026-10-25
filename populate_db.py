import os
import csv
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

if 'port' not in os.environ:
    os.environ['port'] = '3306'

# ============================================================
# CONFIGURATION
# ============================================================

CSV_DIR = "data"
DB_NAME = os.environ['database']

# ============================================================
# DATABASE CONNECTION & CREATION
# ============================================================

# Connect to MySQL server first (without specifying a database)
conn = mysql.connector.connect(
    host=os.environ['host'],
    port=int(os.environ['port']),
    user=os.environ['user'],
    password=os.environ['password']
)
conn.autocommit = False
cursor = conn.cursor()

# Create the database if it doesn't exist and switch to it
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
cursor.execute(f"USE {DB_NAME}")

print(f"Connected to MySQL and using database: {DB_NAME}")

# ============================================================
# CREATE TABLES
# ============================================================

create_tables_sql = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(50),
    city VARCHAR(100),
    province VARCHAR(50),
    user_type VARCHAR(20) NOT NULL,
    signup_date DATE,
    is_active BOOLEAN
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    driver_id INTEGER NOT NULL,
    make VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    license_plate VARCHAR(20) UNIQUE,
    color VARCHAR(30),
    is_active BOOLEAN,

    CONSTRAINT fk_vehicle_driver
        FOREIGN KEY (driver_id)
        REFERENCES users(user_id),
        
    INDEX idx_vehicles_driver_id (driver_id)
);

CREATE TABLE IF NOT EXISTS rides (
    ride_id INTEGER PRIMARY KEY,
    rider_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,

    requested_at DATETIME,
    pickup_time DATETIME,
    dropoff_time DATETIME,

    pickup_latitude DECIMAL(9,6),
    pickup_longitude DECIMAL(9,6),

    dropoff_latitude DECIMAL(9,6),
    dropoff_longitude DECIMAL(9,6),

    distance_km DECIMAL(10,2),
    fare DECIMAL(10,2),
    surge_multiplier DECIMAL(4,2),

    status VARCHAR(30),
    cancellation_reason VARCHAR(100),

    CONSTRAINT fk_ride_rider
        FOREIGN KEY (rider_id)
        REFERENCES users(user_id),

    CONSTRAINT fk_ride_driver
        FOREIGN KEY (driver_id)
        REFERENCES users(user_id),
        
    INDEX idx_rides_rider_id (rider_id),
    INDEX idx_rides_driver_id (driver_id),
    INDEX idx_rides_requested_at (requested_at),
    INDEX idx_rides_status (status)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    payment_status VARCHAR(30),
    transaction_id VARCHAR(100) UNIQUE,
    payment_time DATETIME,

    CONSTRAINT fk_payment_ride
        FOREIGN KEY (ride_id)
        REFERENCES rides(ride_id),

    CONSTRAINT fk_payment_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id),
        
    INDEX idx_payments_ride_id (ride_id),
    INDEX idx_payments_user_id (user_id)
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    rider_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    rating INTEGER,
    comment TEXT,
    rated_at DATETIME,

    CONSTRAINT fk_rating_ride
        FOREIGN KEY (ride_id)
        REFERENCES rides(ride_id),

    CONSTRAINT fk_rating_rider
        FOREIGN KEY (rider_id)
        REFERENCES users(user_id),

    CONSTRAINT fk_rating_driver
        FOREIGN KEY (driver_id)
        REFERENCES users(user_id),

    CONSTRAINT chk_rating
        CHECK (rating BETWEEN 1 AND 5),
        
    INDEX idx_ratings_ride_id (ride_id),
    INDEX idx_ratings_driver_id (driver_id)
);
"""

# Split the SQL commands by semicolon and execute them one by one to avoid multi=True errors
for statement in create_tables_sql.split(';'):
    if statement.strip():
        cursor.execute(statement)

print("Tables created successfully")


# ============================================================
# OPTIONAL: CLEAR EXISTING DATA
# ============================================================

# Disable foreign key checks to wipe the tables cleanly
cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
cursor.execute("TRUNCATE TABLE ratings;")
cursor.execute("TRUNCATE TABLE payments;")
cursor.execute("TRUNCATE TABLE rides;")
cursor.execute("TRUNCATE TABLE vehicles;")
cursor.execute("TRUNCATE TABLE users;")
cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")


# ============================================================
# LOAD CSV USING BATCH INSERTS
# ============================================================

def load_csv(table_name, csv_file, columns):
    file_path = os.path.join(CSV_DIR, csv_file)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row

        # Create parameterized SQL statement
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        data = []
        for row in reader:
            processed_row = []
            for val in row:
                # Handle empty strings and boolean conversions
                if val == '':
                    processed_row.append(None)
                elif val.strip().lower() == 'true':
                    processed_row.append(1)
                elif val.strip().lower() == 'false':
                    processed_row.append(0)
                else:
                    processed_row.append(val)
            
            data.append(processed_row)

        # Batch execute for performance
        cursor.executemany(insert_sql, data)

    print(f"Loaded {csv_file}")


# ============================================================
# LOAD DATA
# ============================================================

load_csv(
    "users",
    "users.csv",
    [
        "user_id", "first_name", "last_name", "email", "phone",
        "city", "province", "user_type", "signup_date", "is_active"
    ]
)

load_csv(
    "vehicles",
    "vehicles.csv",
    [
        "vehicle_id", "driver_id", "make", "model", "year",
        "license_plate", "color", "is_active"
    ]
)

load_csv(
    "rides",
    "rides.csv",
    [
        "ride_id", "rider_id", "driver_id", "requested_at", "pickup_time",
        "dropoff_time", "pickup_latitude", "pickup_longitude",
        "dropoff_latitude", "dropoff_longitude", "distance_km",
        "fare", "surge_multiplier", "status", "cancellation_reason"
    ]
)

load_csv(
    "payments",
    "payments.csv",
    [
        "payment_id", "ride_id", "user_id", "amount", "payment_method",
        "payment_status", "transaction_id", "payment_time"
    ]
)

load_csv(
    "ratings",
    "ratings.csv",
    [
        "rating_id", "ride_id", "rider_id", "driver_id",
        "rating", "comment", "rated_at"
    ]
)


# ============================================================
# VERIFY RECORD COUNTS
# ============================================================

tables = ["users", "vehicles", "rides", "payments", "ratings"]

print("\nRecord counts:")
print("-" * 40)

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table:<15} {count:>10,}")


# ============================================================
# COMMIT & CLOSE
# ============================================================

conn.commit()
print("\nData loaded successfully!")
print("Transaction committed.")

cursor.close()
conn.close()
print("MySQL connection closed.")