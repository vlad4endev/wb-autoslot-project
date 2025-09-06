#!/usr/bin/env python3
"""
Initialize database migrations
"""

import os
import sys
import subprocess

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def init_migrations():
    """Initialize database migrations"""
    print("🚀 Initializing database migrations...")
    
    # Set environment variables
    os.environ['FLASK_APP'] = 'src/main.py'
    os.environ['FLASK_ENV'] = 'development'
    
    try:
        # Initialize migrations
        print("📁 Creating migrations directory...")
        result = subprocess.run(['flask', 'db', 'init'], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode != 0:
            if 'already exists' in result.stderr:
                print("✅ Migrations directory already exists")
            else:
                print(f"❌ Error initializing migrations: {result.stderr}")
                return False
        
        # Create initial migration
        print("📝 Creating initial migration...")
        result = subprocess.run(['flask', 'db', 'migrate', '-m', 'Initial migration'], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode != 0:
            print(f"❌ Error creating migration: {result.stderr}")
            return False
        
        print("✅ Initial migration created successfully")
        
        # Apply migrations
        print("🔄 Applying migrations...")
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode != 0:
            print(f"❌ Error applying migrations: {result.stderr}")
            return False
        
        print("✅ Migrations applied successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_migration(message):
    """Create a new migration"""
    print(f"📝 Creating migration: {message}")
    
    try:
        result = subprocess.run(['flask', 'db', 'migrate', '-m', message], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode != 0:
            print(f"❌ Error creating migration: {result.stderr}")
            return False
        
        print("✅ Migration created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def apply_migrations():
    """Apply pending migrations"""
    print("🔄 Applying pending migrations...")
    
    try:
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode != 0:
            print(f"❌ Error applying migrations: {result.stderr}")
            return False
        
        print("✅ Migrations applied successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python init_migrations.py init          - Initialize migrations")
        print("  python init_migrations.py migrate <msg> - Create new migration")
        print("  python init_migrations.py upgrade       - Apply migrations")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init':
        success = init_migrations()
    elif command == 'migrate':
        if len(sys.argv) < 3:
            print("❌ Migration message required")
            sys.exit(1)
        message = sys.argv[2]
        success = create_migration(message)
    elif command == 'upgrade':
        success = apply_migrations()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
    
    if success:
        print("🎉 Operation completed successfully!")
        sys.exit(0)
    else:
        print("💥 Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
