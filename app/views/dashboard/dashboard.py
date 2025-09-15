from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ..forms.forms import CreateTenantForm
from ..utilities.database import create_database_tenant, delete_database_tenant
from ..utilities.payment import proccess_proof

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')



@dashboard_bp.route('/')
def landing():
    return render_template("landing.html")


@dashboard_bp.route('/home')
@login_required
def home():

    form = CreateTenantForm()
    return render_template("dashboard.html", form=form)




@dashboard_bp.route("/select-db", methods=["GET", "POST"])
@login_required
def select_db():
    form = CreateTenantForm()
    if request.method == "POST":
        if form.validate_on_submit():
            create_database_tenant(form)
        else:
            flash(f"Form validation failed.{form.errors}", "danger")
    return redirect(url_for("dashboard.home"))
    

@dashboard_bp.route("/delete", methods=["POST"])
@login_required
def delete_db():
   
    if request.method == "POST":    
        delete_database_tenant(request.form)
    return redirect(url_for('dashboard.home'))


@dashboard_bp.route("/billing", methods=["GET"])
@login_required
def billing():
    
    return render_template('billing.html')



@dashboard_bp.route("/submit-proof", methods=["POST"])
def submit_proof():
    if request.method == "POST":
        # handle file upload and save proof of payment
        proccess_proof(request)
        return redirect(url_for("dashboard.billing"))
    return redirect(url_for("dashboard.billing"))


@app.route("/upload/<int:user_id>", methods=["POST"])
def upload_file(user_id):
    if "file" not in request.files:
        return {"error": "No file provided"}, 400

    file = request.files["file"]
    filename = secure_filename(file.filename)

    # Create user-specific folder if not exists
    user_dir = os.path.join(app.config["UPLOAD_FOLDER"], f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    # Save file
    path = os.path.join(user_dir, filename)
    file.save(path)

    # Save metadata
    file_url = f"/files/user_{user_id}/{filename}"
    size = os.path.getsize(path)
    mime_type = file.mimetype

    cur.execute(
        """
        INSERT INTO files (user_id, filename, url, size, mime_type)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (user_id, filename, file_url, size, mime_type),
    )
    conn.commit()
    file_id = cur.fetchone()[0]

    return {"status": "ok", "file_id": file_id, "url": file_url}


@app.route("/files/<int:user_id>/<filename>")
def serve_file(user_id, filename):
    user_dir = os.path.join(app.config["UPLOAD_FOLDER"], f"user_{user_id}")
    file_path = os.path.join(user_dir, filename)

    if not os.path.exists(file_path):
        abort(404, "File not found")

    return send_from_directory(user_dir, filename)
















