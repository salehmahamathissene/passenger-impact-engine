with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    content = f.read()

# Split into lines
lines = content.split('\n')

# Find the bulk_create_companies function
in_function = False
function_start = -1
duplicate_found = False

for i, line in enumerate(lines):
    if 'async def bulk_create_companies' in line:
        if not in_function:
            in_function = True
            function_start = i
        else:
            # Found duplicate
            duplicate_found = True
            # Find where this duplicate ends
            j = i
            while j < len(lines) and not lines[j].strip().startswith('def ') and not lines[j].strip().startswith('@router'):
                j += 1
            # Remove duplicate lines
            del lines[i:j]
            break

# Now let's also check if there are duplicate parameter lines within the function
for i in range(len(lines)):
    if 'companies: List[CompanyCreate],' in lines[i]:
        # Check if next line is also a parameter line
        if i+1 < len(lines) and ('background_tasks:' in lines[i+1] or 'db:' in lines[i+1] or 'api_key:' in lines[i+1]):
            # This looks like the start of parameters
            # Find where parameters end
            j = i
            while j < len(lines) and '):' not in lines[j]:
                j += 1
            
            # Check if there are duplicate parameter lines between i and j
            seen = set()
            for k in range(i, j+1):
                line = lines[k].strip()
                if line and not line.startswith('async def'):
                    if line in seen and not line.startswith('@'):
                        # Duplicate line, remove it
                        lines[k] = ''
                    else:
                        seen.add(line)

# Write back
with open('src/pie/pro/enterprise_routes.py', 'w') as f:
    f.write('\n'.join(lines))

print("Cleaned up duplicate function definitions")
