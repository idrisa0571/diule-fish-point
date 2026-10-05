from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Samaki(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jina = db.Column(db.String(100), nullable=False)
    aina = db.Column(db.String(50))
    bei_kununua = db.Column(db.Float, default=0)
    bei_kuuza = db.Column(db.Float, default=0)
    stock_kg = db.Column(db.Float, default=0)
    tarehe = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def faida_kwa_kg(self):
        return self.bei_kuuza - self.bei_kununua


class Mvuvi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jina = db.Column(db.String(100), nullable=False)
    simu = db.Column(db.String(20))
    mahali = db.Column(db.String(100))


class Manunuzi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mvuvi_id = db.Column(db.Integer, db.ForeignKey('mvuvi.id'))
    samaki_id = db.Column(db.Integer, db.ForeignKey('samaki.id'))
    kiasi_kg = db.Column(db.Float, nullable=False)
    bei_kwa_kg = db.Column(db.Float, nullable=False)
    jumla = db.Column(db.Float)
    tarehe = db.Column(db.DateTime, default=datetime.utcnow)

    mvuvi = db.relationship('Mvuvi')
    samaki = db.relationship('Samaki')


class Mteja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jina = db.Column(db.String(100), nullable=False)
    simu = db.Column(db.String(20))
    deni = db.Column(db.Float, default=0)
    tarehe = db.Column(db.DateTime, default=datetime.utcnow)


class Mauzo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    samaki_id = db.Column(db.Integer, db.ForeignKey('samaki.id'))
    mteja_id = db.Column(db.Integer, db.ForeignKey('mteja.id'), nullable=True)
    kiasi_kg = db.Column(db.Float, nullable=False)
    bei_kwa_kg = db.Column(db.Float, nullable=False)
    jumla = db.Column(db.Float)
    aina_ya_malipo = db.Column(db.String(10))
    tarehe = db.Column(db.DateTime, default=datetime.utcnow)

    samaki = db.relationship('Samaki')
    mteja = db.relationship('Mteja')


class Malipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mteja_id = db.Column(db.Integer, db.ForeignKey('mteja.id'))
    kiasi = db.Column(db.Float, nullable=False)
    tarehe = db.Column(db.DateTime, default=datetime.utcnow)
    maelezo = db.Column(db.String(200))

    mteja = db.relationship('Mteja')


class Matumizi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aina = db.Column(db.String(100))
    kiasi = db.Column(db.Float, nullable=False)
    maelezo = db.Column(db.String(200))
    tarehe = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tarehe = db.Column(db.DateTime, default=datetime.utcnow)