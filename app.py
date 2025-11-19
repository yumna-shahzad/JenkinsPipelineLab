from flask import Flask, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp
from markupsafe import escape
from sqlalchemy import text
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta

# ---------------------------------------------
# Initialize Flask application
# ---------------------------------------------
app = Flask(__name__)

# ---------------------------------------------
# App Configuration
# ---------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///firstapp.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'   # Needed for CSRF protection in Flask-WTF forms

# ---------------- Secure session configuration (OWASP recommendations) ----------------

app.config['SESSION_COOKIE_SECURE'] = False        # Set True in production (HTTPS)
app.config['SESSION_COOKIE_HTTPONLY'] = True       # Prevent JavaScript access to cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'      # Mitigate CSRF for cross-site requests
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # session lifetime

# ---------------------------------------------
# Initialize Database
# ---------------------------------------------
db = SQLAlchemy(app)

# Enable CSRF protection globally (Flask-WTF)
csrf = CSRFProtect(app)

# ---------------------------------------------
# Database Model
# ---------------------------------------------
class FirstApp(db.Model):
    sno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"{self.sno} - {self.fname}"

# ---------------------------------------------
# Flask-WTF Secure Form
# ---------------------------------------------
class UserForm(FlaskForm):
    fname = StringField('First Name', validators=[
        DataRequired(), Length(min=2, max=100),
        Regexp(r'^[A-Za-z ]+$', message="Only letters and spaces allowed.")
    ])
    lname = StringField('Last Name', validators=[
        DataRequired(), Length(min=2, max=100),
        Regexp(r'^[A-Za-z ]+$', message="Only letters and spaces allowed.")
    ])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=200)])
    submit = SubmitField('Add User')

# ---------------------------------------------
# Main Route – Secure Input Handling
# ---------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    form = UserForm()  # Create instance of secure form

    # When form is submitted and validated
    if form.validate_on_submit():
        # Escape all inputs to prevent XSS
        fname = escape(form.fname.data.strip())
        lname = escape(form.lname.data.strip())
        email = escape(form.email.data.strip())

        # Create a new database record
        user = FirstApp(fname=fname, lname=lname, email=email)
        db.session.add(user)
        db.session.commit()

        # Redirect to avoid form resubmission on refresh (Post/Redirect/Get)
        return redirect('/')

    # Fetch all records from DB
    allpeople = FirstApp.query.all()

    # Pass form + records to template
    return render_template('index.html', form=form, allpeople=allpeople)

# ---------------------------------------------
# Step 2: Parameterized Query Example (SQL Injection Prevention)
# ---------------------------------------------
@app.route('/search/<name>')
def search_user(name):
    """
    Safe parameterized raw-SQL example.
    Uses the model's actual table name and bound parameters to avoid SQL injection
    and table-name mismatches.
    """
    # Get the actual table name created by SQLAlchemy for the model
    table_name = FirstApp.__table__.name  # e.g., 'first_app' or 'firstapp'

    # Parameterized query using named parameter :fname
    query = text(f"SELECT * FROM {table_name} WHERE fname = :fname")
    result = db.session.execute(query, {"fname": name})

    rows = result.fetchall()

    # Build a safe textual output for testing
    output = ""
    for row in rows:
        # row supports dict-like access by column name in most SQLAlchemy versions
        try:
            fname = row['fname']
            lname = row['lname']
            email = row['email']
        except Exception:
            # fallback if row is tuple-like; adjust indexes if necessary
            fname, lname, email = row[1], row[2], row[3]
        output += f"{fname} {lname} ({email})<br>"
    return output if output else "No records found"

# ---------------------------------------------
# Session demo route (shows how to set a secure session)
# ---------------------------------------------
@app.route('/set_session')
def set_session():
    """
    Demonstration route: mark session as permanent and set a session value.
    This uses PERMANENT_SESSION_LIFETIME and the secure cookie settings above.
    """
    session.permanent = True
    session['user'] = 'test_user'
    return "Session set (permanent=True). Check cookie attributes in browser devtools."

# ---------------------------------------------
# Simple Home Route
# ---------------------------------------------
@app.route('/home')
def home():
    return 'Welcome to the Home Page'
# ---------------------------------------------
# Step 4: Secure Error Handling (Custom Error Pages)
# ---------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    """Custom 404 error page"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 error page (avoid exposing stack traces)"""
    # You could also log the actual error internally using logging module
    return render_template('500.html'), 500

# ---------------------------------------------
# Run Flask App
# ---------------------------------------------
if __name__ == '__main__':
    # Create database tables before starting server (only runs when executing app.py directly)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
