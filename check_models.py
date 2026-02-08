from pathlib import Path
import importlib.util
import sys

# Try to import models module
spec = importlib.util.spec_from_file_location("models", "src/pie/pro/models.py")
models_module = importlib.util.module_from_spec(spec)

try:
    spec.loader.exec_module(models_module)
    
    print("📋 Available models in pie.pro.models:")
    print("=" * 40)
    
    for attr_name in dir(models_module):
        attr = getattr(models_module, attr_name)
        if hasattr(attr, '__tablename__'):
            print(f"✅ {attr_name}:")
            print(f"   Table name: {attr.__tablename__}")
            print(f"   Columns: {[c.name for c in attr.__table__.columns][:5]}...")
            print()
            
except Exception as e:
    print(f"❌ Error importing models: {e}")
    
    # Try to read the file directly
    content = Path("src/pie/pro/models.py").read_text()
    import re
    class_matches = re.findall(r'class (\w+)\(', content)
    print(f"\nFound classes in file: {', '.join(class_matches)}")
