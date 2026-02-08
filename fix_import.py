import re

with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    content = f.read()

# Fix import
content = content.replace(
    'from .simple_queue import enqueue_job as enqueue_enterprise_job',
    'from .queue import enqueue_enterprise_job'
)

# Write back
with open('src/pie/pro/enterprise_routes.py', 'w') as f:
    f.write(content)

print('Fixed import back to original')
