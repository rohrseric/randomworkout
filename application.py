import os
import random
from flask import Flask, flash, redirect, session, jsonify, render_template, request
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from cs50 import SQL
from helpers import muscle_groups, t1name, login_required, apology, admin_required

# Configure application
app = Flask(__name__)
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)

        # Query database for username
        result = db.execute("SELECT * FROM users WHERE username = :username",
                            username=request.form.get("username"))

        # Ensure username does not exist and passwords match
        if result:
            return apology("Username already exists", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)

        # Insert user into database, return primary key
        id = db.execute("INSERT INTO users (username, hash, role) VALUES(:username, :hash, :role)",
                        username=request.form.get("username"),
                        hash=generate_password_hash(request.form.get("password"),
                                                    method='pbkdf2:sha256',
                                                    salt_length=8),
                        role=request.form.get("role"))

        # Remember which user has logged in
        session["user_id"] = id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/")
def index():
    """Render Main Page"""
    # Retrieve user's role to update the navbar
    if session:
        role = db.execute("SELECT role FROM users WHERE id = :id",
                          id=session["user_id"])
        role = role[0]["role"]
    else:
        role = None

    return render_template("index.html", role=role)


@app.route("/button_pressed")
def button_pressed():
    """Button Pressed, Get Data From Exercises"""

    if not request.args.get("exercise"):
        raise RuntimeError("missing ex_day")

    ex_day = request.args.get("exercise")

    # Lookup t1 exercise name
    t1ex = t1name(ex_day)
    exs = db.execute("SELECT * FROM exercises WHERE name = '" + t1ex + "'")

    # Lookup t2/t3 muscle groups
    acc_muscles = muscle_groups(ex_day)

    query = "SELECT * FROM exercises WHERE "
    for ind, muscle in enumerate(acc_muscles["t2"]):
        query += "(group1 = '" + muscle + "' AND t = 2)"
        if ind != len(acc_muscles["t2"]) - 1:
            query += " OR "

    allt2 = db.execute(query)

    # If there are more than 3 t2 exercises, randomly select 3
    if len(allt2) <= 3:
        exs.extend(allt2)
    else:
        rand_ind = random.sample(range(0, len(allt2)), 3)
        exs.extend([ex for i, ex in enumerate(allt2) if i in rand_ind])

    query = "SELECT * FROM exercises WHERE "
    for ind, muscle in enumerate(acc_muscles["t3"]):
        query += "(group1 = '" + muscle + "' AND t = 3)"
        if ind != len(acc_muscles["t3"]) - 1:
            query += " OR "

    allt3 = db.execute(query)

    # If there are more than 4 t3 exercises, randomly select 4
    if len(allt3) <= 4:
        exs.extend(allt3)
    else:
        rand_ind = random.sample(range(0, len(allt3)), 4)
        exs.extend([ex for i, ex in enumerate(allt3) if i in rand_ind])

    return jsonify(exs)


@app.route("/allex")
@login_required
def allex():
    """Displays all the exercises and buttons to edit or add"""
    # role is needed to restrict view of delete buttons
    exs = db.execute("SELECT * FROM exercises")
    role = db.execute("SELECT role FROM users WHERE id = :id",
                      id=session["user_id"])
    role = role[0]["role"]

    return render_template("allex.html", exs=exs, role=role)


@app.route("/suggestions")
@admin_required
def suggestions():
    """View and approve/delete suggestions from suggestion table"""
    # Get the suggestions
    ex_addsug = db.execute("SELECT * FROM suggestions WHERE replace_id IS NULL")
    ex_updatesug = db.execute("SELECT * FROM suggestions WHERE replace_id IS NOT NULL")
    ex_oldlist = []
    for ex in ex_updatesug:
        ex_oldlist.extend(db.execute("SELECT * FROM exercises WHERE id = :replace_id",
                                     replace_id=ex["replace_id"]))
    # send the addition suggestions and a zip of update suggestions and their respective exercise to update
    return render_template("suggestions.html", ex_addsug=ex_addsug, ex_updatelist=zip(ex_updatesug, ex_oldlist))


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add exercise suggestion to suggestion table"""
    # Check the form inputs
    if request.method == "POST":
        if not request.form.get("name"):
            return apology("must provide name", 400)

        if not request.form.get("group1"):
            return apology("must provide group1", 400)

        if not request.form.get("group2"):
            return apology("must provide group2", 400)

        if not request.form.get("t"):
            return apology("must provide t", 400)

        # Check if adding edit suggestion or add suggestions
        if not request.form.get("replace_id"):
            # Insert Add suggestion
            # Check if exercise exists in DB
            name = db.execute("SELECT * FROM exercises WHERE name = :name AND t = :t",
                              name=request.form.get("name").lower(),
                              t=request.form.get("t"))
            if name:
                return apology("exercise exists", 400)
            else:
                db.execute("INSERT INTO suggestions (name, group1, group2, t, user_id) VALUES(:name, :group1, :group2, :t, :user_id)",
                           name=request.form.get("name").lower(),
                           group1=request.form.get("group1").lower(),
                           group2=request.form.get("group2").lower(),
                           t=request.form.get("t"),
                           user_id=session["user_id"])
        else:
            # Insert Edit suggestion
            db.execute("INSERT INTO suggestions (name, group1, group2, t, user_id, replace_id) VALUES(:name, :group1, :group2, :t, :user_id, :replace_id)",
                       name=request.form.get("name").lower(),
                       group1=request.form.get("group1").lower(),
                       group2=request.form.get("group2").lower(),
                       t=request.form.get("t"),
                       user_id=session["user_id"],
                       replace_id=request.form.get("replace_id"))

        return render_template("index.html")
    else:
        return render_template("add.html")


@app.route("/edit", methods=["POST"])
@login_required
def edit():
    """Add edit exercise suggestion to suggestion table"""
    if request.form.get('edit'):
        id = request.form.get('edit')
        ex = db.execute("SELECT * FROM exercises WHERE id = :id",
                        id=id)
        ex = ex[0]

        return render_template("edit.html", ex=ex)

    else:
        return allex()


@app.route("/updateex", methods=["POST"])
@admin_required
def updateex():
    """Update from suggestion table"""
    if request.form.get('update'):

        id_sug = request.form.get('update')
        ex = db.execute("SELECT * FROM suggestions WHERE id = :id_sug",
                        id_sug=id_sug)
        ex = ex[0]

        db.execute("UPDATE exercises SET name = :name, group1 = :group1, group2 = :group2, t = :t, user_id = :user_id WHERE id = :replace_id",
                   name=ex["name"],
                   group1=ex["group1"],
                   group2=ex["group2"],
                   t=ex["t"],
                   user_id=ex["user_id"],
                   replace_id=ex["replace_id"])

        db.execute("DELETE FROM suggestions WHERE id = :id_sug",
                   id_sug=id_sug)

    return suggestions()


@app.route("/addex", methods=["POST"])
@admin_required
def addex():
    """Update from suggestion table"""

    if request.form.get('delete'):
        db.execute("DELETE FROM suggestions WHERE id = :id",
                   id=request.form.get('delete'))

    if request.form.get('add'):
        sug = db.execute("SELECT * FROM suggestions WHERE id = :id",
                         id=request.form.get('add'))
        sug = sug[0]
        db.execute("INSERT INTO exercises (name, group1, group2, t, user_id) VALUES(:name, :group1, :group2, :t, :user_id)",
                   name=sug["name"],
                   group1=sug["group1"],
                   group2=sug["group2"],
                   t=sug["t"],
                   user_id=sug["user_id"])
        db.execute("DELETE FROM suggestions WHERE id = :id",
                   id=request.form.get('add'))

    return suggestions()


@app.route("/delete", methods=["POST"])
@admin_required
def delete():
    """Deletes from exercise table"""

    if request.form.get('delete'):
        db.execute("DELETE FROM exercises WHERE id = :id",
                   id=request.form.get('delete'))

    return allex()


@app.route("/deletesug", methods=["POST"])
@admin_required
def deletesug():
    """Delete from suggestion table"""

    if request.form.get('delete'):
        db.execute("DELETE FROM suggestions WHERE id = :id",
                   id=request.form.get('delete'))

    return suggestions()