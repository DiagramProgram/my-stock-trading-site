#export API_KEY=pk_983125ff75134e8a81341cb68d8ca84a
#flask run
import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    user = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])

    info = db.execute("SELECT symbol, share_name, shares_num, shares_price FROM transactions WHERE user_id = :user_id", user_id=session["user_id"])

    # How much cash the user has in their account
    cash = user[0]["cash"]

    total = 0

    for each in info:
        symbol = each["symbol"]
        shares = each["shares_num"]
        shares_price = each["shares_price"]

        total += shares * shares_price


    return render_template("index.html", cash=cash, info=info, total=total)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        # Name, price, symbol
        book = lookup(request.form.get("symbol"))

        shares_num = int(request.form.get("shares"))

        # Ensure nothing is left blank or that symbol is invalid
        if not request.form.get("symbol") or book == None:
            return apology("incorrect stock symbol", 403)

        elif not request.form.get("shares") or shares_num <= 0:
            return apology("must provide valid number of shares", 403)

        # Query database for cash in account for current user
        rows = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])

        cashamt = rows[0]["cash"]

        purchaseamt = book['price']*shares_num

        if purchaseamt > cashamt:
            return apology("sorry, not enough money to complete transaction", 403)

        # Update cash after purchase
        db.execute("UPDATE users SET cash = cash - :purchaseamt WHERE id = :user_id", purchaseamt=purchaseamt, user_id=session["user_id"])

        # Make new table and update its database with purchasing info
        db.execute("INSERT INTO transactions (user_id, share_name, symbol, shares_num, shares_price) VALUES (:user_id, :share_name, :symbol, :shares_num, :shares_price)",
                   user_id=session["user_id"],
                   share_name=book['name'],
                   symbol=request.form.get("symbol"),
                   shares_num=shares_num,
                   shares_price=book['price'])

        # Table solely for containing information needed to show transaction history
        db.execute("INSERT INTO transhist (user_id, symbol, shares_num, shares_price) VALUES (:user_id, :symbol, :shares_num, :shares_price)",
                   user_id=session["user_id"],
                   symbol=request.form.get("symbol"),
                   shares_num=shares_num,
                   shares_price=book['price'])

        flash("Bought!")

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    info = db.execute("SELECT * FROM transhist WHERE user_id = :user_id", user_id=session["user_id"])

    return render_template("history.html", info=info)


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    #if submitted
    if request.method == "POST":
        book = {}
        book = lookup(request.form.get("symbol")) #{'name': 'Apple, Inc.', 'price': 339.27, 'symbol': 'AAPL'}

        if book == None:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", book=book)

        #"A share of " + book['name'] + " " + book['symbol'] + " costs $" + str(book['price'])

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    #if submitted
    if request.method == "POST":

        # Ensure username provided
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password provided
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password confirmation provided
        elif not request.form.get("password"):
            return apology("must provide password retype", 403)


        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Check if username already exists
        if len(rows) == 1:
            return apology("sorry, that username already exists", 403)

        # Check if pasword retype matches initial password
        elif request.form.get("confirmation") != request.form.get("password"):
            return apology("sorry, your passwords don't match", 403)

        # If its good, we may proceed
        else:
            newp = generate_password_hash(request.form.get("password"))

            db.execute("INSERT INTO users (username, hash) VALUES (:user, :newp)", user=request.form.get("username"), newp=newp)

            return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":

        book = lookup(request.form.get("sel1"))


        my_symb = book['symbol'].lower()


        fut = db.execute("SELECT shares_num from transactions WHERE user_id = :user_id AND symbol = :symbol", # GIVES [{'shares_num': 4}]
                         user_id=session["user_id"],
                         symbol=my_symb)

        # Original amount of shares in account
        bla = fut[0]['shares_num']



        # Query database for cash in account for current user
        rows = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])

        cashamt = rows[0]["cash"]

        shares_sold_num = int(request.form.get("shares"))

        saleamt = book['price']*shares_sold_num


        # ----------- a few if statements -----------

        # Ensure nothing is left blank or that symbol is invalid
        if not request.form.get("sel1") or book == None:
            return apology("please select a share to sell", 403)

        elif not request.form.get("shares") or shares_sold_num <= 0:
            return apology("must provide valid number of shares", 403)

        elif shares_sold_num > bla:
            return apology("not enough shares in portfolio", 403)


        # Original amount - amount sold
        updatednum = bla-shares_sold_num

        if updatednum > 0:
            # Update portfolio table on hompeage
            db.execute("UPDATE transactions SET shares_num = :updatednum WHERE user_id = :user_id AND symbol = :symbol", updatednum=updatednum, user_id=session["user_id"], symbol=my_symb)

        # If the user sold all of their shares for that stock
        else:
            db.execute("DELETE FROM transactions WHERE user_id = :user_id AND symbol = :symbol", user_id=session["user_id"], symbol=my_symb)
            #db.execute("UPDATE transactions SET shares_num = :updatednum WHERE user_id = :user_id AND symbol = :symbol", updatednum=updatednum, user_id=session["user_id"], symbol=my_symb)

        # Update cash after purchase
        db.execute("UPDATE users SET cash = cash + :saleamt WHERE id = :user_id", saleamt=saleamt, user_id=session["user_id"])


        # Table solely for containing information needed to show transaction history
        db.execute("INSERT INTO transhist (user_id, symbol, shares_num, shares_price) VALUES (:user_id, :symbol, :shares_num, :shares_price)",
                   user_id=session["user_id"],
                   symbol=my_symb,
                   shares_num=-shares_sold_num,
                   shares_price=book['price'])


        flash("Sold!")

        return redirect("/")

    else:
        # To display list of all current stocks
        transinfo = db.execute("SELECT * FROM transactions WHERE user_id = :user_id", # CHECK IF ORDER IS RIGHT, ELSE REVERSE IT
                          user_id=session["user_id"])

        return render_template("sell.html", transinfo=transinfo)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
