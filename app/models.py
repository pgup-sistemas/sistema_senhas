from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from . import db as db

class TipoAtendimento(db.Model):
    __tablename__ = 'tipos_atendimento'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    sigla = db.Column(db.String(3), unique=True, nullable=False)

class Guiche(db.Model):
    __tablename__ = 'guiches'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)

class Senha(db.Model):
    __tablename__ = 'senhas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipos_atendimento.id'), nullable=False)
    data_emissao = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='aguardando')
    guiche_id = db.Column(db.Integer, db.ForeignKey('guiches.id'))  # Relacionamento com guichê
    operador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))  # Novo campo para operador
    chamada_em = db.Column(db.DateTime)
    tipo = db.relationship('TipoAtendimento')
    operador = db.relationship('Usuario')
    guiche = db.relationship('Guiche')

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    guiche_id = db.Column(db.Integer, db.ForeignKey('guiches.id'))  # Relacionamento com guichê
    guiche = db.relationship('Guiche')

    @property
    def is_operator(self):
        return not self.is_admin

class Configuracao(db.Model):
    __tablename__ = 'configuracoes'
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.String(100))
