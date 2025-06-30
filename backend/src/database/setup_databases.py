#!/usr/bin/env python3
"""
ATLAS Database Setup Utility
Automates the creation and initialization of all ATLAS databases
"""

import os
import sys
import subprocess
import psycopg2
from pathlib import Path
import time
import argparse

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'superuser': 'postgres',
    'superuser_password': None,  # Will prompt if needed
    'databases': {
        'atlas_main': {
            'user': 'atlas_main_user',
            'password': 'atlas_main_password',
            'init_script': 'init_atlas_main.sql'
        },
        'atlas_agents': {
            'user': 'atlas_agents_user', 
            'password': 'atlas_agents_password',
            'init_script': 'init_atlas_agents.sql'
        },
        'atlas_memory': {
            'user': 'atlas_memory_user',
            'password': 'atlas_memory_password', 
            'init_script': 'init_atlas_memory.sql'
        }
    }
}

def check_postgresql_running():
    """Check if PostgreSQL is running"""
    try:
        result = subprocess.run(['pg_isready', '-h', DB_CONFIG['host'], '-p', str(DB_CONFIG['port'])], 
                               capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ PostgreSQL tools not found. Please install PostgreSQL.")
        return False

def get_script_directory():
    """Get the directory containing the database scripts"""
    return Path(__file__).parent

def create_databases_and_users():
    """Create databases and users using master script"""
    script_dir = get_script_directory()
    master_script = script_dir / 'init_all_databases.sql'
    
    if not master_script.exists():
        raise FileNotFoundError(f"Master script not found: {master_script}")
    
    print("🔧 Creating databases and users...")
    
    # Connect as superuser to create databases
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres',  # Connect to default database
            user=DB_CONFIG['superuser'],
            password=DB_CONFIG['superuser_password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Read and execute master script
        with open(master_script, 'r') as f:
            script_content = f.read()
        
        # Split by \c commands and execute separately
        commands = script_content.split('\\c')
        
        # Execute first part (database and user creation)
        first_commands = commands[0]
        for statement in first_commands.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except psycopg2.Error as e:
                    if "already exists" not in str(e):
                        print(f"⚠️  Warning: {e}")
        
        cursor.close()
        conn.close()
        print("✅ Databases and users created successfully")
        
    except psycopg2.Error as e:
        print(f"❌ Error creating databases: {e}")
        raise

def initialize_database(db_name, config):
    """Initialize a specific database with its schema"""
    script_dir = get_script_directory()
    init_script = script_dir / config['init_script']
    
    if not init_script.exists():
        raise FileNotFoundError(f"Init script not found: {init_script}")
    
    print(f"🔧 Initializing {db_name} database...")
    
    try:
        # Connect to the specific database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=db_name,
            user=config['user'],
            password=config['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Read and execute init script
        with open(init_script, 'r') as f:
            script_content = f.read()
        
        # Execute the script
        cursor.execute(script_content)
        
        cursor.close()
        conn.close()
        print(f"✅ {db_name} database initialized successfully")
        
    except psycopg2.Error as e:
        print(f"❌ Error initializing {db_name}: {e}")
        raise

def test_database_connections():
    """Test connections to all databases"""
    print("🔍 Testing database connections...")
    
    for db_name, config in DB_CONFIG['databases'].items():
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=db_name,
                user=config['user'],
                password=config['password']
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            print(f"✅ {db_name}: Connection successful")
            
        except psycopg2.Error as e:
            print(f"❌ {db_name}: Connection failed - {e}")
            return False
    
    return True

def verify_table_creation():
    """Verify that tables were created successfully"""
    print("🔍 Verifying table creation...")
    
    expected_tables = {
        'atlas_main': ['tasks', 'agents', 'executions', 'file_metadata', 'project_metrics', 'model_pricing'],
        'atlas_agents': ['agent_sessions', 'agent_memory', 'agent_tools', 'agent_performance', 'agent_collaborations'],
        'atlas_memory': ['memory_chunks', 'knowledge_entities', 'document_metadata', 'task_summaries', 'knowledge_relationships']
    }
    
    for db_name, tables in expected_tables.items():
        config = DB_CONFIG['databases'][db_name]
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=db_name,
                user=config['user'],
                password=config['password']
            )
            
            cursor = conn.cursor()
            
            for table in tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table,))
                
                exists = cursor.fetchone()[0]
                if exists:
                    print(f"✅ {db_name}.{table}: Table exists")
                else:
                    print(f"❌ {db_name}.{table}: Table missing")
                    return False
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e:
            print(f"❌ Error verifying {db_name}: {e}")
            return False
    
    return True

def setup_file_storage_directories():
    """Create file storage directory structure"""
    print("📁 Setting up file storage directories...")
    
    base_dir = Path("/data/files")
    file_types = ['images', 'audio', 'video', '3d_models', 'documents']
    
    try:
        # Create base directory
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each file type
        for file_type in file_types:
            (base_dir / file_type).mkdir(exist_ok=True)
        
        print(f"✅ File storage directories created at {base_dir}")
        return True
        
    except PermissionError:
        print(f"⚠️  Permission denied creating {base_dir}. You may need to run with sudo or create manually.")
        return False
    except Exception as e:
        print(f"❌ Error creating file storage directories: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Setup ATLAS databases')
    parser.add_argument('--skip-verification', action='store_true', help='Skip table verification')
    parser.add_argument('--recreate', action='store_true', help='Drop and recreate databases')
    parser.add_argument('--superuser-password', help='PostgreSQL superuser password')
    
    args = parser.parse_args()
    
    if args.superuser_password:
        DB_CONFIG['superuser_password'] = args.superuser_password
    
    print("🚀 ATLAS Database Setup Starting...")
    print("=" * 50)
    
    # Check PostgreSQL is running
    if not check_postgresql_running():
        print("❌ PostgreSQL is not running. Please start PostgreSQL and try again.")
        sys.exit(1)
    
    try:
        # Step 1: Create databases and users
        create_databases_and_users()
        time.sleep(1)  # Brief pause for database creation
        
        # Step 2: Initialize each database
        for db_name, config in DB_CONFIG['databases'].items():
            initialize_database(db_name, config)
            time.sleep(0.5)
        
        # Step 3: Test connections
        if not test_database_connections():
            print("❌ Database connection tests failed")
            sys.exit(1)
        
        # Step 4: Verify table creation
        if not args.skip_verification:
            if not verify_table_creation():
                print("❌ Table verification failed")
                sys.exit(1)
        
        # Step 5: Setup file storage
        setup_file_storage_directories()
        
        print("\n" + "=" * 50)
        print("🎉 ATLAS Database Setup Complete!")
        print("\nDatabases created:")
        for db_name in DB_CONFIG['databases'].keys():
            print(f"  • {db_name}")
        
        print("\nConnection details:")
        print(f"  • Host: {DB_CONFIG['host']}")
        print(f"  • Port: {DB_CONFIG['port']}")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()