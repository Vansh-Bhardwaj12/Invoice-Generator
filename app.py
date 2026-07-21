from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from sqlalchemy import or_
from functools import wraps

from fpdf import FPDF

from config import Config
from database import db

from models import (
    User,
    Company,
    Institute,
    Invoice,
    InvoiceItem,
    Result,
    ResultSubject
)

# =====================================
# FLASK APP CONFIGURATION
# =====================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

# =====================================
# CURRENT COMPANY
# =====================================

def get_current_company():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return Company.query.filter_by(
        user_id=user_id
    ).first()

# =====================================
# CURRENT INSTITUTE
# =====================================

def get_current_institute():

    user_id = session.get("user_id")

    if not user_id:
        return None

    return Institute.query.filter_by(
        user_id=user_id
    ).first()

# =====================================
# LOGIN REQUIRED
# =====================================

def login_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return decorated_function

# =====================================
# HOME
# =====================================

@app.route("/")
@login_required
def home():

    return render_template("home.html")

# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id
            session["username"] = user.username

            flash(
                "Login Successful",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid Email or Password",
            "danger"
        )

    return render_template("login.html")

# =====================================
# REGISTER
# =====================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing = User.query.filter_by(
            email=email
        ).first()

        if existing:

            flash(
                "Email already exists.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        user = User(

            username=username,

            email=email,

            password=generate_password_hash(password)

        )

        db.session.add(user)

        db.session.commit()

        flash(
            "Registration Successful",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template("register.html")

# =====================================
# DASHBOARD
# =====================================

@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    # Current user's company
    company = Company.query.filter_by(user_id=user_id).first()

    # Current user's invoices
    invoices = Invoice.query.filter_by(user_id=user_id).all()

    invoice_count = len(invoices)

    # Current user's results
    results = Result.query.filter_by(user_id=user_id).all()

    result_count = len(results)

    # Revenue
    total_amount = sum(invoice.grand_total for invoice in invoices)

    return render_template(
        "dashboard.html",
        company=company,
        invoice_count=invoice_count,
        result_count=result_count,
        total_amount=total_amount,
        users=1
    )
# =====================================
# INVOICE PAGE
# =====================================

@app.route("/invoice")
@login_required
def invoice():

    search = request.args.get("search", "")

    query = Invoice.query.filter_by(
        user_id=session["user_id"]
    )

    if search:

        query = query.filter(

            or_(

                Invoice.customer_name.contains(search),

                Invoice.phone.contains(search)

            )

        )

    invoices = query.order_by(
        Invoice.id.desc()
    ).all()

    return render_template(
        "invoice.html",
        invoices=invoices,
        search=search
    )


# =====================================
# ADD INVOICE
# =====================================

@app.route("/add_invoice", methods=["POST"])
@login_required
def add_invoice():

    customer = request.form["customer"]
    phone = request.form["phone"]
    address = request.form["address"]

    products = request.form.getlist("product[]")
    quantities = request.form.getlist("quantity[]")
    prices = request.form.getlist("price[]")
    gsts = request.form.getlist("gst[]")

    invoice = Invoice(
        user_id=session["user_id"],
        customer_name=customer,
        phone=phone,
        address=address,
        grand_total=0
    )

    db.session.add(invoice)
    db.session.flush()

    grand_total = 0

    for product, qty, price, gst in zip(products, quantities, prices, gsts):

        qty = int(qty)
        price = float(price)
        gst = float(gst)

        subtotal = qty * price
        total = subtotal + (subtotal * gst / 100)

        grand_total += total

        item = InvoiceItem(
            invoice_id=invoice.id,
            product=product,
            quantity=qty,
            price=price,
            gst=gst,
            total=total
        )

        db.session.add(item)

    invoice.grand_total = grand_total

    db.session.commit()

    flash(
        "Invoice Saved Successfully!",
        "success"
    )

    return redirect(
        url_for("invoice")
    )


# =====================================
# EDIT INVOICE
# =====================================

@app.route("/edit_invoice/<int:id>", methods=["GET", "POST"])
@login_required
def edit_invoice(id):

    invoice = Invoice.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    if request.method == "POST":

        invoice.customer_name = request.form["customer"]
        invoice.phone = request.form["phone"]
        invoice.address = request.form["address"]

        InvoiceItem.query.filter_by(
            invoice_id=invoice.id
        ).delete()

        products = request.form.getlist("product[]")
        quantities = request.form.getlist("quantity[]")
        prices = request.form.getlist("price[]")
        gsts = request.form.getlist("gst[]")

        grand_total = 0

        for product, qty, price, gst in zip(products, quantities, prices, gsts):

            qty = int(qty)
            price = float(price)
            gst = float(gst)

            subtotal = qty * price
            total = subtotal + (subtotal * gst / 100)

            grand_total += total

            db.session.add(

                InvoiceItem(

                    invoice_id=invoice.id,

                    product=product,

                    quantity=qty,

                    price=price,

                    gst=gst,

                    total=total

                )

            )

        invoice.grand_total = grand_total

        db.session.commit()

        flash(
            "Invoice Updated Successfully!",
            "success"
        )

        return redirect(
            url_for("invoice")
        )

    return render_template(
        "edit_invoice.html",
        invoice=invoice,
        items=invoice.items
    )


# =====================================
# DELETE INVOICE
# =====================================

@app.route("/delete_invoice/<int:id>")
@login_required
def delete_invoice(id):

    invoice = Invoice.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    db.session.delete(invoice)

    db.session.commit()

    flash(
        "Invoice Deleted Successfully!",
        "success"
    )

    return redirect(
        url_for("invoice")
    )
# =====================================
# INVOICE PDF
# =====================================

@app.route("/invoice/pdf/<int:id>")
@login_required
def invoice_pdf(id):

    invoice = Invoice.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    company = get_current_company()

    if company is None:

        flash(
            "Please complete your Company Profile first.",
            "warning"
        )

        return redirect(
            url_for("profile")
        )

    pdf = FPDF()

    pdf.add_page()


    
    # ----------------------------
    # Company Details
    # ----------------------------

    pdf.set_font("Helvetica", "B", 18)

    pdf.cell(
        190,
        10,
        company.company_name,
        ln=True,
        align="C"
    )

    pdf.set_font("Helvetica", "", 11)

    pdf.cell(
        190,
        6,
        company.address or "",
        ln=True,
            align="C"
    )

    pdf.cell(
        190,
        6,
        f"Website : {company.website or ''}",
        ln=True,
        align="C"
    )    
    

    pdf.cell(
        190,
        6,
        f"Phone : {company.phone or ''}",
        ln=True,
        align="C"
    )

    pdf.cell(
        190,
        6,
        f"Email : {company.email or ''}",
        ln=True,
    )

    pdf.ln(8)

    # ----------------------------
    # Invoice Title
    # ----------------------------

    pdf.set_font("Helvetica", "B", 16)

    pdf.cell(
        190,
        10,
        "TAX INVOICE",
        ln=True,
        align="C"
    )

    pdf.ln(5)

    pdf.set_font("Helvetica", "", 12)

    pdf.cell(
        95,
        8,
        f"Invoice No : INV-{invoice.id:04}"
    )

    pdf.cell(
        95,
        8,
        datetime.now().strftime("%d-%m-%Y"),
        align="R",
        ln=True
    )

    pdf.ln(5)

    # ----------------------------
    # Customer Details
    # ----------------------------

    pdf.set_font("Helvetica", "B", 12)

    pdf.cell(
        190,
        8,
        "Customer Details",
        ln=True
    )

    pdf.set_font("Helvetica", "", 11)

    pdf.cell(
        40,
        8,
        "Customer"
    )

    pdf.cell(
        150,
        8,
        invoice.customer_name,
        ln=True
    )

    pdf.cell(
        40,
        8,
        "Phone"
    )

    pdf.cell(
        150,
        8,
        invoice.phone,
        ln=True
    )

    pdf.cell(
        40,
        8,
        "Address"
    )

    pdf.multi_cell(
        150,
        8,
        invoice.address
    )

    pdf.ln(5)

    # ----------------------------
    # Product Table
    # ----------------------------

    pdf.set_font("Helvetica", "B", 11)

    pdf.cell(60,10,"Product",1)
    pdf.cell(20,10,"Qty",1)
    pdf.cell(35,10,"Price",1)
    pdf.cell(25,10,"GST%",1)
    pdf.cell(50,10,"Total",1,ln=True)

    pdf.set_font("Helvetica","",11)

    for item in invoice.items:

        pdf.cell(60,10,item.product,1)
        pdf.cell(20,10,str(item.quantity),1)
        pdf.cell(35,10,f"{item.price:.2f}",1)
        pdf.cell(25,10,f"{item.gst:.2f}",1)
        pdf.cell(50,10,f"{item.total:.2f}",1,ln=True)

    pdf.ln(8)

    pdf.set_font("Helvetica","B",13)

    pdf.cell(
        140,
        10,
        "Grand Total"
    )

    pdf.cell(
        50,
        10,
        f"Rs. {invoice.grand_total:.2f}",
        align="R",
        ln=True
    )

    pdf.ln(20)

    pdf.set_font("Helvetica","",11)

    pdf.cell(
        95,
        10,
        "Customer Signature"
    )

    pdf.cell(
        95,
        10,
        "Authorized Signature",
        align="R"
    )

    filename = f"Invoice_{invoice.id}.pdf"

    pdf.output(filename)

    return send_file(
        filename,
        as_attachment=True
    )


# =====================================
# PRINT INVOICE
# =====================================

@app.route("/invoice/print/<int:id>")
@login_required
def print_invoice(id):

    invoice = Invoice.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    company = get_current_company()

    if company is None:

        flash(
            "Please complete your Company Profile first.",
            "warning"
        )

        return redirect(
            url_for("profile")
        )

    return render_template(

        "print_invoice.html",

        invoice=invoice,

        company=company,

        items=invoice.items

    )
# =====================================
# COMPANY PROFILE
# =====================================

@app.route("/profile")
@login_required
def profile():

    company = get_current_company()

    if company is None:

        company = Company(
            user_id=session["user_id"],
            company_name="My Company",
            address="",
            phone="",
            email="",
            website="",
            logo="logo.png"
        )

        db.session.add(company)
        db.session.commit()

    return render_template(
        "profile.html",
        company=company
    )


# =====================================
# UPDATE COMPANY PROFILE
# =====================================

@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():

    company = get_current_company()

    if company is None:

        company = Company(
            user_id=session["user_id"]
        )

        db.session.add(company)

    company.company_name = request.form.get("company_name")
    company.address = request.form.get("address")
    company.phone = request.form.get("phone")
    company.email = request.form.get("email")
    company.website = request.form.get("website")

    db.session.commit()

    flash(
        "Company Profile Updated Successfully!",
        "success"
    )

    return redirect(
        url_for("profile")
    )


# =====================================
# UPLOAD COMPANY LOGO
# =====================================

@app.route("/upload_logo", methods=["POST"])
@login_required
def upload_logo():

    company = get_current_company()

    if company is None:

        flash(
            "Please create company profile first.",
            "warning"
        )

        return redirect(
            url_for("profile")
        )

    file = request.files.get("logo")

    if file and file.filename:

        filename = secure_filename(file.filename)

        upload_folder = app.config["UPLOAD_FOLDER"]

        os.makedirs(upload_folder, exist_ok=True)

        file.save(
            os.path.join(
                upload_folder,
                filename
            )
        )

        company.logo = filename

        db.session.commit()

        flash(
            "Company Logo Uploaded Successfully!",
            "success"
        )

    return redirect(
        url_for("profile")
    )


# =====================================
# INSTITUTE PROFILE
# =====================================

@app.route("/institute_profile")
@login_required
def institute_profile():

    institute = get_current_institute()

    if institute is None:

        institute = Institute(

            user_id=session["user_id"],

            institute_name="My School",

            address="",

            phone="",

            email="",

            website="",

            logo="school_logo.png",

            principal_name="",

            principal_signature="",

            class_teacher_name="",

            class_teacher_signature=""

        )

        db.session.add(institute)
        db.session.commit()

    return render_template(
        "institute_profile.html",
        institute=institute
    )


# =====================================
# UPDATE INSTITUTE PROFILE
# =====================================

@app.route("/update_institute_profile", methods=["POST"])
@login_required
def update_institute_profile():

    institute = get_current_institute()

    if institute is None:

        institute = Institute(
            user_id=session["user_id"]
        )

        db.session.add(institute)

    institute.institute_name = request.form.get("institute_name")
    institute.address = request.form.get("address")
    institute.phone = request.form.get("phone")
    institute.email = request.form.get("email")
    institute.website = request.form.get("website")

    institute.principal_name = request.form.get("principal_name")
    institute.class_teacher_name = request.form.get("class_teacher_name")

    db.session.commit()

    flash(
        "Institute Profile Updated Successfully!",
        "success"
    )

    return redirect(
        url_for("institute_profile")
    )


# =====================================
# UPLOAD INSTITUTE LOGO
# =====================================

@app.route("/upload_institute_logo", methods=["POST"])
@login_required
def upload_institute_logo():

    institute = get_current_institute()

    if institute is None:

        flash(
            "Please create institute profile first.",
            "warning"
        )

        return redirect(
            url_for("institute_profile")
        )

    file = request.files.get("logo")

    if file and file.filename:

        filename = secure_filename(file.filename)

        upload_folder = app.config["UPLOAD_FOLDER"]

        os.makedirs(upload_folder, exist_ok=True)

        file.save(
            os.path.join(
                upload_folder,
                filename
            )
        )

        institute.logo = filename

        db.session.commit()

        flash(
            "Institute Logo Uploaded Successfully!",
            "success"
        )

    return redirect(
        url_for("institute_profile")
    )
# =====================================
# RESULT PAGE
# =====================================

@app.route("/result")
@login_required
def result():

    search = request.args.get("search", "")

    query = Result.query.filter_by(
        user_id=session["user_id"]
    )

    if search:

        query = query.filter(

            or_(

                Result.student_name.contains(search),

                Result.roll_number.contains(search)

            )

        )

    results = query.order_by(
        Result.id.desc()
    ).all()

    return render_template(
        "result.html",
        results=results,
        search=search
    )


# =====================================
# ADD RESULT
# =====================================

@app.route("/add_result", methods=["POST"])
@login_required
def add_result():

    student = request.form["student"]
    roll = request.form["roll"]
    student_class = request.form["student_class"]

    subjects = request.form.getlist("subject[]")
    marks = request.form.getlist("marks[]")

    total = 0

    for mark in marks:
        total += float(mark)

    percentage = total / len(subjects) if subjects else 0

    if percentage >= 90:
        grade = "A+"
        status = "Pass"

    elif percentage >= 80:
        grade = "A"
        status = "Pass"

    elif percentage >= 70:
        grade = "B"
        status = "Pass"

    elif percentage >= 60:
        grade = "C"
        status = "Pass"

    elif percentage >= 40:
        grade = "D"
        status = "Pass"

    else:
        grade = "F"
        status = "Fail"

    result = Result(

        user_id=session["user_id"],

        student_name=student,

        roll_number=roll,

        student_class=student_class,

        total=total,

        percentage=percentage,

        grade=grade,

        status=status

    )

    db.session.add(result)

    db.session.flush()

    for subject, mark in zip(subjects, marks):

        db.session.add(

            ResultSubject(

                result_id=result.id,

                subject_name=subject,

                marks=float(mark)

            )

        )

    db.session.commit()

    flash(
        "Result Generated Successfully!",
        "success"
    )

    return redirect(
        url_for("result")
    )
# =====================================
# EDIT RESULT
# =====================================

@app.route("/edit_result/<int:id>", methods=["GET", "POST"])
@login_required
def edit_result(id):

    result = Result.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    if request.method == "POST":

        # Student Details
        result.student_name = request.form["student"]
        result.roll_number = request.form["roll"]
        result.student_class = request.form["student_class"]

        # Delete Old Subjects
        ResultSubject.query.filter_by(
            result_id=result.id
        ).delete()

        subjects = request.form.getlist("subject[]")
        marks = request.form.getlist("marks[]")

        total = 0

        for subject, mark in zip(subjects, marks):

            mark = float(mark)

            total += mark

            db.session.add(
                ResultSubject(
                    result_id=result.id,
                    subject_name=subject,
                    marks=mark
                )
            )

        percentage = total / len(subjects) if subjects else 0

        if percentage >= 90:
            grade = "A+"
            status = "Pass"

        elif percentage >= 80:
            grade = "A"
            status = "Pass"

        elif percentage >= 70:
            grade = "B"
            status = "Pass"

        elif percentage >= 60:
            grade = "C"
            status = "Pass"

        elif percentage >= 40:
            grade = "D"
            status = "Pass"

        else:
            grade = "F"
            status = "Fail"

        result.total = total
        result.percentage = percentage
        result.grade = grade
        result.status = status

        db.session.commit()

        flash(
            "Result Updated Successfully!",
            "success"
        )

        return redirect(
            url_for("result")
        )

    return render_template(
        "edit_result.html",
        result=result
    )


# =====================================
# DELETE RESULT
# =====================================

@app.route("/delete_result/<int:id>")
@login_required
def delete_result(id):

    result = Result.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    db.session.delete(result)

    db.session.commit()

    flash(
        "Result Deleted Successfully!",
        "success"
    )

    return redirect(
        url_for("result")
    )

# =====================================
# RESULT PDF
# =====================================

@app.route("/result_pdf/<int:id>")
@login_required
def result_pdf(id):

    result = Result.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    institute = get_current_institute()

    if institute is None:

        flash(
            "Please complete your Institute Profile first.",
            "warning"
        )

        return redirect(
            url_for("institute_profile")
        )

    os.makedirs("static/pdfs", exist_ok=True)

    filename = f"Result_{result.id}.pdf"

    filepath = os.path.join(
        "static",
        "pdfs",
        filename
    )

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    title = styles["Title"]
    title.alignment = TA_CENTER

    heading = styles["Heading2"]

    normal = styles["Normal"]

    elements = []

    # ---------------------------------
    # Institute Header
    # ---------------------------------

    elements.append(
        Paragraph(
            f"<b>{institute.institute_name}</b>",
            title
        )
    )

    if institute.address:
        elements.append(
            Paragraph(
                institute.address,
                normal
            )
        )

    info = []

    if institute.phone:
        info.append(f"Phone : {institute.phone}")

    if institute.email:
        info.append(f"Email : {institute.email}")

    if institute.website:
        info.append(f"Website : {institute.website}")

    if info:

        elements.append(
            Paragraph(
                " | ".join(info),
                normal
            )
        )

    elements.append(
        Spacer(1, 20)
    )

    # ---------------------------------
    # Student Information
    # ---------------------------------

    elements.append(
        Paragraph(
            "<b>STUDENT REPORT CARD</b>",
            heading
        )
    )

    student_table = Table([

        ["Student Name", result.student_name],

        ["Roll Number", result.roll_number],

        ["Class", result.student_class]

    ], colWidths=[150, 300])

    student_table.setStyle(TableStyle([

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),

        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),

        ("BOTTOMPADDING", (0,0), (-1,-1), 8)

    ]))

    elements.append(student_table)

    elements.append(
        Spacer(1, 15)
    )

    # ---------------------------------
    # Subject Marks
    # ---------------------------------

    data = [

        ["Subject", "Marks"]

    ]

    for subject in result.subjects:

        data.append([
            subject.subject_name,
            f"{subject.marks:.2f}"
        ])

    marks_table = Table(
        data,
        colWidths=[300,150]
    )

    marks_table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(-1,0),colors.darkblue),

        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

        ("BOTTOMPADDING",(0,0),(-1,0),8)

    ]))

    elements.append(marks_table)

    elements.append(
        Spacer(1,20)
    )

    # ---------------------------------
    # Result Summary
    # ---------------------------------

    summary = [

        ["Total", f"{result.total:.2f}"],

        ["Percentage", f"{result.percentage:.2f}%"],

        ["Grade", result.grade],

        ["Status", result.status]

    ]

    summary_table = Table(
        summary,
        colWidths=[180,180]
    )

    summary_table.setStyle(TableStyle([

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("BACKGROUND",(0,0),(0,-1),colors.lightgrey),

        ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),

        ("ALIGN",(0,0),(-1,-1),"CENTER")

    ]))

    elements.append(summary_table)

    elements.append(
        Spacer(1,40)
    )

    # ---------------------------------
    # Signatures
    # ---------------------------------

    sign = Table([

        [
            "Class Teacher\n\n\n__________________",
            "Principal\n\n\n__________________"
        ]

    ], colWidths=[250,250])

    sign.setStyle(TableStyle([

        ("ALIGN",(0,0),(-1,-1),"CENTER"),

        ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold")

    ]))

    elements.append(sign)

    doc.build(elements)

    return send_file(
        filepath,
        as_attachment=True
    )
# =====================================
# PRINT RESULT
# =====================================

@app.route("/print_result/<int:id>")
@login_required
def print_result(id):

    result = Result.query.filter_by(
        id=id,
        user_id=session["user_id"]
    ).first_or_404()

    institute = get_current_institute()

    if institute is None:

        flash(
            "Please complete your Institute Profile first.",
            "warning"
        )

        return redirect(
            url_for("institute_profile")
        )

    return render_template(

        "print_result.html",

        result=result,

        institute=institute,

        subjects=result.subjects

    )


# =====================================
# HISTORY
# =====================================

@app.route("/history")
@login_required
def history():

    invoices = Invoice.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Invoice.id.desc()
    ).all()

    results = Result.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Result.id.desc()
    ).all()

    return render_template(

        "history.html",

        invoices=invoices,

        results=results

    )


# =====================================
# CONTACT
# =====================================

@app.route("/contact")
@login_required
def contact():

    return render_template("contact.html")


# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
@login_required
def logout():

    session.clear()

    flash(
        "Logged Out Successfully!",
        "success"
    )

    return redirect(
        url_for("login")
    )


# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":

    app.run(
        debug=True
    )