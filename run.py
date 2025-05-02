from app import create_app, socketio
from flask import request
from datetime import date

app = create_app()

@socketio.on('get_painel')
def handle_get_painel():
    from app.models import Senha, TipoAtendimento
    hoje = date.today()
    senhas = Senha.query.filter(Senha.status.in_(['chamando']), Senha.data_emissao==hoje).order_by(Senha.chamada_em.desc()).all()
    data = [
        {
            'numero': s.numero,
            'tipo_sigla': s.tipo.sigla,
            'tipo_nome': s.tipo.nome,
            'guiche': s.guiche
        } for s in senhas
    ]
    socketio.emit('update_painel', {'senhas': data})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
