"""
Production Configuration for Passenger Impact Engine
"""
import os
from typing import Dict, Any

class ProductionConfig:
    """Production-grade configuration management"""
    
    # Database configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise"
    )
    
    # Security configuration
    ENTERPRISE_ADMIN_KEY = os.getenv(
        "ENTERPRISE_ADMIN_KEY",
        "test_admin_key_123"  # CHANGE THIS IN PRODUCTION!
    )
    
    # Server configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    WORKERS = int(os.getenv("WORKERS", "4"))
    RELOAD = os.getenv("RELOAD", "false").lower() == "true"
    
    # CORS configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Rate limiting (requests per minute)
    RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100"))
    
    # Database connection pool
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return issues"""
        issues = []
        
        # Check for default admin key in production
        if cls.ENTERPRISE_ADMIN_KEY == "test_admin_key_123":
            issues.append("WARNING: Using default admin key in production!")
        
        # Validate database URL
        if "localhost" in cls.DATABASE_URL or "127.0.0.1" in cls.DATABASE_URL:
            issues.append("WARNING: Using localhost database in production configuration")
        
        # Check required environment variables
        required_vars = ["DATABASE_URL", "ENTERPRISE_ADMIN_KEY"]
        for var in required_vars:
            if not getattr(cls, var):
                issues.append(f"ERROR: {var} is not set")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config": {
                "database_url": cls.DATABASE_URL,
                "host": cls.HOST,
                "port": cls.PORT,
                "workers": cls.WORKERS,
                "cors_origins": cls.CORS_ORIGINS,
                "log_level": cls.LOG_LEVEL
            }
        }
    
    @classmethod
    def get_start_command(cls) -> str:
        """Get the uvicorn start command for production"""
        cmd = [
            "uvicorn",
            "src.pie.main:app",
            f"--host={cls.HOST}",
            f"--port={cls.PORT}",
            f"--workers={cls.WORKERS}",
            f"--log-level={cls.LOG_LEVEL}",
        ]
        
        if not cls.RELOAD:
            cmd.append("--no-reload")
        
        return " ".join(cmd)

if __name__ == "__main__":
    # Validate and display configuration
    validation = ProductionConfig.validate()
    
    print("🔧 PRODUCTION CONFIGURATION CHECK")
    print("=" * 50)
    
    print("\n📋 Configuration:")
    for key, value in validation["config"].items():
        print(f"  {key}: {value}")
    
    print("\n🔍 Validation Results:")
    if validation["valid"]:
        print("✅ Configuration is valid for production")
    else:
        print("⚠️  Configuration issues found:")
        for issue in validation["issues"]:
            print(f"  • {issue}")
    
    print(f"\n🚀 Start command:\n  {ProductionConfig.get_start_command()}")
    
    print("\n💡 Production Recommendations:")
    print("  1. Set a strong ENTERPRISE_ADMIN_KEY environment variable")
    print("  2. Use a production PostgreSQL database (not localhost)")
    print("  3. Configure HTTPS with a reverse proxy (nginx)")
    print("  4. Set up monitoring and logging")
    print("  5. Implement backup strategy for database")
