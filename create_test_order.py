from app import create_app
from app.extensions import db
from app.models.order import Order
from app.models.service import  Service, AcademicLevel, Deadline
from app.models.user import User

from datetime import datetime, timedelta
import random

app = create_app()
with app.app_context():
    # 1. Query all users
    users = User.query.all()
    if not users:
        print("No users found in the database.")
        exit()

    # pick one user (first for now)
    user = users[2]
    print(f"Creating test order for user: {user.id} - {user}")

    # 2. Pick related entities (just grab first ones for testing)
    service = Service.query.first()
    academic_level = AcademicLevel.query.first()
    deadline = Deadline.query.first()

    if not (service and academic_level and deadline):
        print("Missing related records (Service, AcademicLevel, Deadline). Please seed them first.")
        exit()

    # 3. Create dummy order
    order = Order(
        client_id=user.id,
        service_id=service.id,
        academic_level_id=academic_level.id,
        deadline_id=deadline.id,
        title="Test Order Title",
        description="This is a dummy order created for testing purposes.",
        word_count=2000,
        page_count=8,
        format_style="APA",
        report_type="turnitin",
        total_price=99.99,
        due_date=datetime.now() + timedelta(days=7),
    )

    # 4. Save to DB
    db.session.add(order)
    db.session.commit()

    print(f"✅ Test order created successfully! Order number: {order.order_number}")
