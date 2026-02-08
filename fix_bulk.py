import re

# Read the file
with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    lines = f.readlines()

# Find the bulk_create_companies function
in_function = False
function_start = -1
function_end = -1

for i, line in enumerate(lines):
    if 'async def bulk_create_companies' in line:
        in_function = True
        function_start = i
    elif in_function and line.strip() == '' and function_end == -1:
        # Found the end of the function (empty line after it)
        function_end = i
        break

if function_start != -1 and function_end == -1:
    function_end = len(lines)

if function_start != -1:
    # Extract the function
    function_lines = lines[function_start:function_end]
    
    # Parse the function definition line
    def_line = function_lines[0]
    
    # Fix the parameter order
    # Current: companies: List[CompanyCreate], background_tasks: BackgroundTasks, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)
    # Should be: companies: List[CompanyCreate], db: Session = Depends(get_db), api_key: str = Depends(verify_api_key), background_tasks: BackgroundTasks
    
    # Simple fix: just rewrite the function definition
    new_def_line = """@router.post("/bulk/companies", response_model=dict)
async def bulk_create_companies(
    companies: List[CompanyCreate],
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks
):"""
    
    # Replace the old function definition
    lines[function_start] = new_def_line + '\n'
    
    # Write back
    with open('src/pie/pro/enterprise_routes.py', 'w') as f:
        f.writelines(lines)
    
    print("Fixed the bulk_create_companies function!")
else:
    print("Could not find bulk_create_companies function")
