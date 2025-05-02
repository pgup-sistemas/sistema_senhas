from app import create_app, db
from app.models import Guiche

app = create_app()

with app.app_context():
    nomes = [f"Guichê {i}" for i in range(1, 6)]
    for nome in nomes:
        if not Guiche.query.filter_by(nome=nome).first():
            guiche = Guiche(nome=nome, descricao=f"Guichê padrão {nome}")
            db.session.add(guiche)
    db.session.commit()
print("Guichês iniciais criados.")
