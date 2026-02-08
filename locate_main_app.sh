#!/bin/bash
echo "🔍 LOCATING MAIN FASTAPI APP"
echo "============================="

# Look for files with FastAPI
find . -name "*.py" -type f | xargs grep -l "FastAPI" | grep -v __pycache__ | grep -v ".pyc" | head -10

echo ""
echo "📄 Checking likely candidates..."

# Check main.py if exists
if [ -f "src/main.py" ]; then
    echo "src/main.py:"
    grep -n "app\|FastAPI\|include_router" src/main.py | head -20
fi

# Check pie/pro if exists
if [ -f "src/pie/pro/main.py" ]; then
    echo ""
    echo "src/pie/pro/main.py:"
    grep -n "app\|FastAPI\|include_router" src/pie/pro/main.py | head -20
fi

# Check what's running
echo ""
echo "🌐 Current running app endpoints:"
curl -s http://127.0.0.1:8080/openapi.json 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print('Available paths:')
    for path in sorted(data.get('paths', {}).keys()):
        print(f'  {path}')
except:
    print('Could not fetch OpenAPI spec')
"
