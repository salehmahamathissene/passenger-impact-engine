"""
Find and update the main FastAPI app to include billing routes
"""
import os
from pathlib import Path

# Search for main app files
app_files = []
for py_file in Path(".").rglob("*.py"):
    content = py_file.read_text(errors='ignore')
    if 'FastAPI(' in content and 'app = ' in content:
        app_files.append(py_file)
        print(f"Found FastAPI app: {py_file}")

# Look for the most likely one
for app_file in app_files:
    print(f"\n📄 Checking {app_file}")
    content = app_file.read_text()
    
    # Check if it already has billing routes
    if 'billing_routes' in content:
        print("  ✅ Already has billing routes")
    else:
        print("  ❌ Missing billing routes")
        
        # Find where to add the import
        import_section = content.find('import')  # Rough location
        if import_section != -1:
            # Add import after other imports
            lines = content.split('\n')
            new_lines = []
            billing_import_added = False
            
            for line in lines:
                new_lines.append(line)
                if not billing_import_added and ('from' in line or 'import' in line) and '#' not in line:
                    # Add billing import
                    new_lines.append('from src.pie.pro.billing_routes import router as billing_router')
                    billing_import_added = True
            
            # Find where to include the router
            for i, line in enumerate(new_lines):
                if 'app.include_router' in line:
                    # Add billing router after this line
                    new_lines.insert(i + 1, 'app.include_router(billing_router)')
                    break
            
            new_content = '\n'.join(new_lines)
            app_file.write_text(new_content)
            print(f"  ✅ Added billing routes to {app_file}")
            break
