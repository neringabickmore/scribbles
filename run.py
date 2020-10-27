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


# Global Variables:
mongo = PyMongo(app)
reviews = mongo.db.reviews
genres = mongo.db.genre
users =  mongo.db.users


@app.route("/")
@app.route("/about")
def about():
    return render_template("pages/about.html")


@app.route("/add/review", methods={"GET", "POST"})
def add_review():
    if request.method == "POST":
        review = {
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "genre": request.form.get("genre_category"),
            "length": request.form.get("length"),
            "ease_of_reading": request.form.get("ease_of_reading"),
            "plot_summary": request.form.get("plot_summary"),
            "favorite_quote": request.form.get("favorite_quote"),
            "emoji": request.form.get("emoji"),
            "rating": request.form.get("rating"),
            "link_to_image": request.form.get("link_to_image"),
            "link_to_buy": request.form.get("link_to_buy"),
            "reviewed_by": session["user"]
        }
        reviews.insert_one(review)
        flash("review added")
        return redirect(url_for("user_reviews"))

    genre = genres.find().sort("genre_category", 1)
    return render_template("pages/my-reviews.html", main_content="add_review", genre=genre)


@app.route("/edit/review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if request.method == "POST":
        submit = {"$set": {
            "title": request.form.get("title"),
            "author": request.form.get("author"),
            "genre": request.form.get("genre_category"),
            "length": request.form.get("length"),
            "ease_of_reading": request.form.get("ease_of_reading"),
            "plot_summary": request.form.get("plot_summary"),
            "favorite_quote": request.form.get("favorite_quote"),
            "emoji": request.form.get("emoji"),
            "rating": request.form.get("rating"),
            "link_to_image": request.form.get("link_to_image"),
            "link_to_buy": request.form.get("link_to_buy")
            }
        }
        reviews.update_one({"_id": ObjectId(review_id)}, submit)
        flash("Review Updated!")
        return redirect(url_for("user_reviews"))   
        
    review = reviews.find_one({"_id": ObjectId(review_id)})
    genre = genres.find().sort("genre_category", 1)
    return render_template("pages/my-reviews.html", main_content="edit_review", review=review, genre=genre)
    

@app.route("/delete/review/<review_id>")
def delete_review(review_id):
    reviews.remove({"_id": ObjectId(review_id)})
    flash("Review Deleted")
    return redirect(url_for("user_reviews"))


@app.route("/my/reviews", methods=["GET", "POST"])
def user_reviews():
    if session["user"]:
        user_profile = users.find({"username": session["user"]})
        reviews = list(mongo.db.reviews.find({"reviewed_by": session["user"]}))
        return render_template("pages/my-reviews.html", user=user_profile, reviews=reviews)
    return redirect(url_for("user_reviews"))


@app.route("/discover/reviews", methods=["GET"])
def discover():
    if request.method == "GET":
        reviews = mongo.db.reviews.find().sort("genre")
        return render_template("pages/discover.html", reviews=reviews)
    return redirect(url_for("discover"))


@app.route("/add/favorites/<review_id>", methods=["GET", "POST"])
def add_favorites(review_id):
    if session["user"]:
        # check if favorite review already exists in database
        favorite_review_exists = mongo.db.favorites.find_one({"favorite": review_id})

        # if the favorite review already in the database - it flashes a message    
        if favorite_review_exists:
            flash("This review is already in your favorites")
            return redirect(url_for("discover"))
        
        favorite_review = {
            "username": session["user"],
            "favorite" : review_id
        }
        mongo.db.favorites.insert_one(favorite_review)
        flash("new favorite added to your collection")
        return redirect(url_for("discover"))
    return redirect(url_for("discover"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = users.find_one(
            { "username": request.form.get("username").lower()})
        # if the user exists - it flashes a message
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))
        
        register = {
            "username": request.form.get("username").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        return redirect(url_for("discover", username=session["user"]))

    return render_template("pages/access.html", main_content="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_user = users.find_one(
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

        return redirect(url_for("login"))
    return render_template("pages/access.html", main_content="login")


@app.route("/logout")
def logout():
    # remove user from session cookies
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if session["user"]:
        # grab the session user's credentials from database
        user_profile = users.find_one({"username": session["user"]})
        return render_template("pages/profile.html", user=user_profile)
    return redirect(url_for("login"))


@app.route("/edit/profile/<user_profile_id>", methods=["GET", "POST"])
def edit_profile(user_profile_id):
    if request.method == "POST":
        submit = {"$set": {
            "username": request.form.get("username"), 
            "email": request.form.get("email"),
            "password": generate_password_hash(request.form.get("password"))
            }
        }
        users.update_one({"_id": ObjectId(user_profile_id)}, submit)
        #update user session to push new username before re-directing
        session["user"] = request.form.get("username")
        flash("User Profile Successfully Updated!")
        return redirect(url_for("profile"))
        
    user_profile = users.find_one({"_id": ObjectId(user_profile_id)})
    return render_template("pages/profile.html", main_content="edit_profile", user=user_profile)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), 
            port=int(os.environ.get("PORT")), 
            debug=True)