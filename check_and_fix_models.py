import os
import sys
sys.path.append('src')

models_file = 'src/pie/pro/enterprise_models.py'
if os.path.exists(models_file):
    print(f"📋 Current models file ({models_file}):")
    print("=" * 60)
    
    with open(models_file, 'r') as f:
        content = f.read()
        print(content[:500] + "..." if len(content) > 500 else content)
    
    # Check for Base import
    if 'from pie.pro.database import Base' in content:
        print("\n✅ Already imports from pie.pro.database")
    elif 'Base = declarative_base()' in content:
        print("\n⚠️  Has local Base declaration - needs update")
        # Update the file
        with open(models_file, 'r') as f:
            lines = f.readlines()
        
        with open(models_file, 'w') as f:
            for line in lines:
                if 'declarative_base' in line:
                    f.write('from pie.pro.database import Base\n')
                elif 'Base = declarative_base()' in line:
                    f.write('# Base imported from database module\n')
                else:
                    f.write(line)
        print("✅ Updated to use centralized Base")
    else:
        print("\n❌ No Base found - models need database import")
else:
    print(f"❌ {models_file} not found!")
