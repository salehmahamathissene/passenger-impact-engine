import sys
sys.path.insert(0, 'src')

from pie.pro.settings import settings
from pie.pro.enterprise_models import EnterpriseCompany
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Check settings
print(f"ENTERPRISE_ADMIN_KEY: {settings.ENTERPRISE_ADMIN_KEY[:10]}...")

# Check model
print(f"\nEnterpriseCompany attributes:")
for attr in dir(EnterpriseCompany):
    if not attr.startswith('_'):
        print(f"  {attr}")

# Check if api_key_hash exists
print(f"\nHas api_key_hash: {'api_key_hash' in EnterpriseCompany.__dict__}")
