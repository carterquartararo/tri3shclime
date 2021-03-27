import data
from flask import Flask, render_template, redirect, url_for, request, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, BooleanField, IntegerField
from wtforms.validators import InputRequired, Email, Length
from sqlalchemy import select
from test import get_price

app = Flask(__name__)
app.config['SECRET_KEY'] = '981@&^#dlsaA'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
# IMPORTANT - GENERATES CSRF TOKEN
csrf = CSRFProtect(app)
csrf.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):  # Creates columns inside of the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)  # username column
    email = db.Column(db.String(50), unique=True)  # email column
    password = db.Column(db.String(80), unique=False)  # password column
    dat_green = db.Column(db.Integer, unique=False)


class Chat(UserMixin, db.Model):  # Creates columns inside of the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=False)  # username column
    chat = db.Column(db.String(250), unique=False)  # chat column


class UserYOLO(UserMixin, db.Model):  # Creates columns inside of the database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=False)  # username column
    stock = db.Column(db.String(250), unique=False)  # stock symbol column
    number_shares = db.Column(db.Integer, unique=False)  # number of shares
    initial_price = db.Column(db.Float, unique=False)  # initial price of share


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')


class ChatForm(FlaskForm):
    chat = StringField('chat', validators=[InputRequired(), Length(min=1, max=250)])


class BuyForm(FlaskForm):
    stock = StringField('stock', validators=[InputRequired(), Length(min=1, max=250)])
    amount = IntegerField('amount', validators=[InputRequired()])


class SellForm(FlaskForm):
    stock = StringField('stock', validators=[InputRequired(), Length(min=1, max=250)])
    amount = IntegerField('amount', validators=[InputRequired()])


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


@app.route('/', methods=["GET", "POST"])
def home():
    if request.method == 'POST':
        form = request.form
        selection = form["symbol"]
        price = get_price(selection)
    else:
        price = ""
    return render_template("home.html", price=price)


@app.route('/stocks')
def stocks():
    return render_template("stocks.html")


@app.route('/jesus')
def jesus():
    return render_template("easteregg.html")


@app.route('/broke')
def broke():
    return render_template("broke.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        return render_template('invalid.html', form=form)
    # return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    form = ChatForm()
    if request.form:
        new_chat = Chat(username=current_user.username, chat=form.chat.data)
        db.session.add(new_chat)
        db.session.commit()
    results = db.session.query(Chat).all()
    return render_template('chat.html', form=form, chats=results)


@app.route('/buy', methods=['GET', 'POST'])
@login_required
def buy():
    form = BuyForm()
    if request.form:
        selection = form.stock.data
        price_string = get_price(selection)
        price = float(price_string)
        if price * form.amount.data < current_user.dat_green:
            new_buy = UserYOLO(username=current_user.username, stock=form.stock.data, number_shares=form.amount.data,
                               initial_price=price)
            db.session.add(new_buy)
            db.session.commit()
            current_user.dat_green = current_user.dat_green-price * form.amount.data
            db.session.commit()
        else:
            return render_template('broke.html')
    return render_template('buy.html', form=form)


@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    form = SellForm()
    if request.form:
        selection = form.stock.data
        stmt = select(UserYOLO).where(UserYOLO.stock == selection, UserYOLO.username == current_user.username)
        stock_sell = stmt.number_shares
        price_string = get_price(selection)
        price = float(price_string)
        if form.amount.data < stock_sell:
            print("hello")
            current_user.dat_green = current_user.dat_green+price * form.amount.data
            db.session.commit()
        else:
            return render_template('broke.html')
    return render_template('sell.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password, dat_green=50000)
        db.session.add(new_user)
        db.session.commit()
        # redirect to page when user is created
        return render_template('usercreatedredirect.html')
    # return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'
    return render_template('signup.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/about')
def about():
    return render_template("aboutus.html")


@app.route('/collegeboard')
def collegeboard():
    return render_template("collegeboard.html", datalist=data.playlist())


@app.route('/leaderboard')
@login_required
def leaderboard():
    #go to the score table and query it, order it by the score value descending, limit 10 and serve up all of those items I asked for as a list.
    results = User.query.order_by(desc('balance')).limit(10).all()
    balances = []

    for result in results:
        balance_dict = {'username':result.username, 'balance':result.balance}
        balances.append(balance_dict)

    return render_template('Leaderboard.html', balances = balances)


if __name__ == "__main__":
    db.create_all()
    #app.run(debug=True, port='5000', host='127.0.0.1')
    app.run(debug=True, port='5000', host='127.0.0.1')
