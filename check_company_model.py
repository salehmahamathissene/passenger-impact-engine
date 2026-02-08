import os
import sys
sys.path.append('src')

print("🔍 CHECKING ENTERPRISE COMPANY MODEL")
print("=" * 50)

# Check enterprise_models.py for Company fields
models_file = 'src/pie/pro/enterprise_models.py'

with open(models_file, 'r') as f:
    content = f.read()
    
    # Look for EnterpriseCompany class
    import re
    
    # Find the EnterpriseCompany class definition
    company_match = re.search(r'class EnterpriseCompany\(Base\):.*?(?=class|\Z)', content, re.DOTALL)
    
    if company_match:
        company_code = company_match.group(0)
        print("EnterpriseCompany class found:")
        print("-" * 40)
        
        # Extract column definitions
        lines = company_code.split('\n')
        for line in lines:
            if 'Mapped' in line or 'mapped_column' in line or 'relationship' in line:
                print(f"  {line.strip()}")
        
        # Check for specific fields needed by billing routes
        print("\n🔎 Checking for billing-specific fields:")
        needed_fields = ['plan', 'is_active', 'stripe_customer_id', 'stripe_subscription_id', 'current_period_end']
        
        for field in needed_fields:
            if field in company_code:
                print(f"  ✅ {field}: Found")
            else:
                print(f"  ❌ {field}: MISSING - billing routes will fail!")
    else:
        print("❌ EnterpriseCompany class not found!")
