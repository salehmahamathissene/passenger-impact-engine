"""
REAL update to enterprise models - not fake
"""
from pathlib import Path
import re

models_path = Path("src/pie/pro/enterprise_models.py")
content = models_path.read_text()

print("Current content length:", len(content))

# Add SubscriptionStatus enum after JobStatus
jobstatus_end = content.find("class JobStatus")
if jobstatus_end != -1:
    # Find the end of JobStatus class
    jobstatus_class_end = content.find("\n\n", jobstatus_end)
    if jobstatus_class_end == -1:
        jobstatus_class_end = len(content)
    
    # Insert SubscriptionStatus
    subscription_enum = '''


class SubscriptionStatus(str, enum.Enum):
    """Stripe subscription statuses"""
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    unpaid = "unpaid"
    incomplete = "incomplete"
    incomplete_expired = "incomplete_expired"
'''
    
    new_content = content[:jobstatus_class_end] + subscription_enum + content[jobstatus_class_end:]
    content = new_content

# Update EnterpriseCompany billing fields
# Find the billing fields section
billing_start = content.find('    # Billing fields')
if billing_start != -1:
    # Find the end of billing fields (before updated_at)
    billing_end = content.find('    updated_at:', billing_start)
    
    if billing_end != -1:
        # Replace the billing fields
        new_billing_fields = '''    # Billing fields
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    subscription_status: Mapped[Optional[SubscriptionStatus]] = mapped_column(Enum(SubscriptionStatus), nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
'''
        
        # Replace from billing_start to billing_end
        content = content[:billing_start] + new_billing_fields + content[billing_end:]

# Write back
models_path.write_text(content)
print(f"✅ Updated {models_path}")

# Verify
print("\nVerifying update...")
with open(models_path, 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'subscription_status' in line or 'SubscriptionStatus' in line:
            print(f"Line {i+1}: {line.strip()}")
