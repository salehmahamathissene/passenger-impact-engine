with open('src/pie/pro/enterprise_routes.py', 'r') as f:
    content = f.read()

# Replace issued_at with invoice_date
if 'EnterpriseInvoice.issued_at' in content:
    content = content.replace('EnterpriseInvoice.issued_at', 'EnterpriseInvoice.invoice_date')
    print("Fixed issued_at → invoice_date")
    
    with open('src/pie/pro/enterprise_routes.py', 'w') as f:
        f.write(content)
else:
    print("Already fixed or different issue")
