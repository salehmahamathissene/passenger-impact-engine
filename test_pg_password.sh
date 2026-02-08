#!/bin/bash
echo "🔐 TESTING POSTGRESQL PASSWORD CONNECTION"
echo "========================================="

python3 -c "
import psycopg2
import os

# Test with password
try:
    print('Testing connection with password...')
    conn = psycopg2.connect(
        dbname='passenger_impact_prod',
        user='saleh',
        password='M00dle!!',
        host='localhost',
        port='5432'
    )
    print('✅ Password authentication SUCCESS!')
    
    # Check if database exists
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    print('✅ Database query SUCCESS!')
    
    # List tables
    cursor.execute(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    \"\"\")
    tables = cursor.fetchall()
    print(f'📊 Found {len(tables)} tables')
    for table in tables:
        print(f'  - {table[0]}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ Connection failed: {e}')
    
    # Try to create database if it doesn't exist
    print('\\nTrying to create database...')
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            dbname='postgres',
            user='saleh',
            password='M00dle!!',
            host='localhost',
            port='5432'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute('CREATE DATABASE passenger_impact_prod')
        print('✅ Database created!')
        conn.close()
    except Exception as e2:
        print(f'❌ Could not create database: {e2}')
        print('\\nTry: createdb passenger_impact_prod')
"
