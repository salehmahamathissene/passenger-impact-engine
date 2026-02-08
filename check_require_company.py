import inspect
from pathlib import Path

# Read the enterprise_routes.py file to see what require_company returns
content = Path("src/pie/pro/enterprise_routes.py").read_text()

# Find the require_company function
import re
match = re.search(r'def require_company\(.*?\).*?:.*?\n', content, re.DOTALL)
if match:
    print("require_company function signature:")
    print(match.group(0))
    
# Look for what it returns
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'def require_company' in line:
        # Look at next few lines
        for j in range(i, min(i+20, len(lines))):
            if 'return' in lines[j]:
                print(f"\nLine {j+1}: {lines[j]}")
                # Show context
                for k in range(max(0, j-2), min(len(lines), j+3)):
                    print(f"{k+1:4}: {lines[k]}")
                break
        break
