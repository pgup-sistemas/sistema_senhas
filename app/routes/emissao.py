from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date
from ..models import db, Senha, TipoAtendimento, Usuario, Configuracao
from werkzeug.security import check_password_hash
from ..utils.impressao import imprimir_senha
from sqlalchemy import func

emissao_bp = Blueprint('emissao', __name__)

@emissao_bp.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('admin.area_acesso'))

@emissao_bp.route('/', methods=['GET', 'POST'])
@login_required
def emitir():
    tipos = TipoAtendimento.query.all()
    configs = {c.chave: c.valor for c in Configuracao.query.filter(Configuracao.chave.in_(['nome_clinica', 'mensagem_painel']))}
    senha_emitida = None
    tipo_emitido = None
    erro = None
    if request.method == 'POST':
        tipo_id = request.form.get('tipo_id')
        tipo = TipoAtendimento.query.get(tipo_id)
        if not tipo:
            erro = 'Tipo de atendimento inválido.'
        else:
            hoje = date.today()
            ultima_data = Configuracao.query.filter_by(chave='ultima_data_emissao').first()
            if not ultima_data or ultima_data.valor != hoje.strftime('%Y-%m-%d'):
                Senha.query.delete()
                db.session.commit()
                if not ultima_data:
                    ultima_data = Configuracao(chave='ultima_data_emissao', valor=hoje.strftime('%Y-%m-%d'))
                    db.session.add(ultima_data)
                else:
                    ultima_data.valor = hoje.strftime('%Y-%m-%d')
                db.session.commit()
            ultima_senha = Senha.query.filter_by(tipo_id=tipo.id, data_emissao=hoje).order_by(Senha.numero.desc()).first()
            proximo_numero = 1 if not ultima_senha else ultima_senha.numero + 1
            senha = Senha(numero=proximo_numero, tipo_id=tipo.id, data_emissao=hoje)
            db.session.add(senha)
            db.session.commit()
            senha_emitida = senha
            tipo_emitido = tipo
            # Impressão automática
            sucesso, msg_impressao = imprimir_senha(senha_emitida, tipo_emitido, nome_clinica=configs.get('nome_clinica'))
            if not sucesso:
                erro = f'Erro ao imprimir: {msg_impressao}'
    return render_template('emissao/emitir.html', tipos=tipos, senha_emitida=senha_emitida, tipo_emitido=tipo_emitido, config_nome_clinica=configs.get('nome_clinica'), config_mensagem_painel=configs.get('mensagem_painel'), erro=erro)

@emissao_bp.route('/ultima_senha/<int:tipo_id>', methods=['GET'])
@login_required
def ultima_senha(tipo_id):
    hoje = date.today()
    senha = Senha.query.filter_by(tipo_id=tipo_id, data_emissao=hoje).order_by(Senha.numero.desc()).first()
    if senha:
        return jsonify({'numero': senha.numero, 'sigla': senha.tipo.sigla, 'id': senha.id})
    return jsonify({'numero': None, 'sigla': '', 'id': None})

@emissao_bp.route('/reimprimir/<int:senha_id>', methods=['POST'])
@login_required
def reimprimir_senha(senha_id):
    senha = Senha.query.get_or_404(senha_id)
    tipo = TipoAtendimento.query.get(senha.tipo_id)
    configs = {c.chave: c.valor for c in Configuracao.query.filter(Configuracao.chave.in_(['nome_clinica', 'mensagem_painel']))}
    sucesso, msg_impressao = imprimir_senha(senha, tipo, nome_clinica=configs.get('nome_clinica'))
    return jsonify({'sucesso': sucesso, 'mensagem': msg_impressao})

@emissao_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.area_acesso'))
