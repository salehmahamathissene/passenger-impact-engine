import re

with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    content = f.read()

# Find all function definitions
function_pattern = r'async def (\w+)\(([^)]*)\):'
functions = re.findall(function_pattern, content, re.MULTILINE | re.DOTALL)

for func_name, params in functions:
    params_list = [p.strip() for p in params.split(',') if p.strip()]
    
    # Check for parameters with defaults after parameters without defaults
    found_default = False
    for i, param in enumerate(params_list):
        if '=' in param:
            found_default = True
        elif found_default and '=' not in param:
            print(f"WARNING: Function '{func_name}' has parameter '{param}' without default after parameters with defaults")
            print(f"  All parameters: {params_list}")
            break

print("Check complete!")
