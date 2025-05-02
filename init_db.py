from app import create_app, db
from app.models import TipoAtendimento, Usuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()
    # Tipos de atendimento
    tipos = [
        {'nome': 'Preferencial', 'sigla': 'P'},
        {'nome': 'Convencional', 'sigla': 'C'},
        {'nome': 'Pendências', 'sigla': 'PE'},
        {'nome': 'Resultados', 'sigla': 'R'}
    ]
    for t in tipos:
        if not TipoAtendimento.query.filter_by(sigla=t['sigla']).first():
            db.session.add(TipoAtendimento(nome=t['nome'], sigla=t['sigla']))
    # Usuário operador padrão
    if not Usuario.query.filter_by(username='operador').first():
        db.session.add(Usuario(username='operador', password_hash=generate_password_hash('1234'), is_admin=False))
    # Usuário admin padrão
    if not Usuario.query.filter_by(username='admin').first():
        db.session.add(Usuario(username='admin', password_hash=generate_password_hash('admin123'), is_admin=True))
    db.session.commit()
    print('Banco inicializado com sucesso!')
    print('Usuário operador: operador / 1234')
    print('Usuário admin: admin / admin123')
