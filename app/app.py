from flask import Flask, render_template,flash,redirect,url_for,request,session
from flask_socketio import SocketIO, emit
import json
import time
from random import randint, random
import threading
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin,LoginManager,login_required,login_user,logout_user
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length,DataRequired
from flask_bootstrap import Bootstrap
from datetime import timedelta

datosPH = {
		"cols":[
			{"id": "", "label": "i", "pattern": "", "type": "number"},
			{"id": "", "label": "PH", "pattern": "", "type": "number"}],
		"rows":[
				{"c":[
					{"v": 0, "f": None}, 
					{"v": 0, "f": None}]}]
					}

datosOX = {
		"cols":[
			{"id": "", "label": "i", "pattern": "", "type": "number"},
			{"id": "", "label": "PH", "pattern": "", "type": "number"}],
		"rows":[
				{"c":[
					{"v": 0, "f": None}, 
					{"v": 0, "f": None}]}]
					}

datosTUR = {
		"cols":[
			{"id": "", "label": "i", "pattern": "", "type": "number"},
			{"id": "", "label": "PH", "pattern": "", "type": "number"}],
		"rows":[
				{"c":[
					{"v": 0, "f": None}, 
					{"v": 0, "f": None}]}]
					}

ph = 0
ox = 0
tur = 0
n = -1
ng = 0
flujo = 50
estadoS = "ON"
estadoOnOff = "ON"
inicio = False

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True
login_manager = LoginManager()
login_manager.session_protection = 'None'
login_manager.login_view = 'login'
login_manager.init_app(app)
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
socketio = SocketIO(app)

class User(UserMixin,db.Model):
	__tablename__ = 'usuarios'
	id = db.Column(db.Integer,primary_key = True)
	username = db.Column(db.String(64),unique = True,index=True)
	password_hash = db.Column(db.String(128))

	def __repr__(self):
		return '<User %r' %self.username

	password_hash = db.Column(db.String(128))

	@property
	def password(self):
		raise AttributeError('password is not readable attribute')

	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self,password):
		return check_password_hash(self.password_hash,password)

class Data(db.Model):
	__tablename__ = 'datos'
	id = db.Column(db.Integer,primary_key = True)
	n = db.Column(db.Float)
	ph = db.Column(db.Float)
	ox = db.Column(db.Float)
	tur = db.Column(db.Float)

	def __repr__(self):
		return '<Data %r' %self.n

lenData = len(Data.query.all())

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class LoginForm(Form):
	username = StringField('Usuario',validators=[DataRequired(),Length(1,64)])
	password = PasswordField('Password',validators=[DataRequired()])
	submit = SubmitField('Log In')

def generarDatos():
	global n,ph,ox,tur,ng
	while True:
		socketio.sleep(0.5)
		if estadoS == 'PARO':
			pass
		elif estadoOnOff == 'OFF':
			if n == 99:n = -1
			n += 1
			ng += 1
			ph = 0
			ox = 0
			tur = 0
			if len(datosPH["rows"])>40:
				datosPH["rows"].pop(0)
				datosOX["rows"].pop(0)
				datosTUR["rows"].pop(0)
			datosPH["rows"].append(
			{"c":[
					{"v": ng, "f": None}, 
					{"v": ph, "f": None}]}
			)
			datosOX["rows"].append(
			{"c":[
					{"v": ng, "f": None}, 
					{"v": ox, "f": None}]}
			)
			datosTUR["rows"].append(
			{"c":[
					{"v": ng, "f": None}, 
					{"v": tur, "f": None}]}
			)
			strJsonPH = json.dumps(datosPH)
			strJsonOX = json.dumps(datosOX)
			strJsonTUR = json.dumps(datosTUR)
			socketio.emit('eventoDatosS',					{'ph':strJsonPH,'ox':strJsonOX,'tur':strJsonTUR,'phD':ph,'oxD':ox,'turD':tur    })
		else:
			if n == 99:n = -1
			n+= 1
			ng += 1
			ph = int(Data.query.all()[n].ph)
			ox = Data.query.all()[n].ox
			tur = Data.query.all()[n].tur
			if len(datosPH["rows"])>40:
				datosPH["rows"].pop(0)
				datosOX["rows"].pop(0)
				datosTUR["rows"].pop(0)
			datosPH["rows"].append(
			{"c":[
					{"v": ng, "f": None}, 
					{"v": ph, "f": None}]}
			)
			datosOX["rows"].append(
			{"c":[
					{"v": ng, "f": None}, 
					{"v": ox, "f": None}]}
			)
			datosTUR["rows"].append(
			{"c":[
					{"v": ng, "f": None}, 
					{"v": tur, "f": None}]}
			)
			strJsonPH = json.dumps(datosPH)
			strJsonOX = json.dumps(datosOX)
			strJsonTUR = json.dumps(datosTUR)
			socketio.emit('eventoDatosS',{'ph':strJsonPH,'ox':strJsonOX,'tur':strJsonTUR,'phD':ph,'oxD':ox,'turD':tur    })

socketio.start_background_task(target=generarDatos)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login',methods=['GET','POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user)
			return redirect(request.args.get('next') or url_for('index'))
		flash('Usuario o contraseña incorrecto')
	return render_template('login.html',form=form)

"""
@app.route('/logout')
def logout():
	logout_user()
	flash('Sesión terminada')
	return redirect(url_for('index'))
"""
@app.route('/historial')
#@login_required
def historial():
	return render_template('historial.html',datos = Data.query.all())

@app.route('/estado')
#@login_required
def estado():
	return render_template('estado.html')

@app.route('/phs')
#@login_required
def phs():
	return render_template('phs.html')

@app.route('/oxigenoD')
#@login_required
def oxigenoD():
	return render_template('oxigenoD.html')

@app.route('/turbidez')
#@login_required
def turbidez():
	return render_template('turbidez.html')

@app.route('/flujoF')
#@login_required
def flujoF():
	return render_template('flujoF.html')


@socketio.on('eventoConexion')
def conex():
	global n,ph,ox,tur,inicio
	socketio.emit('eventoFlujoS',{'flujo':flujo})
	socketio.emit('eventoEstadoS',{'estado':estadoS})
	socketio.sleep(1.5)
	strJsonPH = json.dumps(datosPH)
	strJsonOX = json.dumps(datosOX)
	strJsonTUR = json.dumps(datosTUR)
	socketio.emit('eventoDatosS',{'ph':strJsonPH,'ox':strJsonOX,'tur':strJsonTUR,'phD':ph,'oxD':ox,'turD':tur    })
	'''if not inicio:
		inicio = True
		while True:
			socketio.sleep(0.5)
			if estadoS == 'PARO':
				pass
			elif estadoOnOff == 'OFF':
				n += 1
				ph = 0
				ox = 0
				tur = 0
				if len(datosPH["rows"])>100:
					datosPH["rows"].pop(0)
					datosOX["rows"].pop(0)
					datosTUR["rows"].pop(0)
				datosPH["rows"].append(
				{"c":[
						{"v": n, "f": None}, 
						{"v": ph, "f": None}]}
				)
				datosOX["rows"].append(
				{"c":[
						{"v": n, "f": None}, 
						{"v": ox, "f": None}]}
				)
				datosTUR["rows"].append(
				{"c":[
						{"v": n, "f": None}, 
						{"v": tur, "f": None}]}
				)
				strJsonPH = json.dumps(datosPH)
				strJsonOX = json.dumps(datosOX)
				strJsonTUR = json.dumps(datosTUR)
				socketio.emit('eventoDatosS',{'ph':strJsonPH,'ox':strJsonOX,'tur':strJsonTUR,'phD':ph,'oxD':ox,'turD':tur    })
			else:
				n+= 1
				ph = int(randint(8,11)*(flujo/100))
				ox = float("%0.2f"%((randint(500,550)+random())*(flujo/100),))
				tur = float("%0.2f"%((randint(0,2)+random())*(flujo/100),))
				if len(datosPH["rows"])>100:
					datosPH["rows"].pop(0)
					datosOX["rows"].pop(0)
					datosTUR["rows"].pop(0)
				datosPH["rows"].append(
				{"c":[
						{"v": n, "f": None}, 
						{"v": ph, "f": None}]}
				)
				datosOX["rows"].append(
				{"c":[
						{"v": n, "f": None}, 
						{"v": ox, "f": None}]}
				)
				datosTUR["rows"].append(
				{"c":[
						{"v": n, "f": None}, 
						{"v": tur, "f": None}]}
				)
				strJsonPH = json.dumps(datosPH)
				strJsonOX = json.dumps(datosOX)
				strJsonTUR = json.dumps(datosTUR)
				socketio.emit('eventoDatosS',{'ph':strJsonPH,'ox':strJsonOX,'tur':strJsonTUR,'phD':ph,'oxD':ox,'turD':tur    })'''

"""
@socketio.on('disconnect')
def desconectar():
	logout_user()
	print('DESCONECTADO')
	session.pop('secret!!',None)
"""
@socketio.on('eventoPurga')
def purgar():
	global estadoS
	if estadoS != 'PARO':
		estadoS = 'Purga iniciada'
		socketio.emit('eventoEstadoS',{'estado':estadoS})
		socketio.sleep(3)
		estadoS = 'Purga finalizada'
		socketio.emit('eventoEstadoS',{'estado':estadoS})

@socketio.on('eventoMasFlujo')
def aumentarFlujo():
	global flujo
	if estadoS != 'PARO':
		flujo += 5
		socketio.emit('eventoFlujoS',{'flujo':flujo})


@socketio.on('eventoMenosFlujo')
def disminuirFlujo():
	global flujo
	if estadoS != 'PARO':
		flujo -= 5
		socketio.emit('eventoFlujoS',{'flujo':flujo})


@socketio.on('eventoParo')
def paro():
	global estadoS
	estadoS = "PARO"
	socketio.emit('eventoEstadoS',{'estado':estadoS})

@socketio.on('eventoSoplador')
def cambioSoplador():
	socketio.emit('eventoCambioSoplador')

@socketio.on('eventoOnOff')
def onOff():
	global estadoOnOff,estadoS
	if estadoS == 'PARO':
		estadoS = 'ON'
		estadoOnOff = 'ON'
		socketio.emit('eventoEstadoS',{'estado':estadoOnOff})
	elif estadoOnOff == "ON":
		estadoOnOff = "OFF"
		estadoS = 'OFF'
		socketio.emit('eventoEstadoS',{'estado':estadoOnOff})
	else:
		estadoOnOff = "ON"
		estadoS = 'ON'
		socketio.emit('eventoEstadoS',{'estado':estadoOnOff})


if __name__ == '__main__':
	socketio.run(app,debug = True,host= "0.0.0.0")
