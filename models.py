from database import db
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# USER MODEL
# ==========================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    institute = db.relationship(
        "Institute",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    company = db.relationship(
        "Company",
        backref="user",
        uselist=False,
        cascade="all, delete"
    )

    invoices = db.relationship(
        "Invoice",
        backref="user",
        cascade="all, delete"
    )

    results = db.relationship(
        "Result",
        backref="user",
        cascade="all, delete"
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# ==========================================
# COMPANY MODEL
# ==========================================

class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    company_name = db.Column(db.String(200), nullable=False)

    address = db.Column(db.Text)

    phone = db.Column(db.String(20))

    email = db.Column(db.String(150))

    website = db.Column(db.String(200))

    logo = db.Column(db.String(200), default="logo.png")

    # ==========================================
# INSTITUTE MODEL
# ==========================================

class Institute(db.Model):
    __tablename__ = "institutes"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    institute_name = db.Column(
        db.String(200),
        nullable=False,
        default="My Institute"
    )

    address = db.Column(
        db.String(300),
        default=""
    )

    phone = db.Column(
        db.String(30),
        default=""
    )

    email = db.Column(
        db.String(120),
        default=""
    )

    website = db.Column(
        db.String(200),
        default=""
    )

    logo = db.Column(
        db.String(200),
        default="school_logo.png"
    )

    principal_name = db.Column(
        db.String(150),
        default=""
    )

    principal_signature = db.Column(
        db.String(200),
        default=""
    )

    class_teacher_name = db.Column(
        db.String(150),
        default=""
    )

    class_teacher_signature = db.Column(
        db.String(200),
        default=""
    )


# ==========================================
# INVOICE MODEL
# ==========================================

class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    customer_name = db.Column(
        db.String(150),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    address = db.Column(
        db.Text,
        nullable=False
    )

    grand_total = db.Column(
        db.Float,
        default=0
    )

    items = db.relationship(
        "InvoiceItem",
        backref="invoice",
        cascade="all, delete-orphan",
        lazy=True
    )


# ==========================================
# INVOICE ITEMS
# ==========================================

class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"

    id = db.Column(db.Integer, primary_key=True)

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoices.id"),
        nullable=False
    )

    product = db.Column(
        db.String(200),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    gst = db.Column(
        db.Float,
        default=18
    )

    total = db.Column(
        db.Float,
        nullable=False
    )


# ==========================================
# RESULT MODEL
# ==========================================

# ==========================================
# RESULT MODEL
# ==========================================

class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    student_name = db.Column(
        db.String(150),
        nullable=False
    )

    roll_number = db.Column(
        db.String(50),
        nullable=False
    )

    student_class = db.Column(
        db.String(100),
        nullable=False
    )

    total = db.Column(
        db.Float,
        default=0
    )

    percentage = db.Column(
        db.Float,
        default=0
    )

    grade = db.Column(
        db.String(10)
    )

    status = db.Column(
        db.String(20)
    )

    subjects = db.relationship(
        "ResultSubject",
        backref="result",
        cascade="all, delete-orphan",
        lazy=True
    )


# ==========================================
# RESULT SUBJECT MODEL
# ==========================================

class ResultSubject(db.Model):
    __tablename__ = "result_subjects"

    id = db.Column(db.Integer, primary_key=True)

    result_id = db.Column(
        db.Integer,
        db.ForeignKey("results.id"),
        nullable=False
    )

    subject_name = db.Column(
        db.String(100),
        nullable=False
    )

    marks = db.Column(
        db.Float,
        nullable=False
    )