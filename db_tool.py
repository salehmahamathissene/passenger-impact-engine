#!/usr/bin/env python3
"""
Database Management Tool for Passenger Impact Engine
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    from pie.pro.enterprise_models import Base, EnterpriseCompany, EnterpriseContact
    from pie.pro.settings import get_settings
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class DatabaseTool:
    def __init__(self):
        self.settings = get_settings()
        self.engine = create_engine(self.settings.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
    
    def check_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Database connected: {version}")
                
                # Check tables
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result]
                print(f"📊 Tables found ({len(tables)}): {', '.join(tables)}")
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def list_companies(self, limit=10):
        """List companies in the database"""
        session = self.Session()
        try:
            companies = session.query(EnterpriseCompany).limit(limit).all()
            print(f"\n🏢 Companies (showing {len(companies)}):")
            print("-" * 80)
            for company in companies:
                print(f"ID: {company.id}")
                print(f"  Legal Name: {company.legal_name}")
                print(f"  Trading Name: {company.trading_name}")
                print(f"  Tier: {company.tier}")
                print(f"  Industry: {company.industry}")
                print(f"  Created: {company.created_at}")
                print()
        finally:
            session.close()
    
    def list_contacts(self, company_id=None, limit=10):
        """List contacts"""
        session = self.Session()
        try:
            query = session.query(EnterpriseContact)
            if company_id:
                query = query.filter(EnterpriseContact.company_id == company_id)
            
            contacts = query.limit(limit).all()
            print(f"\n👥 Contacts (showing {len(contacts)}):")
            print("-" * 80)
            for contact in contacts:
                print(f"ID: {contact.id}")
                print(f"  Name: {contact.first_name} {contact.last_name}")
                print(f"  Email: {contact.email}")
                print(f"  Role: {contact.role}")
                print(f"  Company ID: {contact.company_id}")
                print()
        finally:
            session.close()
    
    def get_stats(self):
        """Get database statistics"""
        session = self.Session()
        try:
            with self.engine.connect() as conn:
                # Company stats
                result = conn.execute(text("SELECT COUNT(*) FROM enterprise_companies"))
                company_count = result.scalar()
                
                result = conn.execute(text("""
                    SELECT tier, COUNT(*) 
                    FROM enterprise_companies 
                    GROUP BY tier 
                    ORDER BY COUNT(*) DESC
                """))
                tier_stats = dict(result.fetchall())
                
                # Contact stats
                result = conn.execute(text("SELECT COUNT(*) FROM enterprise_contacts"))
                contact_count = result.scalar()
                
                # Contract stats
                result = conn.execute(text("SELECT COUNT(*) FROM enterprise_contracts"))
                contract_count = result.scalar()
                
                # Invoice stats
                result = conn.execute(text("SELECT COUNT(*) FROM enterprise_invoices"))
                invoice_count = result.scalar()
                result = conn.execute(text("""
                    SELECT status, COUNT(*) 
                    FROM enterprise_invoices 
                    GROUP BY status 
                    ORDER BY COUNT(*) DESC
                """))
                invoice_stats = dict(result.fetchall())
                
                print("\n📈 Database Statistics:")
                print("-" * 80)
                print(f"Companies: {company_count}")
                print(f"  Tier distribution: {tier_stats}")
                print(f"Contacts: {contact_count}")
                print(f"Contracts: {contract_count}")
                print(f"Invoices: {invoice_count}")
                print(f"  Invoice statuses: {invoice_stats}")
                
        finally:
            session.close()
    
    def run_sql(self, sql):
        """Execute raw SQL"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                if result.returns_rows:
                    rows = result.fetchall()
                    if rows:
                        # Print column names
                        print(" | ".join(result.keys()))
                        print("-" * 80)
                        for row in rows:
                            print(" | ".join(str(col) for col in row))
                    else:
                        print("No rows returned")
                else:
                    print(f"Query executed successfully. Rows affected: {result.rowcount}")
        except Exception as e:
            print(f"SQL error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Database Management Tool")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Check command
    subparsers.add_parser('check', help='Check database connection')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List data')
    list_parser.add_argument('type', choices=['companies', 'contacts'], help='Type to list')
    list_parser.add_argument('--company-id', help='Filter contacts by company ID')
    list_parser.add_argument('--limit', type=int, default=10, help='Limit results')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # SQL command
    sql_parser = subparsers.add_parser('sql', help='Execute SQL query')
    sql_parser.add_argument('query', help='SQL query to execute')
    
    args = parser.parse_args()
    
    tool = DatabaseTool()
    
    if args.command == 'check':
        tool.check_connection()
    
    elif args.command == 'list':
        if args.type == 'companies':
            tool.list_companies(limit=args.limit)
        elif args.type == 'contacts':
            tool.list_contacts(company_id=args.company_id, limit=args.limit)
    
    elif args.command == 'stats':
        tool.get_stats()
    
    elif args.command == 'sql':
        tool.run_sql(args.query)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
