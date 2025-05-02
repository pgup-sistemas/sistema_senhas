from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date, datetime
from ..models import db, Senha, TipoAtendimento, Usuario, Guiche
from .. import socketio
from sqlalchemy import func
from werkzeug.security import check_password_hash

operator_bp = Blueprint('operator', __name__)

@operator_bp.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('admin.area_acesso'))

@operator_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.area_acesso'))

@operator_bp.route('/painel')
@login_required
def painel():
    hoje = date.today()
    fila = Senha.query.filter_by(status='aguardando', data_emissao=hoje).order_by(Senha.id).all()
    em_atendimento = Senha.query.filter_by(status='chamando', data_emissao=hoje, operador_id=current_user.id).order_by(Senha.chamada_em.desc()).all()
    historico = Senha.query.filter(Senha.status!='aguardando', Senha.data_emissao==hoje).order_by(Senha.chamada_em.desc()).limit(10).all()
    guiches = Guiche.query.filter_by(ativo=True).all()
    # Estatísticas do operador logado
    total_atendidas = Senha.query.filter(Senha.operador_id==current_user.id, Senha.status=='finalizado', Senha.data_emissao==hoje).count()
    tempo_medio = db.session.query(func.avg(func.strftime('%s', Senha.chamada_em) - func.strftime('%s', Senha.data_emissao))).filter(Senha.operador_id==current_user.id, Senha.status=='finalizado', Senha.chamada_em!=None, Senha.data_emissao==hoje).scalar()
    if tempo_medio:
        tempo_medio = int(tempo_medio)
    return render_template('operator/painel.html', fila=fila, em_atendimento=em_atendimento, historico=historico, guiches=guiches, total_atendidas=total_atendidas, tempo_medio=tempo_medio)

@operator_bp.route('/painel/data')
@login_required
def painel_data():
    hoje = date.today()
    fila = Senha.query.filter_by(status='aguardando', data_emissao=hoje).order_by(Senha.data_emissao, Senha.numero).all()
    em_atendimento = Senha.query.filter_by(status='chamando', data_emissao=hoje, operador_id=current_user.id).order_by(Senha.chamada_em.desc()).all()
    historico = Senha.query.filter(Senha.status!='aguardando', Senha.data_emissao==hoje).order_by(Senha.chamada_em.desc()).limit(30).all()
    fila_data = [
        {
            'id': s.id,
            'sigla': s.tipo.sigla,
            'numero': s.numero,
            'status': s.status
        } for s in fila
    ]
    em_atendimento_data = [
        {
            'id': s.id,
            'sigla': s.tipo.sigla,
            'numero': s.numero,
            'status': s.status,
            'chamada_em': s.chamada_em.strftime('%H:%M:%S') if s.chamada_em else ''
        } for s in em_atendimento
    ]
    historico_data = [
        {
            'id': s.id,
            'sigla': s.tipo.sigla,
            'numero': s.numero,
            'status': s.status,
            'chamada_em': s.chamada_em.strftime('%H:%M:%S') if s.chamada_em else ''
        } for s in historico
    ]
    return jsonify({'fila': fila_data, 'em_atendimento': em_atendimento_data, 'historico': historico_data})

@operator_bp.route('/set_guiche', methods=['POST'])
@login_required
def set_guiche():
    guiche_id = request.form.get('guiche_id')
    guiche = Guiche.query.get(guiche_id) if guiche_id else None
    if guiche:
        current_user.guiche_id = guiche.id
        db.session.commit()
    return redirect(url_for('operator.painel'))

@operator_bp.route('/call/<int:senha_id>', methods=['POST'])
@login_required
def call_next(senha_id):
    senha = Senha.query.get_or_404(senha_id)
    guiche = current_user.guiche
    if not guiche:
        flash('Selecione um guichê no topo da tela antes de chamar uma senha.', 'danger')
        return redirect(url_for('operator.painel'))
    if senha.status == 'aguardando':
        senha.status = 'chamando'
        senha.chamada_em = datetime.now()
        senha.operador_id = current_user.id
        senha.guiche_id = guiche.id
        db.session.commit()
        emitir_update_painel()
    return redirect(url_for('operator.painel'))

@operator_bp.route('/repeat/<int:senha_id>')
@login_required
def repeat_call(senha_id):
    senha = Senha.query.get_or_404(senha_id)
    # Só permitir repetir chamada se a senha está em atendimento pelo operador logado
    if senha.status == 'chamando' and senha.operador_id == current_user.id:
        senha.chamada_em = datetime.now()
        db.session.commit()
        emitir_update_painel()
    return redirect(url_for('operator.painel'))

@operator_bp.route('/finish/<int:senha_id>')
@login_required
def finish(senha_id):
    senha = Senha.query.get_or_404(senha_id)
    # Só permitir finalizar se a senha está em atendimento pelo operador logado
    if senha.status == 'chamando' and senha.operador_id == current_user.id:
        senha.status = 'finalizado'
        senha.chamada_em = datetime.now()
        db.session.commit()
        emitir_update_painel()
    return redirect(url_for('operator.painel'))

def emitir_update_painel():
    hoje = date.today()
    # Buscar as últimas 5 senhas chamadas (chamando ou finalizado)
    senhas = (
        Senha.query
        .filter(Senha.status != 'aguardando', Senha.data_emissao == hoje)
        .order_by(Senha.chamada_em.desc())
        .limit(5)
        .all()
    )
    data = [
        {
            'numero': s.numero,
            'tipo_sigla': s.tipo.sigla,
            'tipo_nome': s.tipo.nome,
            'guiche': s.guiche.nome if s.guiche else None,
            'status': s.status,
            'chamada_em': s.chamada_em.strftime('%H:%M:%S') if s.chamada_em else ''
        } for s in senhas
    ]
    socketio.emit('update_painel', {'senhas': data})

from . import operator
