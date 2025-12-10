#!/usr/bin/env python3
"""
Database Migration Script for Honeypot Events Database
Adds missing columns for enhanced geolocation and attack type classification.
"""
import sqlite3
import os
from honeypot.config import DATABASE_PATH

def migrate_database():
    """Add missing columns to the events table"""
    print(f"Migrating database: {DATABASE_PATH}")
    
    if not os.path.exists(DATABASE_PATH):
        print("Database file does not exist. Creating new database...")
        from honeypot.storage import init_database
        init_database()
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check current table structure
    cursor.execute("PRAGMA table_info(events)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    # Add missing columns if they don't exist
    columns_to_add = [
        ("latitude", "REAL"),
        ("longitude", "REAL"),
        ("attack_type", "TEXT"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    ]
    
    for col_name, col_type in columns_to_add:
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE events ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name} ({col_type})")
            except sqlite3.OperationalError as e:
                print(f"Warning: Could not add column {col_name}: {e}")
    
    # Create missing indexes
    indexes_to_create = [
        ("idx_latitude", "latitude"),
        ("idx_longitude", "longitude"),
        ("idx_attack_type", "attack_type"),
        ("idx_created_at", "created_at")
    ]
    
    for idx_name, col_name in indexes_to_create:
        if col_name in columns or col_name in [c[0] for c in columns_to_add]:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON events({col_name})")
                print(f"Created index: {idx_name}")
            except sqlite3.OperationalError as e:
                print(f"Warning: Could not create index {idx_name}: {e}")
    
    # Migrate existing data: extract latitude/longitude from raw_json if available
    cursor.execute("SELECT id, raw_json FROM events WHERE (latitude IS NULL OR latitude = 0) AND raw_json IS NOT NULL")
    rows = cursor.fetchall()
    
    if rows:
        import json
        print(f"Migrating geolocation data for {len(rows)} records...")
        
        for event_id, raw_json_str in rows:
            try:
                raw_json = json.loads(raw_json_str)
                lat = raw_json.get('latitude')
                lon = raw_json.get('longitude')
                attack_type = raw_json.get('attack_type', 'credential_attempt')
                
                if lat is not None and lon is not None:
                    cursor.execute("""
                        UPDATE events 
                        SET latitude = ?, longitude = ?, attack_type = ?
                        WHERE id = ?
                    """, (lat, lon, attack_type, event_id))
            except (json.JSONDecodeError, TypeError):
                continue
        
        print("Geolocation migration completed.")
    
    conn.commit()
    
    # Verify final structure
    cursor.execute("PRAGMA table_info(events)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"Final table structure: {final_columns}")
    
    # Show sample data
    cursor.execute("SELECT COUNT(*) FROM events")
    count = cursor.fetchone()[0]
    print(f"Total events in database: {count}")
    
    if count > 0:
        cursor.execute("SELECT id, timestamp, client_ip, country, city, latitude, longitude, attack_type FROM events LIMIT 3")
        print("\nSample records:")
        for row in cursor.fetchall():
            print(f"ID: {row[0][:8]}... | IP: {row[2]} | Location: {row[3]}, {row[4]} | Coords: {row[5]}, {row[6]} | Type: {row[7]}")
    
    conn.close()
    print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()