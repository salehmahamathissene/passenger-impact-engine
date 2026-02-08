from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# IMPORTANT: import models here so Alembic sees them
from pie.db.models.user import User
from pie.db.models.tenant import Tenant
from pie.db.models.membership import TenantMembership
from pie.db.models.api_key import ApiKey
from pie.db.models.audit_log import AuditLog
from pie.db.models.plan import Plan
from pie.db.models.subscription import Subscription
from pie.db.models.invoice import Invoice
from pie.db.models.payment import Payment
