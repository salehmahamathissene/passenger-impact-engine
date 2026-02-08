with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    content = f.read()

# Fix job field mismatches
replacements = [
    ('job.finished_at', 'job.updated_at'),
    ('job.started_at', 'job.created_at'),
    ('EnterpriseJob.finished_at', 'EnterpriseJob.updated_at'),
    ('EnterpriseJob.started_at', 'EnterpriseJob.created_at'),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed {old} → {new}")

with open('src/pie/pro/enterprise_routes.py', 'w') as f:
    f.write(content)
