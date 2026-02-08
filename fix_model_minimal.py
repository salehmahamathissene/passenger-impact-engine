with open('src/pie/pro/enterprise_models.py', 'r') as f:
    lines = f.readlines()

# Find where to insert api_key_hash
for i, line in enumerate(lines):
    if 'total_spent = Column(' in line:
        # Insert after total_spent
        lines.insert(i + 1, '    api_key_hash = Column(String, nullable=True)\n')
        break

with open('src/pie/pro/enterprise_models.py', 'w') as f:
    f.writelines(lines)

print("Added api_key_hash field to model")
