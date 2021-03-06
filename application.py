import os
import random
from flask import Flask, flash, redirect, session, jsonify, render_template, request
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from helpers import muscle_groups, t1name, login_required, apology, admin_required, dump_datetime
from datetime import datetime
from sqlalchemy import and_, or_

# Configure application
app = Flask(__name__)
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

#------- Configure SQL Alchemy-------------
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
#------------------------------------------

app.secret_key = b'\x93\x9a\xfbPLD\xf7\xbf\x14v<\xcaP\x1fL\x94'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    exercises = db.relationship('Exercise', backref='user', lazy=True)
    suggestions = db.relationship('Suggestion', backref='user', lazy=True)
    
    def __init__(self, username, hash, role):
        self.username = username
        self.hash = hash
        self.role = role


class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    group1 = db.Column(db.String(50), nullable=False)
    group2 = db.Column(db.String(50), nullable=False)
    t = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, group1, group2, t, user_id):
        self.name = name
        self.group1 = group1
        self.group2 = group2
        self.t = t
        self.user_id = user_id
    
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id'     : self.id,
           'name'   : self.name,
           'group1' : self.group1,
           'group2' : self.group2,
           't'      : self.t,
           'user_id': self.user_id,
           'time'   : dump_datetime(self.time),
       }

class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    group1 = db.Column(db.String(50), nullable=False)
    group2 = db.Column(db.String(50), nullable=False)
    t = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    exercise_id = db.Column(db.Integer)
    
    def __init__(self, name, group1, group2, t, user_id, exercise_id = None):
        self.name = name
        self.group1 = group1
        self.group2 = group2
        self.t = t
        self.user_id = user_id
        self.exercise_id = exercise_id

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


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

        # Query database for username and the number of users with that username
        n_rows = User.query.filter_by(username=request.form.get("username")).count()
        row = User.query.filter_by(username=request.form.get("username")).first()
            
        # Ensure username exists and password is correct
        if n_rows != 1 or not check_password_hash(row.hash, request.form.get("password")):
            return apology("invalid username and/or password", 403)
            
        # Remember which user has logged in
        session["user_id"] = row.id
        session["role"] = row.role
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

        # Query database for number of people with that username
        n_users = User.query.filter_by(username = request.form.get("username")).count()

        # Ensure username does not exist and passwords match
        print("Number of people with that username")
        print(n_users)
        if n_users > 0:
            return apology("Username already exists", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)

        # Insert user into database, return primary key
        new_user = User(username=request.form.get("username"),
                        hash=generate_password_hash(request.form.get("password"),
                                                    method='pbkdf2:sha256',
                                                    salt_length=8),
                        role=request.form.get("role"))
        db.session.add(new_user)
        db.session.commit()
        
        # Remember which user has logged in
        session["user_id"] = new_user.id
        session["role"] = new_user.role

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/")
def index():
    """Render Main Page"""

    return render_template("index.html")


@app.route("/button_pressed")
def button_pressed():
    """Button Pressed, Get Data From Exercises"""

    if not request.args.get("exercise"):
        raise RuntimeError("missing ex_day")

    ex_day = request.args.get("exercise")

    # Lookup t1 exercise name
    t1ex = t1name(ex_day)
    exs = Exercise.query.filter_by(name=t1ex).all()

    print(exs)
    
    # Lookup t2/t3 muscle groups
    acc_muscles = muscle_groups(ex_day)
    allt2=[]

    for muscle in acc_muscles["t2"]:
        allt2.extend(Exercise.query.filter(and_(Exercise.group1==muscle, Exercise.t==2)).all())

    # If there are more than 3 t2 exercises, randomly select 3
    if len(allt2) <= 3:
        exs.extend(allt2)
    else:
        rand_ind = random.sample(range(0, len(allt2)), 3)
        exs.extend([ex for i, ex in enumerate(allt2) if i in rand_ind])
    
    allt3 = []

    for muscle in acc_muscles["t3"]:
        allt3.extend(Exercise.query.filter(and_(Exercise.group1==muscle, Exercise.t==3)).all())

    # If there are more than 4 t3 exercises, randomly select 4
    if len(allt3) <= 4:
        exs.extend(allt3)
    else:
        rand_ind = random.sample(range(0, len(allt3)), 4)
        exs.extend([ex for i, ex in enumerate(allt3) if i in rand_ind])
    
    json_list=[i.serialize for i in exs]
    return jsonify(json_list)
    # return jsonify(exs)
    
@app.route("/allex")
@login_required
def allex():
    """Displays all the exercises and buttons to edit or add"""
    # role is needed to restrict view of delete buttons
    
    exs = Exercise.query.all()

    return render_template("allex.html", exs=exs)


@app.route("/suggestions")
@admin_required
def suggestions():
    """View and approve/delete suggestions from suggestion table"""
    # Get the suggestions
    
    ex_addsug = Suggestion.query.filter(Suggestion.exercise_id == None)

    ex_updatesug = Suggestion.query.filter(Suggestion.exercise_id != None)

    ex_oldlist = []
    for ex in ex_updatesug.all():
        ex_oldlist.extend([Exercise.query.get(ex.exercise_id)])

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
            # Check if exercise exists in DB, get the number of exercises with that name
            n_exs = Exercise.query.filter(and_(Exercise.name == request.form.get("name").lower(), Exercise.t == request.form.get("t"))).count()

            if n_exs > 0:
                return apology("exercise exists", 400)
            else:
                new_suggestion = Suggestion(name=request.form.get("name").lower(),
                                            group1=request.form.get("group1").lower(),
                                            group2=request.form.get("group2").lower(),
                                            t=request.form.get("t"),
                                            user_id=session["user_id"])

                db.session.add(new_suggestion)
                db.session.commit()

        else:
            # Insert Edit suggestion
            new_suggestion = Suggestion(name=request.form.get("name").lower(),
                                            group1=request.form.get("group1").lower(),
                                            group2=request.form.get("group2").lower(),
                                            t=request.form.get("t"),
                                            user_id=session["user_id"],
                                            exercise_id=request.form.get("replace_id"))
            db.session.add(new_suggestion)
            db.session.commit()

        return render_template("index.html")
    else:
        return render_template("add.html")


@app.route("/edit", methods=["POST"])
@login_required
def edit():
    """Add edit exercise suggestion to suggestion table"""
    if request.form.get('edit'):
        id = request.form.get('edit')
        ex = Exercise.query.get(id)

        return render_template("edit.html", ex=ex)

    else:
        return allex()


@app.route("/updateex", methods=["POST"])
@admin_required
def updateex():
    """Update from suggestion table"""
    if request.form.get('update'):
        
        # Get the exercise suggestion
        id_sug = request.form.get('update')
        ex_new = Suggestion.query.get(id_sug)
        
        # Update the exercise table
        ex = Exercise.query.get(ex_new.exercise_id)
        ex.name = ex_new.name
        ex.group1 = ex_new.group1
        ex.group2 = ex_new.group2
        ex.t = ex_new.t
        ex.user_id = ex_new.user_id
        db.session.commit()
        
        # Delete the suggestion
        db.session.delete(ex_new)
        db.session.commit()
        
        # Return to suggestions
    return suggestions()


@app.route("/addex", methods=["POST"])
@admin_required
def addex():
    """Update from suggestion table"""

    if request.form.get('delete'):
        db.session.delete(Suggestion.query.get(request.form.get('delete')))

    if request.form.get('add'):
        sug = Suggestion.query.get(request.form.get('add'))
        
        db.session.add(Exercise(name=sug.name,
                                group1=sug.group1,
                                group2=sug.group2,
                                t=sug.t,
                                user_id=sug.user_id))
        db.session.commit()

        db.session.delete(sug)
        db.session.commit()

    return suggestions()


@app.route("/delete", methods=["POST"])
@admin_required
def delete():
    """Deletes from exercise table"""

    if request.form.get('delete'):
        db.session.delete(Exercise.query.get(request.form.get('delete')))
        db.session.commit()

    return allex()


@app.route("/deletesug", methods=["POST"])
@admin_required
def deletesug():
    """Delete from suggestion table"""

    if request.form.get('delete'):
        db.session.delete(Suggestion.query.get(request.form.get('delete')))
        db.session.commit()

    return suggestions()