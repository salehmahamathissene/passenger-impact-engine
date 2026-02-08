import os
import sys
sys.path.append('src')

print("🔧 FIXING COMPANY MODEL FOR BILLING")
print("=" * 50)

models_file = 'src/pie/pro/enterprise_models.py'

with open(models_file, 'r') as f:
    content = f.read()

# Check if we have the necessary fields
missing_fields = []
needed_fields = ['plan', 'is_active', 'stripe_customer_id', 'stripe_subscription_id', 'current_period_end']

for field in needed_fields:
    if field not in content:
        missing_fields.append(field)

if missing_fields:
    print(f"Missing fields: {missing_fields}")
    
    # Find where to add the fields (after id and name)
    lines = content.split('\n')
    new_lines = []
    in_company_class = False
    added = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        if 'class EnterpriseCompany(Base):' in line:
            in_company_class = True
        
        # Add fields after the basic ones
        if in_company_class and not added:
            if 'created_at' in line and 'Mapped' in line:
                print("Adding billing fields after created_at...")
                # Add the missing billing fields
                new_lines.append('')
                new_lines.append('    # Billing fields')
                new_lines.append('    plan: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="free")')
                new_lines.append('    is_active: Mapped[bool] = mapped_column(Boolean, default=False)')
                new_lines.append('    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)')
                new_lines.append('    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)')
                new_lines.append('    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)')
                new_lines.append('')
                added = True
    
    # Write back
    with open(models_file, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ Company model updated with billing fields!")
    
    # Show the updated section
    print("\nUpdated EnterpriseCompany class (billing section):")
    print("-" * 50)
    with open(models_file, 'r') as f:
        updated = f.read()
        import re
        company_match = re.search(r'class EnterpriseCompany\(Base\):.*?(?=class|\Z)', updated, re.DOTALL)
        if company_match:
            lines = company_match.group(0).split('\n')
            for line in lines:
                if 'plan' in line or 'is_active' in line or 'stripe' in line or 'current_period' in line:
                    print(f"  {line}")
else:
    print("✅ All billing fields already present in model")
