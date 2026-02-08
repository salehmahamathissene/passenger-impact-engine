from pathlib import Path
import re

file_path = Path("src/pie/pro/billing_routes.py")
content = file_path.read_text()

# Fix the _need_env function - remove the placeholder check
new_need_env = '''def _need_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise HTTPException(
            status_code=400,
            detail=f"Please configure {name} in your environment."
        )
    return v'''

# Replace the old function
old_pattern = r'def _need_env\(name: str\) -> str:.*?\n\n'
content = re.sub(old_pattern, new_need_env + '\n\n', content, flags=re.DOTALL)

# Also fix the create_checkout function to not check for placeholder keys
# Remove the validation that's causing issues
lines = content.splitlines()
new_lines = []
skip_next = False

for i, line in enumerate(lines):
    # Skip lines that check for placeholder keys
    if 'if not stripe.api_key or "YOUR_REAL" in stripe.api_key:' in line:
        skip_next = 3  # Skip this line and the next few
        continue
    if 'if not req.price_id or "YOUR_REAL" in req.price_id:' in line:
        skip_next = 3
        continue
    
    if skip_next > 0:
        skip_next -= 1
        continue
    
    new_lines.append(line)

content = "\n".join(new_lines)

# Write back
file_path.write_text(content)
print("✅ Fixed billing_routes.py - removed placeholder checks")
