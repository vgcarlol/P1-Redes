from flask import Flask
from flask_jsonrpc import JSONRPC
from models import Session, Usuario

app = Flask(__name__)
jsonrpc = JSONRPC(app, '/api')

@jsonrpc.method('get_pending_balance')
def get_pending_balance(name: str) -> float:
    session = Session()
    usuario = session.query(Usuario).filter_by(nombre=name).first()
    session.close()
    if not usuario:
        raise Exception(f"Usuario '{name}' no encontrado.")
    return usuario.saldo_pendiente

@jsonrpc.method('register_payment')
def register_payment(name: str, amount: float) -> str:
    session = Session()
    usuario = session.query(Usuario).filter_by(nombre=name).first()
    if not usuario:
        session.close()
        raise Exception(f"Usuario '{name}' no encontrado.")
    usuario.saldo_pendiente = max(usuario.saldo_pendiente - amount, 0)
    session.commit()
    session.close()
    return f"Pago de Q{amount} registrado exitosamente. Nuevo saldo: Q{usuario.saldo_pendiente}"

if __name__ == '__main__':
    app.run(port=5000)
