"""
Create main FastAPI app with billing routes if it doesn't exist
"""
from pathlib import Path

# Check what exists
app_paths = [
    Path("src/main.py"),
    Path("main.py"),
    Path("app/main.py"),
    Path("src/pie/pro/main.py"),
    Path("src/pie/main.py")
]

existing_app = None
for path in app_paths:
    if path.exists():
        print(f"✅ Found existing app: {path}")
        existing_app = path
        break

if not existing_app:
    print("❌ No main app found, creating one...")
    # Create src/main.py
    main_app_content = '''
"""
MAIN FASTAPI APPLICATION
Enterprise Passenger Impact Engine
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.pie.pro.billing_routes import router as billing_router
from src.pie.pro.enterprise_routes import router as enterprise_router

# Create FastAPI app
app = FastAPI(
    title="Passenger Impact Engine Enterprise API",
    description="Enterprise billing and management API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(enterprise_router)
app.include_router(billing_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Passenger Impact Engine Enterprise API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
'''
    
    main_path = Path("src/main.py")
    main_path.parent.mkdir(parents=True, exist_ok=True)
    main_path.write_text(main_app_content)
    print(f"✅ Created main app at: {main_path}")
    existing_app = main_path

# Now update it to include billing routes
print(f"\n📝 Updating {existing_app} to include billing routes...")
content = existing_app.read_text()

if 'billing_router' not in content:
    # Add import
    lines = content.split('\n')
    new_lines = []
    billing_import_added = False
    billing_include_added = False
    
    for line in lines:
        new_lines.append(line)
        
        # Add import after other imports
        if not billing_import_added and ('from' in line or 'import' in line) and '#' not in line:
            new_lines.append('from src.pie.pro.billing_routes import router as billing_router')
            billing_import_added = True
        
        # Add include_router
        if not billing_include_added and 'app.include_router' in line:
            new_lines.append('app.include_router(billing_router)')
            billing_include_added = True
    
    new_content = '\n'.join(new_lines)
    existing_app.write_text(new_content)
    print(f"✅ Added billing routes to {existing_app}")
else:
    print(f"✅ {existing_app} already has billing routes")
