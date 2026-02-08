#!/bin/bash
echo "🔍 CHECKING PROJECT STRUCTURE"
echo "============================="

echo ""
echo "1️⃣ Python Path and Imports:"
export PYTHONPATH="$PWD/src:$PYTHONPATH"
python3 -c "
import sys
print('Python path:')
for path in sys.path:
    if 'portfolio' in path or 'site-packages' not in path:
        print(f'  {path}')

print('\\nTrying to import pie modules...')
try:
    from pie.pro import enterprise_models
    print('✅ enterprise_models imports successfully')
    
    # Check if database module exists
    try:
        from pie.pro.database import Base
        print('✅ database.Base imports successfully')
    except ImportError as e:
        print(f'❌ database.Base import failed: {e}')
        
except ImportError as e:
    print(f'❌ Import error: {e}')
"

echo ""
echo "2️⃣ Project Directory Structure:"
find src -name "*.py" -type f | head -20 | sort

echo ""
echo "3️⃣ Check for database.py file:"
find . -name "database.py" -o -name "*database*.py" | grep -v __pycache__

echo ""
echo "4️⃣ Check enterprise_models.py content:"
if [ -f "src/pie/pro/enterprise_models.py" ]; then
    grep -n "class.*Base" src/pie/pro/enterprise_models.py || echo "No Base class found in models"
else
    echo "❌ enterprise_models.py not found!"
fi
