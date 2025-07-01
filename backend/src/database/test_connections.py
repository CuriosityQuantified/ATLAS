#!/usr/bin/env python3
"""
ATLAS Database Connection Testing
Simple utility to test database connections and basic operations
"""

import sys
import psycopg2
from datetime import datetime
import uuid

# Database configuration (matches setup_databases.py)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'databases': {
        'atlas_main': {
            'user': 'atlas_main_user',
            'password': 'atlas_main_password'
        },
        'atlas_agents': {
            'user': 'atlas_agents_user', 
            'password': 'atlas_agents_password'
        },
        'atlas_memory': {
            'user': 'atlas_memory_user',
            'password': 'atlas_memory_password'
        }
    }
}

def test_basic_connection(db_name, config):
    """Test basic database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=db_name,
            user=config['user'],
            password=config['password']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT current_database(), current_user, now();")
        db, user, timestamp = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"✅ {db_name}: Connected as {user} at {timestamp}")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ {db_name}: Connection failed - {e}")
        return False

def test_atlas_main_operations():
    """Test basic operations on atlas_main database"""
    print("\n🔧 Testing atlas_main operations...")
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='atlas_main',
            user=DB_CONFIG['databases']['atlas_main']['user'],
            password=DB_CONFIG['databases']['atlas_main']['password']
        )
        
        cursor = conn.cursor()
        
        # Test 1: Insert a test task
        test_task_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO tasks (task_id, project_name, status, priority)
            VALUES (%s, %s, %s, %s)
        """, (test_task_id, 'test_project', 'pending', 'medium'))
        
        # Test 2: Insert a test agent
        test_agent_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO agents (agent_id, agent_type, team, persona_config)
            VALUES (%s, %s, %s, %s)
        """, (test_agent_id, 'test_agent', 'research', '{"test": true}'))
        
        # Test 3: Query the data back
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE project_name = %s", ('test_project',))
        task_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agents WHERE agent_type = %s", ('test_agent',))
        agent_count = cursor.fetchone()[0]
        
        # Test 4: Test the view
        cursor.execute("SELECT * FROM task_summary_view WHERE project_name = %s", ('test_project',))
        summary = cursor.fetchone()
        
        # Clean up test data
        cursor.execute("DELETE FROM tasks WHERE task_id = %s", (test_task_id,))
        cursor.execute("DELETE FROM agents WHERE agent_id = %s", (test_agent_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ atlas_main: Created and queried {task_count} task(s) and {agent_count} agent(s)")
        print(f"✅ atlas_main: Task summary view working")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ atlas_main operations failed: {e}")
        return False

def test_atlas_agents_operations():
    """Test basic operations on atlas_agents database"""
    print("\n🔧 Testing atlas_agents operations...")
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='atlas_agents',
            user=DB_CONFIG['databases']['atlas_agents']['user'],
            password=DB_CONFIG['databases']['atlas_agents']['password']
        )
        
        cursor = conn.cursor()
        
        # Test 1: Create agent session using function
        test_agent_id = str(uuid.uuid4())
        test_task_id = str(uuid.uuid4())
        
        cursor.execute("""
            SELECT create_agent_session(%s, %s, %s)
        """, (test_agent_id, test_task_id, '{"status": "testing"}'))
        
        session_id = cursor.fetchone()[0]
        
        # Test 2: Add memory using function
        cursor.execute("""
            SELECT add_agent_memory(%s, %s, %s, %s)
        """, (session_id, 'user', 'Test message', 10))
        
        memory_id = cursor.fetchone()[0]
        
        # Test 3: Query the active sessions view
        cursor.execute("SELECT * FROM active_sessions_view WHERE session_id = %s", (session_id,))
        session_data = cursor.fetchone()
        
        # Test 4: End session using function
        cursor.execute("SELECT end_agent_session(%s)", (session_id,))
        success = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ atlas_agents: Created session {session_id}")
        print(f"✅ atlas_agents: Added memory {memory_id}")
        print(f"✅ atlas_agents: Session ended successfully: {success}")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ atlas_agents operations failed: {e}")
        return False

def test_atlas_memory_operations():
    """Test basic operations on atlas_memory database"""
    print("\n🔧 Testing atlas_memory operations...")
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='atlas_memory',
            user=DB_CONFIG['databases']['atlas_memory']['user'],
            password=DB_CONFIG['databases']['atlas_memory']['password']
        )
        
        cursor = conn.cursor()
        
        # Test 1: Create memory chunk using function
        test_source_id = str(uuid.uuid4())
        cursor.execute("""
            SELECT create_memory_chunk(%s, %s, %s, %s)
        """, (test_source_id, 'task', 'This is a test memory chunk', 1))
        
        chunk_id = cursor.fetchone()[0]
        
        # Test 2: Create knowledge entity using function
        cursor.execute("""
            SELECT upsert_knowledge_entity(%s, %s, %s)
        """, ('concept', 'test_concept', 'A test concept for validation'))
        
        entity_id = cursor.fetchone()[0]
        
        # Test 3: Search memory chunks
        cursor.execute("""
            SELECT * FROM search_memory_chunks(%s, %s, %s)
        """, ('test memory', 'task', 5))
        
        search_results = cursor.fetchall()
        
        # Test 4: Check views
        cursor.execute("SELECT * FROM knowledge_entity_summary")
        entity_summary = cursor.fetchall()
        
        cursor.execute("SELECT * FROM memory_chunk_statistics")
        chunk_stats = cursor.fetchall()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ atlas_memory: Created chunk {chunk_id}")
        print(f"✅ atlas_memory: Created entity {entity_id}")
        print(f"✅ atlas_memory: Found {len(search_results)} search result(s)")
        print(f"✅ atlas_memory: Views working - {len(entity_summary)} entity types, {len(chunk_stats)} chunk types")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ atlas_memory operations failed: {e}")
        return False

def test_model_pricing_data():
    """Test model pricing data availability"""
    print("\n🔧 Testing model pricing data...")
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='atlas_main',
            user=DB_CONFIG['databases']['atlas_main']['user'],
            password=DB_CONFIG['databases']['atlas_main']['password']
        )
        
        cursor = conn.cursor()
        
        # Test pricing data
        cursor.execute("SELECT COUNT(*) FROM model_pricing")
        total_models = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT provider) FROM model_pricing")
        providers = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT provider, COUNT(*) as model_count 
            FROM model_pricing 
            GROUP BY provider 
            ORDER BY model_count DESC
        """)
        provider_breakdown = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Model pricing: {total_models} models from {providers} providers")
        for provider, count in provider_breakdown:
            print(f"  • {provider}: {count} models")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Model pricing test failed: {e}")
        return False

def main():
    print("🔍 ATLAS Database Connection Testing")
    print("=" * 40)
    
    success_count = 0
    total_tests = 0
    
    # Test basic connections
    print("\n📡 Testing basic connections...")
    for db_name, config in DB_CONFIG['databases'].items():
        total_tests += 1
        if test_basic_connection(db_name, config):
            success_count += 1
    
    # Test database operations
    operation_tests = [
        test_atlas_main_operations,
        test_atlas_agents_operations, 
        test_atlas_memory_operations,
        test_model_pricing_data
    ]
    
    for test_func in operation_tests:
        total_tests += 1
        if test_func():
            success_count += 1
    
    # Summary
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All database tests passed! ATLAS databases are ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the database setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())