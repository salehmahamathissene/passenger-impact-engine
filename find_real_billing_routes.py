"""
Find the REAL billing routes file
"""
import os
from pathlib import Path

# Search for billing_routes.py
project_root = Path(".")
for py_file in project_root.rglob("billing_routes.py"):
    print(f"Found: {py_file}")
    
    # Check if it's the enterprise one
    if "enterprise" in str(py_file) or "pro" in str(py_file):
        print(f"📄 Enterprise billing routes at: {py_file}")
        print("\nFirst 50 lines:")
        try:
            content = py_file.read_text()
            lines = content.split('\n')
            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3}: {line}")
        except:
            print("Could not read file")
        break

# Check what routes are actually registered
print("\n🔍 Checking FastAPI routes...")
try:
    import subprocess
    result = subprocess.run(['curl', '-s', 'http://127.0.0.1:8080/openapi.json'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        import json
        openapi = json.loads(result.stdout)
        print("Available paths:")
        for path in sorted(openapi.get('paths', {}).keys()):
            if 'billing' in path or 'enterprise' in path:
                print(f"  {path}")
    else:
        print("Could not fetch OpenAPI spec")
except:
    print("Failed to check routes")
