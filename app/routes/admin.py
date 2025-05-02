from flask import Blueprint, render_template, redirect, url_for, request, flash, Response
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from datetime import date, datetime
from ..models import db, Senha, TipoAtendimento, Usuario, Configuracao, Guiche
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
import csv
from io import StringIO

admin_bp = Blueprint('admin', __name__)

# Filtro Jinja para converter segundos em HH:MM
@admin_bp.app_template_filter('segundos_para_hhmm')
def segundos_para_hhmm(segundos):
    if segundos is None:
        return '-'
    try:
        segundos = int(segundos)
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        return f"{horas:02d}:{minutos:02d}"
    except Exception:
        return '-'

def init_login_manager(login_manager):
    login_manager.login_view = 'admin.area_acesso'

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('admin.area_acesso'))

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.area_acesso'))

@admin_bp.route('/')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Acesso restrito a administradores.', 'danger')
        return redirect(url_for('admin.area_acesso'))
    hoje = date.today()
    total_emitidas = Senha.query.filter(Senha.data_emissao==hoje).count()
    total_chamadas = Senha.query.filter(Senha.data_emissao==hoje, Senha.status!='aguardando').count()
    tempo_medio = db.session.query(func.avg(func.strftime('%s', Senha.chamada_em) - func.strftime('%s', Senha.data_emissao))).filter(Senha.data_emissao==hoje, Senha.chamada_em!=None).scalar()
    if tempo_medio:
        tempo_medio = round(tempo_medio)
    else:
        tempo_medio = None
    # Gráfico: senhas emitidas por tipo
    tipos = TipoAtendimento.query.all()
    grafico_tipos = []
    for tipo in tipos:
        count = Senha.query.filter_by(tipo_id=tipo.id, data_emissao=hoje).count()
        grafico_tipos.append({'label': tipo.nome, 'sigla': tipo.sigla, 'value': count})
    return render_template('admin/dashboard.html', total_emitidas=total_emitidas, total_chamadas=total_chamadas, tempo_medio=tempo_medio, grafico_tipos=grafico_tipos)

@admin_bp.route('/relatorios')
@login_required
def relatorios():
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')
    query = Senha.query
    if data_inicio:
        query = query.filter(Senha.data_emissao >= data_inicio)
    if data_fim:
        query = query.filter(Senha.data_emissao <= data_fim)
    senhas = query.order_by(Senha.data_emissao.desc(), Senha.numero).all()

    # 1. Senhas emitidas por tipo
    senhas_por_tipo = db.session.query(
        TipoAtendimento.nome,
        TipoAtendimento.sigla,
        func.count(Senha.id)
    ).join(Senha, Senha.tipo_id == TipoAtendimento.id)
    if data_inicio:
        senhas_por_tipo = senhas_por_tipo.filter(Senha.data_emissao >= data_inicio)
    if data_fim:
        senhas_por_tipo = senhas_por_tipo.filter(Senha.data_emissao <= data_fim)
    senhas_por_tipo = senhas_por_tipo.group_by(TipoAtendimento.id).all()

    # 2. Atendimentos por guichê
    atendimentos_por_guiche = db.session.query(
        Guiche.nome,
        func.count(Senha.id)
    ).join(Senha, Senha.guiche_id == Guiche.id)
    if data_inicio:
        atendimentos_por_guiche = atendimentos_por_guiche.filter(Senha.data_emissao >= data_inicio)
    if data_fim:
        atendimentos_por_guiche = atendimentos_por_guiche.filter(Senha.data_emissao <= data_fim)
    atendimentos_por_guiche = atendimentos_por_guiche.group_by(Guiche.id).all()

    # 3. Tempos de atendimento (média, min, max por dia)
    tempos_atendimento = db.session.query(
        Senha.data_emissao,
        func.count(Senha.id),
        func.avg(func.strftime('%s', Senha.chamada_em) - func.strftime('%s', Senha.data_emissao)),
        func.min(func.strftime('%s', Senha.chamada_em) - func.strftime('%s', Senha.data_emissao)),
        func.max(func.strftime('%s', Senha.chamada_em) - func.strftime('%s', Senha.data_emissao))
    ).filter(Senha.status == 'finalizado', Senha.chamada_em != None)
    if data_inicio:
        tempos_atendimento = tempos_atendimento.filter(Senha.data_emissao >= data_inicio)
    if data_fim:
        tempos_atendimento = tempos_atendimento.filter(Senha.data_emissao <= data_fim)
    tempos_atendimento = tempos_atendimento.group_by(Senha.data_emissao).all()

    # 4. Atendimentos por operador
    atendimentos_por_operador = db.session.query(
        Usuario.username,
        func.count(Senha.id)
    ).join(Senha, Senha.operador_id == Usuario.id)
    if data_inicio:
        atendimentos_por_operador = atendimentos_por_operador.filter(Senha.data_emissao >= data_inicio)
    if data_fim:
        atendimentos_por_operador = atendimentos_por_operador.filter(Senha.data_emissao <= data_fim)
    atendimentos_por_operador = atendimentos_por_operador.group_by(Usuario.id).all()

    return render_template('admin/relatorios.html',
        senhas=senhas,
        senhas_por_tipo=senhas_por_tipo,
        atendimentos_por_guiche=atendimentos_por_guiche,
        tempos_atendimento=tempos_atendimento,
        atendimentos_por_operador=atendimentos_por_operador
    )

@admin_bp.route('/relatorios/export')
@login_required
def exportar_relatorio():
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')
    query = Senha.query
    if data_inicio:
        query = query.filter(Senha.data_emissao >= data_inicio)
    if data_fim:
        query = query.filter(Senha.data_emissao <= data_fim)
    senhas = query.order_by(Senha.data_emissao.desc(), Senha.numero).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Data', 'Senha', 'Tipo', 'Status', 'Guichê', 'Hora Chamada'])
    for s in senhas:
        writer.writerow([
            s.data_emissao.strftime('%d/%m/%Y'),
            f"{s.tipo.sigla}{s.numero:03d}",
            s.tipo.nome,
            s.status,
            s.guiche or '-',
            s.chamada_em.strftime('%H:%M:%S') if s.chamada_em else '-'
        ])
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=relatorio_senhas.csv"}
    )

@admin_bp.route('/usuarios')
@login_required
def usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = bool(request.form.get('is_admin'))
        if Usuario.query.filter_by(username=username).first():
            flash('Usuário já existe.', 'danger')
            return redirect(url_for('admin.novo_usuario'))
        user = Usuario(username=username, password_hash=generate_password_hash(password), is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('admin.usuarios'))
    return render_template('admin/usuario_form.html')

@admin_bp.route('/usuarios/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(user_id):
    user = Usuario.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']:
            user.password_hash = generate_password_hash(request.form['password'])
        user.is_admin = bool(request.form.get('is_admin'))
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('admin.usuarios'))
    return render_template('admin/usuario_edit.html', usuario=user)

@admin_bp.route('/usuarios/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_usuario(user_id):
    user = Usuario.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Não é possível remover o usuário admin padrão.', 'danger')
        return redirect(url_for('admin.usuarios'))
    db.session.delete(user)
    db.session.commit()
    flash('Usuário removido!', 'success')
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/tipos')
@login_required
def tipos():
    tipos = TipoAtendimento.query.all()
    return render_template('admin/tipos.html', tipos=tipos)

@admin_bp.route('/tipos/novo', methods=['GET', 'POST'])
@login_required
def novo_tipo():
    if request.method == 'POST':
        nome = request.form['nome']
        sigla = request.form['sigla']
        if TipoAtendimento.query.filter_by(sigla=sigla).first():
            flash('Sigla já cadastrada.', 'danger')
            return redirect(url_for('admin.novo_tipo'))
        tipo = TipoAtendimento(nome=nome, sigla=sigla)
        db.session.add(tipo)
        db.session.commit()
        flash('Tipo de atendimento criado com sucesso!', 'success')
        return redirect(url_for('admin.tipos'))
    return render_template('admin/tipo_form.html')

@admin_bp.route('/tipos/edit/<int:tipo_id>', methods=['GET', 'POST'])
@login_required
def editar_tipo(tipo_id):
    tipo = TipoAtendimento.query.get_or_404(tipo_id)
    if request.method == 'POST':
        tipo.nome = request.form['nome']
        tipo.sigla = request.form['sigla']
        db.session.commit()
        flash('Tipo atualizado com sucesso!', 'success')
        return redirect(url_for('admin.tipos'))
    return render_template('admin/tipo_edit.html', tipo=tipo)

@admin_bp.route('/tipos/delete/<int:tipo_id>', methods=['POST'])
@login_required
def delete_tipo(tipo_id):
    tipo = TipoAtendimento.query.get_or_404(tipo_id)
    db.session.delete(tipo)
    db.session.commit()
    flash('Tipo removido!', 'success')
    return redirect(url_for('admin.tipos'))

@admin_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    config_keys = ['nome_clinica', 'mensagem_painel']
    config = {c.chave: c.valor for c in Configuracao.query.filter(Configuracao.chave.in_(config_keys))}
    if request.method == 'POST':
        for key in config_keys:
            valor = request.form.get(key, '')
            conf = Configuracao.query.filter_by(chave=key).first()
            if conf:
                conf.valor = valor
            else:
                db.session.add(Configuracao(chave=key, valor=valor))
        db.session.commit()
        flash('Configurações salvas!', 'success')
        return redirect(url_for('admin.configuracoes'))
    return render_template('admin/configuracoes.html', config=config)

@admin_bp.route('/area-acesso', methods=['GET', 'POST'])
def area_acesso():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.area_acesso'))
        flash('Usuário ou senha inválidos.', 'danger')
    login_message = None
    if 'message' in request.args:
        login_message = request.args['message']
    return render_template('admin/area_acesso.html', login_message=login_message)
