from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import boto3
import os
import csv
import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

#  RDS MySQL connection string
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin123@mailmatrix-db.ccte8q0ashq5.us-east-1.rds.amazonaws.com/mailmatrix'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#  AWS S3
S3_BUCKET = 'mailmatrix-csv-bucket'
s3 = boto3.client('s3')

# ------------------ User Model (linked to 'users' table) ------------------ #
class Users(db.Model):
    __tablename__ = 'users'  #  Explicitly map to your existing table name
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    country_code = db.Column(db.String(10))
    mobile = db.Column(db.String(30))
    organization = db.Column(db.String(100))

class UploadHistory(db.Model):
    __tablename__ = 'upload_history'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100))
    file_name = db.Column(db.String(255))
    upload_type = db.Column(db.String(20))
    action = db.Column(db.String(20))
    recipient_email = db.Column(db.String(100))
    status = db.Column(db.String(20))
    company = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())


# ------------------ Routes ------------------ #

@app.route('/')
def index():
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        country_code = request.form.get('country_code')
        mobile = request.form.get('mobile')
        organization = request.form.get('organization')

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match.")

        if Users.query.filter_by(email=email).first():
            return render_template('register.html', error="User already exists.")

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user = Users(
            email=email,
            password=hashed_pw.decode('utf-8'),
            first_name=first_name,
            last_name=last_name,
            country_code=country_code,
            mobile=mobile,
            organization=organization
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email).first()

        # Secure bcrypt password check
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user'] = user.email
            session['first_name'] = user.first_name
            return redirect('/home')
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')


@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        if 'csvfile' not in request.files:
            return "No CSV file uploaded", 400

        file = request.files['csvfile']
        if file.filename == '':
            return "No selected file", 400

        filename =secure_filename(file.filename)
        local_path = os.path.join('uploads', filename)
        file.save(local_path)

        # Read and record recipient info
        with open(local_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                recipient = row.get('Email') or row.get('email')
                status = row.get('Status') or row.get('status')

                user = Users.query.filter_by(email=session['user']).first()
                company = user.organization

                history = UploadHistory(
                    user_email=session['user'],
                    file_name=filename,
                    upload_type='csv',
                    action='uploaded',
                    recipient_email=recipient or "-",
                    status=status or "N/A",
                    company=company,
                    timestamp=datetime.datetime.now()
                )
                db.session.add(history)

        db.session.commit()

        # 2. Upload to S3 and delete the file AFTER parsing
        s3.upload_file(local_path, S3_BUCKET, f"uploads/{filename}")
        os.remove(local_path)

        print(f" CSV uploaded and history recorded: {filename}")
        return redirect('/home')


    return render_template('home.html', user=session['user'], first_name=session.get('first_name'))



@app.route('/upload_offer_letter', methods=['POST'])
def upload_offer_letter():
    if 'offer_letters' not in request.files:
        return "No file part", 400

    files = request.files.getlist('offer_letters')

    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            s3.upload_fileobj(file, S3_BUCKET, f"offer_letters/{filename}")
            print(f"✅ Offer letter uploaded: {filename}")

        else:
            print("⚠️ Skipped empty or unnamed file")
   

    db.session.commit()
    flash("Offer letters uploaded successfully!", "success")
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect('/login')

    user_email = session['user']
    user = Users.query.filter_by(email=user_email).first()

    if request.method == 'POST':
        new_org = request.form.get('organization')
        new_mobile = request.form.get('mobile')
        new_password = request.form.get('new_password')

        user.organization = new_org
        user.mobile = new_mobile

        if new_password:
            user.password = generate_password_hash(new_password)  

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect('/profile')

    return render_template('profile.html', user=user)


@app.route('/upload_recipients', methods=['POST'])
def upload_recipients():
    if 'recipients_csv' not in request.files:
        return "No CSV file uploaded", 400

    file = request.files['recipients_csv']
    if file.filename == '':
        return "No file selected", 400

    filename = secure_filename(file.filename)
    local_path = os.path.join('uploads', filename)
    file.save(local_path)
    user = Users.query.filter_by(email=session['user']).first()
    company = user.organization

    # Read and record recipient info
    with open(local_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            recipient = row.get('Email') or row.get('email')
            status = row.get('Status') or row.get('status')

            history = UploadHistory(
                user_email=session['user'],
                file_name=filename,
                upload_type='csv',
                action='uploaded',
                recipient_email=recipient or "-",
                status=status or "N/A",
                company=company,
                timestamp=datetime.datetime.now()
            )
            db.session.add(history)

    db.session.commit()

    # Upload to S3
    s3.upload_file(local_path, S3_BUCKET, f"uploads/{filename}")
    os.remove(local_path)

    flash("Recipients CSV uploaded successfully!", "success")
    return redirect('/home')


@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/login')

    records = UploadHistory.query.filter_by(user_email=session['user'], upload_type='csv') \
                                 .order_by(UploadHistory.timestamp.desc()).all()
    return render_template('history.html', records=records, user_email=session['user'])


@app.route('/contact')
def contact():
    if 'user' not in session:
        return redirect('/login')
    return render_template('contact.html')



#@app.route('/history')
#def history():
#    if 'user' not in session:
#        return redirect('/login')
#
#    records = UploadHistory.query.filter_by(user_email=session['user']).order_by(UploadHistory.timestamp.desc()).all()
#    return render_template('history.html', records=records)



# ------------------ Run App ------------------ #

if __name__ == '__main__':
    app.run(debug=True)
