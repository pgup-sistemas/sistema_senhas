from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import db, Guiche

admin_guiche_bp = Blueprint('admin_guiche', __name__)

@admin_guiche_bp.route('/admin/guiches')
@login_required
def listar_guiches():
    if not current_user.is_admin:
        return redirect(url_for('operator.painel'))
    guiches = Guiche.query.all()
    return render_template('admin/guiche_list.html', guiches=guiches)

@admin_guiche_bp.route('/admin/guiches/novo', methods=['GET', 'POST'])
@login_required
def novo_guiche():
    if not current_user.is_admin:
        return redirect(url_for('operator.painel'))
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        if Guiche.query.filter_by(nome=nome).first():
            flash('Nome de guichê já existe.', 'danger')
            return redirect(url_for('admin_guiche.novo_guiche'))
        guiche = Guiche(nome=nome, descricao=descricao)
        db.session.add(guiche)
        db.session.commit()
        flash('Guichê criado com sucesso!', 'success')
        return redirect(url_for('admin_guiche.listar_guiches'))
    return render_template('admin/guiche_form.html')

@admin_guiche_bp.route('/admin/guiches/edit/<int:guiche_id>', methods=['GET', 'POST'])
@login_required
def editar_guiche(guiche_id):
    if not current_user.is_admin:
        return redirect(url_for('operator.painel'))
    guiche = Guiche.query.get_or_404(guiche_id)
    if request.method == 'POST':
        guiche.nome = request.form['nome']
        guiche.descricao = request.form['descricao']
        guiche.ativo = bool(request.form.get('ativo'))
        db.session.commit()
        flash('Guichê atualizado!', 'success')
        return redirect(url_for('admin_guiche.listar_guiches'))
    return render_template('admin/guiche_form.html', guiche=guiche)

@admin_guiche_bp.route('/admin/guiches/delete/<int:guiche_id>', methods=['POST'])
@login_required
def deletar_guiche(guiche_id):
    if not current_user.is_admin:
        return redirect(url_for('operator.painel'))
    guiche = Guiche.query.get_or_404(guiche_id)
    db.session.delete(guiche)
    db.session.commit()
    flash('Guichê removido!', 'success')
    return redirect(url_for('admin_guiche.listar_guiches'))
