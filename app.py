from flask import Flask, render_template, request, redirect, url_for, flash, session,send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user,logout_user, current_user, login_required
from flask_mail import Mail, Message
from random import randint
from pyzbar.pyzbar import decode
from PIL import Image
import os
import datetime
from io import BytesIO

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite"
app.config['SECRET_KEY'] = 'jlsadkjfdofofsaldffjas'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'flaskapp389@gmail.com'
app.config['MAIL_PASSWORD'] = 'Flaskapp@3891821'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.secret_key = 'sds4878asdkfn38j9we'

mail = Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean)

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    frm = db.Column(db.String(100))
    to = db.Column(db.String(100))
    data = db.Column(db.LargeBinary)
    name = db.Column(db.String(100))
    dt = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def welcome():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/signup')
def signup():
    return render_template("signup.html")


@app.route("/send",methods=['GET','POST'])
def send():
    email = request.form['email']
    pswd = request.form['pswd1']
    session['vem'] = email
    session['vpas'] = pswd
    user = User.query.filter_by(username=email).first()
    if user:
        flash("Email Already Exists")
        return redirect(url_for("signup"))
    else:
        msg = Message('Email Verification', sender='flaskapp389@gmail.com', recipients=[email])
        otp = randint(100000, 999999)
        session['otp'] = otp
        msg.body = 'We are sending this Otp for security Reasons.\nPlease dont share this otp with others\nYour OTP is ' + str(otp)
        mail.send(msg)
        return render_template("otp.html")

@app.route("/verify", methods=['GET','POST'])
def verify():
    otp = request.form['otp']
    if int(otp) == session['otp']:
        new_user = User(username=session['vem'],password=generate_password_hash(session['vpas']))
        db.session.add(new_user)
        db.session.commit()
        flash("SignUp Successful!!!")
        return redirect(url_for("signup"))
    flash("Incorrect Otp")
    return render_template("otp.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/loginUser", methods=['GET','POST'])
def loginUser():
    username = request.form['email']
    pswd = request.form['pswd']
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, pswd):
        login_user(user)
        return redirect(url_for('home'))
    flash("Please check your login details and try again.")
    return redirect(url_for("login"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/todoApp")
@login_required
def todoApp():
    todo_list = Todo.query.filter_by(username=current_user.username).order_by('complete').all()
    return render_template("todo.html", todo_list=todo_list)

@app.route("/addTodo", methods=['GET','POST'])
@login_required
def addTodo():
    title = request.form.get("title")
    new_todo = Todo(username=current_user.username,title=title,complete=False)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("todoApp"))

@app.route("/updateTodo/<int:todo_id>")
@login_required
def updateTodo(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for("todoApp"))

@app.route("/deleteTodo/<int:todo_id>")
@login_required
def deleteTodo(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("todoApp"))

@app.route("/qrCodeScanner")
@login_required
def qrCodeScanner():
    return render_template("scanner.html")

@app.route("/scanQr", methods=['GET','POST'])
@login_required
def scanQr():
    f = request.files['file']
    f.save(os.path.join("images", f.filename))
    d = decode(Image.open("images/"+f.filename))
    j = str(d[0].data.decode('ascii'))
    os.remove("images/"+f.filename)
    return render_template("scanner.html", data=j)

@app.route("/fileShare")
@login_required
def fileShare():
    files_list = Share.query.filter_by(to=current_user.username).order_by(Share.dt.desc()).all()
    return render_template("share.html",files_list=files_list)

@app.route("/getFiles")
@login_required
def getFiles():
    return render_template("getFiles.html")

@app.route("/sendFile", methods=['GET','POST'])
@login_required
def sendFile():
    file = request.files['file']
    email = request.form['email']
    user = User.query.filter_by(username=email).first()
    if user:
        new_file = Share(frm=current_user.username, to=email, data=file.read(), name=file.filename)
        db.session.add(new_file)
        db.session.commit()
        flash("File Sent Successfully")
        return redirect(url_for("getFiles"))
    else:
        flash("Email does not exists!!!")
        return redirect(url_for("getFiles"))

@app.route("/downloadFile/<int:file_id>")
@login_required
def downloadFile(file_id):
    file = Share.query.filter_by(id=file_id).first()
    return send_file(BytesIO(file.data),attachment_filename=file.name, as_attachment=True)

@app.route("/passwordGenerator")
@login_required
def passwordGenerator():
    return render_template("password.html")



if __name__ == "__main__":
    db.create_all()
    app.run()