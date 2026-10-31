"""Cria um usuário da aplicação com senha em hash+sal (bcrypt). Uso:
    python criar_usuario.py LOGIN PERFIL      (PERFIL: ADMIN, ORGANIZADOR ou CONSULTA; a senha é pedida sem eco)
Usa a conta MySQL do perfil ADMIN definida no .env."""
import sys, getpass
from db import conectar, executar
from app import hash_senha

def criar(login, perfil, senha):
    cn = conectar("ADMIN")
    try:
        executar(cn, "INSERT INTO usuario_app (login, senha_hash, perfil) VALUES (%s, %s, %s)",
                 (login, hash_senha(senha), perfil))
        cn.commit()
    finally:
        cn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    s1 = getpass.getpass("Senha (8+ caracteres): ")
    if len(s1) < 8 or s1 != getpass.getpass("Repita a senha: "):
        sys.exit("Senhas diferentes ou curtas demais.")
    criar(sys.argv[1], sys.argv[2].upper(), s1)
    print("Usuário criado.")
