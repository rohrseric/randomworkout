import os
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorate routes to require admin.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    # Adapted from login_required(f)
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        role = db.execute("SELECT role FROM users WHERE id = " + str(session.get("user_id")))
        if role[0]["role"] != "Admin":
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


def t1name(ex_day):
    """Returns object of t2 and t3 muscle groups"""

    # Find T1, T2, and T3 options
    if ex_day == "squat":
        return "back squat"
    elif ex_day == "bench":
        return "bench press"
    elif ex_day == "deadlift":
        return "deadlift"
    elif ex_day == "press":
        return "overhead press"
    else:
        return None


def muscle_groups(ex_day):
    """Returns object of t2 and t3 muscle groups"""

    # Find T1, T2, and T3 options
    if ex_day == "squat":
        t2 = ["back", "legs"]
        t3 = ["biceps", "back"]
    elif ex_day == "bench":
        t2 = ["chest", "shoulders"]
        t3 = ["triceps", "shoulders", "back"]
    elif ex_day == "deadlift":
        t2 = ["back", "legs"]
        t3 = ["biceps", "back"]
    elif ex_day == "press":
        t2 = ["chest", "shoulders"]
        t3 = ["triceps", "shoulders", "back"]
    else:
        return None

    # Send muscles_groups back as an object
    muscle_groups = {
        "t2": t2,
        "t3": t3
    }
    return muscle_groups