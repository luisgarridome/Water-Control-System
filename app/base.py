from app import db,User,Data
import numpy as np

db.drop_all()
db.create_all()
usuario = User(username='usuario1')
usuario.password = '1234'
db.session.add(usuario)
n = np.array(range(1,101))
nd = n/10
ox = np.cos(nd) + np.log(nd)
tur = np.sin(nd) + np.log(nd)**2 - 3
ph = np.array(range(1,101))
ph[0:20] = 3
ph[20:50] = 5
ph[50:70] = 6
ph[70:100]=4
datos = list(Data(n=nda,ph=phd,ox=float("%0.2f"%(oxi)),tur=float("%0.2f"%(turb))) for nda,phd,oxi,turb in zip(n,ph,ox,tur))
db.session.add_all(datos)
db.session.commit()