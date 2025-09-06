#!/usr/bin/env python3
"""
Migration script to add email field to users table
"""

import sqlite3
import os
import sys

def migrate_database():
    """Add email column to users table if it doesn't exist"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found. Please run the application first to create the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if email column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'email' in columns:
            print("✅ Email column already exists in users table")
            return True
        
        # Add email column (without UNIQUE constraint first)
        print("🔄 Adding email column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(120)")
        
        # Create new table with email column and UNIQUE constraint
        print("🔄 Creating new users table with email constraint...")
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone VARCHAR(20) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE,
                password_hash VARCHAR(128) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Copy data from old table to new table
        print("🔄 Copying data to new table...")
        cursor.execute("""
            INSERT INTO users_new (id, phone, password_hash, created_at, is_active)
            SELECT id, phone, password_hash, created_at, is_active FROM users
        """)
        
        # Drop old table
        print("🔄 Dropping old table...")
        cursor.execute("DROP TABLE users")
        
        # Rename new table
        print("🔄 Renaming new table...")
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        # Commit changes
        conn.commit()
        print("✅ Email column added successfully")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'email' in columns:
            print("✅ Migration completed successfully")
            return True
        else:
            print("❌ Migration failed - email column not found after adding")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    success = migrate_database()
    
    if success:
        print("🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)
