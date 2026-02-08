with open('src/pie/pro/enterprise_models.py', 'r') as f:
    content = f.read()

# Replace Column with mapped_column
if 'api_key_hash = Column(' in content:
    content = content.replace('api_key_hash = Column(String, nullable=True)', 
                             'api_key_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)')
    
    with open('src/pie/pro/enterprise_models.py', 'w') as f:
        f.write(content)
    
    print("Fixed api_key_hash to use mapped_column")
else:
    print("api_key_hash already uses mapped_column or doesn't exist")
