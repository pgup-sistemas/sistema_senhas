@admin_bp.route('/relatorios/export')
@login_required
def exportar_relatorio():
    if not current_user.is_admin:
        return redirect(url_for('operator.painel'))
    import csv
    from io import StringIO
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
    from flask import Response
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=relatorio_senhas.csv"}
    )
