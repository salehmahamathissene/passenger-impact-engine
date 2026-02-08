with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    lines = f.readlines()

# Find bulk_create_companies
for i in range(len(lines)):
    if 'async def bulk_create_companies' in lines[i]:
        # Find the end of function definition
        j = i
        while j < len(lines) and '):' not in lines[j]:
            j += 1
        
        if j < len(lines):
            # Fix parameter order
            lines[i:j+1] = [
                '@router.post("/bulk/companies", response_model=dict)\n',
                'async def bulk_create_companies(\n',
                '    companies: List[CompanyCreate],\n',
                '    db: Session = Depends(get_db),\n',
                '    api_key: str = Depends(verify_api_key),\n',
                '    background_tasks: BackgroundTasks\n',
                '):\n'
            ]
        break

with open('src/pie/pro/enterprise_routes.py', 'w') as f:
    f.writelines(lines)

print("Fixed bulk_create_companies function")
