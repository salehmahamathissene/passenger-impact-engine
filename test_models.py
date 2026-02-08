import sys
sys.path.insert(0, 'src')

try:
    from pie.pro.enterprise_models import (
        EnterpriseCompany, EnterpriseContact, EnterpriseContract,
        EnterpriseOrder, EnterpriseJob, EnterpriseInvoice
    )
    print("✅ All models import successfully")
    
    # Check each model's __table__ attribute
    for model in [EnterpriseCompany, EnterpriseContact, EnterpriseContract, 
                  EnterpriseOrder, EnterpriseJob, EnterpriseInvoice]:
        print(f"\n{model.__name__}:")
        if hasattr(model, '__table__'):
            print(f"  Table: {model.__table__.name}")
            print(f"  Columns: {len(model.__table__.columns)}")
        else:
            print("  ❌ No __table__ attribute")
            
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
