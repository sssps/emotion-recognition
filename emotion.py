from flask import Flask,render_template,request,session,logging,url_for,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
import secrets
  

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__,template_folder='template')
app.secret_key = 'super-secret-key'

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = params['gmail_user']
app.config['MAIL_PASSWORD'] = params['gmail_password']
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contact(db.Model):
  
    cno = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(80), nullable=False)
    lname = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Register(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    rno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    password =db.Column(db.String(20), nullable=False)
    password2 =db.Column(db.String(20), nullable=False)

class Forgetpassword(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String, nullable=False)
    token=db.Column(db.String(100), nullable=False)


if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

@app.route("/")
def home():
    return render_template('index.html',params=params)

@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/dashboard")
def dashboard():
	if ('email' in session and session['email']):
		return render_template('dashboard.html', params=params)
    

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        fname = request.form.get('fname')
        lname =request.form.get('lname')
        email = request.form.get('email')
        message = request.form.get('message')
        entry = Contact(fname=fname, lname=lname, message = message, email = email,date= datetime.now() )
        db.session.add(entry)
        db.session.commit()
    return render_template('contact.html',params=params)


@app.route('/register', methods=['GET','POST'])
def register():
    if(request.method=='POST'):
        name=request.form.get('name')
        email=request.form.get('email')
        password=request.form.get('password')
        password2=request.form.get('password2')
        if(password==password2):
            entry=Register(name=name,email=email,password=password,password2=password2)
            db.session.add(entry)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            flash("plz enter right password")
    return render_template('register.html', params=params)


@app.route('/login', methods=['GET','POST'])
def login():
    if ('email' in session and session['email']):
        return render_template('dashboard.html', params=params)

    if(request.method=="POST"):
        email=request.form["email"]
        password=request.form["password"]

        login=Register.query.filter_by(email=email, password=password).first()
        if login is not None:
            session['email']=email
            return render_template("dashboard.html",params=params)
        else:
            flash("plz enter right password")   
    return render_template('login.html',params=params)


@app.route("/forgetpassword", methods = ['GET','POST'])
def forgetpassword():
    if(request.method=='POST'):
        email=request.form.get('email')
        token=secrets.token_urlsafe(3)
        send_reset_email(email,token)
        entry=Forgetpassword(email=email,token=token)
        db.session.add(entry)
        db.session.commit()
        return render_template('mailsuccess.html', params=params)
    else:
        return render_template('forgetpassword.html',params=params)

def send_reset_email(email,token):
    message_body="http://127.0.0.1:5000/reset_password/"+token
    mail.send_message('New message from your email plz check the mail and click' ,
                          sender="params['gmail_user']",
                          recipients = [email],
                          body = message_body
                          )

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if(request.method=='POST'):
        email=request.form.get('email')
        password=request.form.get('password')
        record=Register.query.filter_by(email=email).first()
        if record:
            record.password=password
            record.password2=password
            db.session.add(record)
            db.transcation.commit()
            return redirect(url_for('login'))
        else:
            pass
    else:
        record = Forgetpassword.query.filter_by(token=token).first()
        if record:
                 return render_template('resetpassword.html', email=record.email)
                 
@app.route('/logout', methods=['GET','POST'])
def logout():
    session.pop('email')
    return redirect(url_for('login'))

@app.route('/main', methods=['GET','POST'])
def main():
    from capture import capture
    return render_template('main.html', params=params)

if __name__ == "__main__":
    
    app.run(debug=True)
