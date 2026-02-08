import os
from pathlib import Path

# Your correct Stripe key (from earlier in the conversation)
CORRECT_STRIPE_KEY = "sk_test_REDACTED"

# Read the .env.working file
env_path = Path(".env.working")
if env_path.exists():
    content = env_path.read_text()
    
    # Fix the Stripe key
    lines = content.splitlines()
    fixed_lines = []
    for line in lines:
        if line.startswith("export STRIPE_SECRET_KEY="):
            fixed_lines.append(f'export STRIPE_SECRET_KEY="{CORRECT_STRIPE_KEY}"')
        elif line.startswith("export STRIPE_PRICE_PRO_MONTHLY="):
            # Use the price you just created
            fixed_lines.append('export STRIPE_PRICE_PRO_MONTHLY="price_1Sxwg1GTsbjFmuVQTy0qQbfh"')
        else:
            fixed_lines.append(line)
    
    # Write back
    env_path.write_text("\n".join(fixed_lines))
    print("✅ Fixed .env.working file")
    
    # Show the fixed lines
    print("\nUpdated environment:")
    for line in fixed_lines:
        if "STRIPE_" in line or "API_KEY" in line or "COMPANY_ID" in line:
            print(f"  {line[:60]}...")
else:
    print("❌ .env.working not found")
