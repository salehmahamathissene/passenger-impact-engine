#!/usr/bin/env python3
import re

with open('src/pie/pro/enterprise_models.py', 'r') as f:
    content = f.read()

# Check if api_key_hash exists
if 'api_key_hash = Column' not in content:
    # Add it after total_spent field
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        fixed_lines.append(line)
        # Look for total_spent field and add api_key_hash after it
        if 'total_spent = Column(Numeric' in line and i+1 < len(lines):
            # Check next line doesn't already have api_key_hash
            if 'api_key_hash' not in lines[i+1]:
                fixed_lines.append('    api_key_hash = Column(String, nullable=True)')
    
    fixed_content = '\n'.join(fixed_lines)
    
    with open('src/pie/pro/enterprise_models.py', 'w') as f:
        f.write(fixed_content)
    
    print("Fixed: Added api_key_hash to EnterpriseCompany model")
else:
    print("api_key_hash already exists in model")
