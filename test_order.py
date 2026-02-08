from pie.pro.db import SessionLocal, init_db
from pie.pro.models import Order, OrderStatus
from pie.pro.queue import enqueue_order_job

# Initialize
init_db()

# Create test order
db = SessionLocal()
order = Order(
    customer_email="test@example.com",
    plan="pro",
    amount_cents=49900,
    currency="eur",
    status=OrderStatus.paid  # Simulate paid
)
db.add(order)
db.commit()
db.refresh(order)
print(f"✅ Created order {order.id} for {order.customer_email}")

# Queue job
enqueue_order_job(order.id)
print(f"✅ Queued job for order {order.id}")

db.close()
