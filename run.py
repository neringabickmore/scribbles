import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask (__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)

@app.route("/")
@app.route("/about")
def about():
    return render_template("pages/about.html")


@app.route("/account")
def account():
    return render_template("components/forms/account.html")


@app.route("/favorites")
def favorites():
    return render_template("pages/favorites.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
            { "username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        
        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        return redirect(url_for("discover", username=session["user"]))

    return render_template("components/forms/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user: 
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "discover", username=session["user"]))
            else: 
                # invalid password match
                return redirect(url_for("login"))

        else: 
            # username doesn't exist
            return redirect(url_for("login"))

    return render_template("components/forms/login.html")


@app.route("/discover/<username>", methods=["GET", "POST"])
def discover(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("pages/discover.html", username=username)
    
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), 
            port=int(os.environ.get("PORT")), 
            debug=True)