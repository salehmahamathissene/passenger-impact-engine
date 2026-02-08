from pathlib import Path

file_path = Path("src/pie/pro/billing_routes.py")
content = file_path.read_text()

# Find the _need_env function
import re
match = re.search(r'def _need_env\(name: str\) -> str:.*?\n\n', content, re.DOTALL)
if match:
    print("Found _need_env function:")
    print(match.group(0))
    print("\n" + "="*50)
    
# Check how the Stripe key is being used
if "YOUR_REAL" in content:
    print("⚠️ Found 'YOUR_REAL' placeholder in code")
if "changeme" in content:
    print("⚠️ Found 'changeme' placeholder in code")
    
# Check the create_checkout function
match = re.search(r'@router.post\("/checkout"\).*?def create_checkout.*?\n\n', content, re.DOTALL)
if match:
    print("\nFound create_checkout function (first 20 lines):")
    lines = match.group(0).split('\n')
    for i, line in enumerate(lines[:20]):
        print(f"{i:2}: {line}")
