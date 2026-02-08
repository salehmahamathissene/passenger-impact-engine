#!/bin/bash
echo "🐳 TESTING DOCKER POSTGRESQL CONNECTION"
echo "========================================"

python3 -c "
import psycopg2
import time

max_attempts = 10
for i in range(max_attempts):
    try:
        print(f'Attempt {i+1}/{max_attempts}...')
        conn = psycopg2.connect(
            dbname='pie',
            user='pieuser',
            password='piepass123',
            host='localhost',
            port='5432'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version()')
        version = cursor.fetchone()[0]
        print(f'✅ Connected to PostgreSQL: {version}')
        
        # List databases
        cursor.execute('SELECT datname FROM pg_database WHERE datistemplate = false;')
        dbs = cursor.fetchall()
        print(f'📊 Databases: {[db[0] for db in dbs]}')
        
        conn.close()
        break
    except Exception as e:
        print(f'❌ Attempt {i+1} failed: {e}')
        if i < max_attempts - 1:
            time.sleep(2)
        else:
            print('Failed to connect after multiple attempts')
"
