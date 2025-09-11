from models import Base, engine, Session, Usuario

Base.metadata.create_all(engine)

session = Session()

usuarios = [
    Usuario(nombre='Carlos', saldo_pendiente=300),
    Usuario(nombre='Andrea', saldo_pendiente=150),
    Usuario(nombre='Luis', saldo_pendiente=0)
]

session.add_all(usuarios)
session.commit()
session.close()

print("✅ Base de datos inicializada.")
