import sys
sys.path.append('src')

with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    lines = f.readlines()

# Find and replace the jobs function
new_lines = []
in_jobs_func = False
replaced = False

for i, line in enumerate(lines):
    if '@router.get("/jobs")' in line or 'def list_jobs' in line:
        in_jobs_func = True
    
    if in_jobs_func and '.order_by(desc(' in line:
        # Replace with simple ordering
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(f'{indent}.order_by(EnterpriseJob.created_at.desc())\n')
        replaced = True
        continue
    
    if in_jobs_func and line.strip().startswith('out = []'):
        # We've passed the ordering line
        in_jobs_func = False
    
    if not replaced:
        new_lines.append(line)

# Write back
with open('src/pie/pro/enterprise_routes.py', 'w') as f:
    f.writelines(new_lines)

print('Simplified jobs query ordering')
