#!/usr/bin/env python3
"""
Database Copy Script for PostgreSQL
Copy database 'dynamic' to 'dynamic1'
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection_params():
    """Get database connection parameters from environment variables."""
    return {
        'host': os.getenv('POSTGRES_SERVER', '149.200.251.12'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'user': os.getenv('POSTGRES_USER', 'husain'),
        'password': os.getenv('POSTGRES_PASSWORD', 'tt55oo77'),
    }

def copy_database():
    """Copy database 'dynamic' to 'dynamic1'."""
    
    # Get connection parameters
    conn_params = get_db_connection_params()
    source_db = 'dynamic'
    target_db = 'dynamic1'
    
    print(f"Starting database copy from '{source_db}' to '{target_db}'...")
    print(f"Host: {conn_params['host']}:{conn_params['port']}")
    print(f"User: {conn_params['user']}")
    
    try:
        # Connect to PostgreSQL server (not to a specific database)
        print("\n1. Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=conn_params['host'],
            port=conn_params['port'],
            user=conn_params['user'],
            password=conn_params['password'],
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if source database exists
        print(f"\n2. Checking if source database '{source_db}' exists...")
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (source_db,))
        if not cur.fetchone():
            print(f"❌ Error: Source database '{source_db}' does not exist!")
            return False
        
        print(f"✅ Source database '{source_db}' found.")
        
        # Check if target database already exists
        print(f"\n3. Checking if target database '{target_db}' already exists...")
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
        if cur.fetchone():
            print(f"⚠️  Target database '{target_db}' already exists!")
            response = input("Do you want to drop it and recreate? (y/N): ").lower().strip()
            if response == 'y':
                print(f"Dropping existing database '{target_db}'...")
                # Terminate connections to target database
                cur.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid()
                """, (target_db,))
                cur.execute(f'DROP DATABASE "{target_db}"')
                print(f"✅ Dropped existing database '{target_db}'.")
            else:
                print("❌ Operation cancelled.")
                return False
        
        # Create the new database by copying from the source
        print(f"\n4. Creating database '{target_db}' as a copy of '{source_db}'...")
        cur.execute(f'CREATE DATABASE "{target_db}" WITH TEMPLATE "{source_db}"')
        
        print(f"✅ Successfully created database '{target_db}' as a copy of '{source_db}'!")
        
        # Get database sizes for verification
        print(f"\n5. Verifying database copy...")
        cur.execute("""
            SELECT datname, pg_size_pretty(pg_database_size(datname)) as size
            FROM pg_database 
            WHERE datname IN (%s, %s)
            ORDER BY datname
        """, (source_db, target_db))
        
        results = cur.fetchall()
        print("\nDatabase sizes:")
        for db_name, size in results:
            print(f"  {db_name}: {size}")
        
        # Get table counts for verification
        print(f"\n6. Comparing table counts...")
        
        # Check source database tables
        source_conn = psycopg2.connect(**conn_params, database=source_db)
        source_cur = source_conn.cursor()
        source_cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        """)
        source_table_count = source_cur.fetchone()[0]
        source_conn.close()
        
        # Check target database tables
        target_conn = psycopg2.connect(**conn_params, database=target_db)
        target_cur = target_conn.cursor()
        target_cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        """)
        target_table_count = target_cur.fetchone()[0]
        target_conn.close()
        
        print(f"  {source_db}: {source_table_count} tables")
        print(f"  {target_db}: {target_table_count} tables")
        
        if source_table_count == target_table_count:
            print("✅ Table counts match - copy appears successful!")
        else:
            print("⚠️  Table counts don't match - there might be an issue with the copy.")
        
        # Close connections
        cur.close()
        conn.close()
        
        print(f"\n🎉 Database copy completed successfully!")
        print(f"You can now connect to the new database '{target_db}' using the same credentials.")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def main():
    """Main function."""
    print("=" * 60)
    print("PostgreSQL Database Copy Utility")
    print("=" * 60)
    print("Starting script execution...")
    print(f"Python path: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    
    # Verify environment variables
    required_vars = ['POSTGRES_SERVER', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file.")
        sys.exit(1)
    
    # Perform the copy
    success = copy_database()
    
    if success:
        print("\n✅ Database copy operation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Database copy operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
