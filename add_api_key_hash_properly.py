with open('src/pie/pro/enterprise_models.py', 'r') as f:
    lines = f.readlines()

# Find the line with total_spent
for i, line in enumerate(lines):
    if 'total_spent:' in line and 'mapped_column' in line:
        # Insert api_key_hash after total_spent
        indent = len(line) - len(line.lstrip())
        api_key_line = ' ' * indent + 'api_key_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)\n'
        lines.insert(i + 1, api_key_line)
        break

with open('src/pie/pro/enterprise_models.py', 'w') as f:
    f.writelines(lines)

print("Added api_key_hash field after total_spent")
