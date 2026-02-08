# Read the file
with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    lines = f.readlines()

# Find and fix the export_companies function
for i in range(len(lines)):
    if 'async def export_companies' in lines[i]:
        # Find the function definition
        j = i
        while j < len(lines) and '):' not in lines[j]:
            j += 1
        
        if j < len(lines):
            # Reconstruct with correct parameter order
            lines[i:j+1] = [
                '@router.post("/exports/companies", response_model=dict)\n',
                'async def export_companies(\n',
                '    background_tasks: BackgroundTasks,\n',
                '    format: str = Query("csv", regex="^(csv|json|xlsx)$"),\n',
                '    filters: Optional[Dict[str, Any]] = Query(None),\n',
                '    db: Session = Depends(get_db),\n',
                '    api_key: str = Depends(verify_api_key)\n',
                '):\n'
            ]
        break

# Write back
with open('src/pie/pro/enterprise_routes.py', 'w') as f:
    f.writelines(lines)

print("Fixed export_companies function")
