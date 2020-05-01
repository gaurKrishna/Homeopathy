import datetime
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required


# Configure application
app = Flask(__name__)
# Reload templates when they are changed
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Handling responces
@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///patients.db")
print("SQL done")
# To handel "/" route i.e. index page
@app.route("/")
@login_required
def index():
    print("Index page")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        if not request.form.get("DocName"):
            return apology("Please provide name of the doctor!")
        elif not request.form.get("DocID"):
            return apology("Please provide your ID")
        elif not request.form.get("password"):
            return apology("Password field can't be empty!")
        rows = db.execute("SELECT * FROM doctors where DocID = :DocID",
                          DocID = request.form.get("DocID"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid Doctor name or password!")

        session["user_id"] = rows[0]["DocID"]
        return redirect("/patient")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/patient", methods=["GET", "POST"])
@login_required
def patient():
    if request.method == "POST":
        if not request.form.get("PatientName"):
            return apology("Please provide patient's name")
        if not request.form.get("PatientId"):
            return apology("Please provide patient's id number")
        rows = db.execute("SELECT * FROM patients WHERE PatientId = :PatientId",
                          PatientId = request.form.get("PatientId"))
        if len(rows) != 1:
            return apology("Sorry there is no patient with given ID")

        rows = db.execute("SELECT * FROM history WHERE patientid = :patientid",
                          patientid = request.form.get("PatientId"))
        info = {}
        patients = []
        for row in rows:
            info = {
                "illness": row["Illness"],
                "id": request.form.get("PatientId"),
                "medicines": row["Prescribed"],
                "date": row["Date"]
            }
            patients.append(info)
        return render_template("checkup.html", patients=patients)
    else:
        return render_template("patient.html")

@app.route("/add", methods=["POST"])
@login_required
def add():
    if request.method == "POST":
        if not request.form.get("PatientId"):
            return apology("Please enter the ID of the patient!")
        elif not request.form.get("Illness"):
            return apology("Please enter the discreption of disease!")
        elif not request.form.get("Prescribed"):
            return apology("Please enter the medicine prescribed!")

        patient = db.execute("SELECT City FROM patients WHERE PatientId = :PatientId",
                             PatientId = request.form.get("PatientId"))
        db.execute("INSERT INTO history (PatientID, Prescribed, Illness, Date, City) VALUES (:PatientID, :Prescribed, :Illness, :Date, :City)",
               PatientID = request.form.get("PatientId"),
               Prescribed = request.form.get("Prescribed"),
               Illness = request.form.get("Illness"),
               Date=datetime.now(),
               City=patient[0]["City"]
               )
        return render_template("patient.html")

@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if request.method == "GET":
        return render_template("Register.html")
    else:
        if not request.form.get("PatientName"):
            return apology("Please provide patient's name")
        if not request.form.get("city"):
            return apology("Please provide the name of the city in which patient lives")

        db.execute("INSERT INTO patients (Patient, City) VALUES (:Patient, :City)",
                   Patient=request.form.get("PatientName"),
                   City=request.form.get("city"))
        return render_template("patient.html")


@app.route("/remove", methods=["GET", "POST"])
@login_required
def passive():
    if request.method == "GET":
        return render_template("Passive.html")
    else:
        if not request.form.get("Rmcity"):
            return apology("Please enter the name of the city!")
        rows = db.execute("SELECT * FROM history WHERE City = :City",
                          City = request.form.get("Rmcity"))
        for row in rows:
            dt_object1 = datetime.strptime(row["Date"], "%Y-%m-%d %H:%M:%S")
            print(((datetime.now() - dt_object1).days))
            print(((datetime.now() - dt_object1).days) / 365)
            if (((datetime.now() - dt_object1).days) / 365) > 2:
                print("hare")
                db.execute("DELETE FROM history WHERE City = :City AND PatientID = :PatientID",
                           City = request.form.get("Rmcity"),
                           PatientID = row["PatientID"])
                db.execute("DELETE FROM patients WHERE PatientID = :PatientId",
                           PatientId = row["PatientID"])
        return redirect("/patient")
