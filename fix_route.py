import re

# Read the file
with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    content = f.read()

# Fix the bulk_create_companies function
# The issue is that background_tasks doesn't have a default value but comes after db which does
# We need to reorder the parameters
pattern = r'async def bulk_create_companies\(\s*companies: List\[CompanyCreate\],\s*background_tasks: BackgroundTasks,\s*db: Session = Depends\(get_db\),\s*api_key: str = Depends\(verify_api_key\)\s*\):'

# Actually, let's find and fix this more carefully
# The parameters should be: companies, db, api_key, background_tasks
lines = content.split('\n')
fixed_lines = []

for i, line in enumerate(lines):
    if 'async def bulk_create_companies' in line:
        # Find the function definition and the next few lines
        func_def = line
        j = i + 1
        while j < len(lines) and '):' not in lines[j] and 'def' not in lines[j]:
            func_def += ' ' + lines[j]
            j += 1
        if j < len(lines) and '):' in lines[j]:
            func_def += ' ' + lines[j]
        
        # Extract and reorder parameters
        params_match = re.search(r'bulk_create_companies\((.*?)\):', func_def, re.DOTALL)
        if params_match:
            params_text = params_match.group(1)
            # Split parameters
            params = [p.strip() for p in params_text.split(',') if p.strip()]
            
            # Reorder: companies, db, api_key, background_tasks
            new_params = []
            for param in params:
                if 'companies:' in param:
                    new_params.insert(0, param)
                elif 'db:' in param:
                    new_params.insert(1, param)
                elif 'api_key:' in param:
                    new_params.insert(2, param)
                elif 'background_tasks:' in param:
                    new_params.insert(3, param)
                else:
                    new_params.append(param)
            
            # Create new function definition
            new_func_def = f"async def bulk_create_companies(\n    " + ",\n    ".join(new_params) + "\n):"
            
            # Replace the old function definition
            # We need to replace from line i to line j
            for k in range(i, min(j+1, len(lines))):
                if k == i:
                    fixed_lines.append(new_func_def.split('\n')[0])
                elif k <= j:
                    # Skip old lines
                    continue
                else:
                    break
            
            # Skip the old lines we're replacing
            i = j
            continue
    
    fixed_lines.append(line)

# Write fixed content
with open('src/pie/pro/enterprise_routes.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("Fixed the function definition!")
