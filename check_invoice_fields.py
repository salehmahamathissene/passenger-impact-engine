import sys
sys.path.insert(0, 'src')

from pie.pro.enterprise_models import EnterpriseInvoice
import inspect

print("EnterpriseInvoice fields:")
for name, obj in inspect.getmembers(EnterpriseInvoice):
    if not name.startswith('_'):
        print(f"  {name}: {type(obj).__name__}")
