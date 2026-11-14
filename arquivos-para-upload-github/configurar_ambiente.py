"""Gera .env e contas MySQL locais sem publicar senhas. Não executa SQL no banco."""
import argparse
import os
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parent
CONTAS = (
    ('ADMIN', 'usr_admin_eventos', 'r_admin_eventos'),
    ('ORGANIZADOR', 'usr_organizador', 'r_organizador'),
    ('CONSULTA', 'usr_consulta', 'r_consulta'),
    ('AUTH', 'usr_app_auth', 'r_autenticacao'),
)


def gerar(destino=ROOT, host='localhost', porta=3306, rotacionar=False):
    destino = Path(destino)
    env_path = destino / '.env'
    sql_path = destino / 'sql' / '06_usuarios.local.sql'
    if not rotacionar and (env_path.exists() or sql_path.exists()):
        raise FileExistsError('Configuração local já existe. Use --rotacionar para substituir os dois arquivos.')
    if host not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Este gerador configura contas locais; use localhost, 127.0.0.1 ou ::1.')
    if not 1 <= porta <= 65535:
        raise ValueError('Porta inválida.')
    lines = ['# Arquivo privado. Não versionar nem incluir em ZIP.', f'DB_HOST={host}',
             f'DB_PORT={porta}', 'DB_NAME=eventos_academicos']
    sql = ['-- PRIVADO: executar como administrador após 06_seguranca.sql.',
           '-- CREATE/ALTER preservam os dados e os usuários da aplicação.']
    for perfil, usuario, role in CONTAS:
        senha = secrets.token_hex(24)
        lines += [f'DB_USER_{perfil}={usuario}', f'DB_PASS_{perfil}={senha}']
        sql += [f"CREATE USER IF NOT EXISTS '{usuario}'@'localhost' IDENTIFIED BY '{senha}';",
                f"ALTER USER '{usuario}'@'localhost' IDENTIFIED BY '{senha}';",
                f"GRANT '{role}' TO '{usuario}'@'localhost';",
                f"SET DEFAULT ROLE '{role}' TO '{usuario}'@'localhost';"]
    lines += ['FLASK_SECRET_KEY=' + secrets.token_hex(32), 'SESSION_COOKIE_SECURE=0']
    sql_path.parent.mkdir(parents=True, exist_ok=True)
    # Arquivos separados devem ser aplicados juntos durante uma parada da aplicação.
    for path, content in [(sql_path, '\n'.join(sql) + '\n'), (env_path, '\n'.join(lines) + '\n')]:
        temporary = path.with_name(path.name + '.tmp')
        with open(temporary, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        os.chmod(temporary, 0o600)
        temporary.replace(path)
    return env_path, sql_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--porta', type=int, default=3306)
    parser.add_argument('--rotacionar', action='store_true', help='substitui as credenciais locais existentes')
    args = parser.parse_args()
    try:
        paths = gerar(host=args.host, porta=args.porta, rotacionar=args.rotacionar)
    except (ValueError, FileExistsError) as exc:
        parser.exit(1, str(exc) + '\n')
    print('Gerados .env e sql/06_usuarios.local.sql. Nenhuma senha foi exibida.')
    print('Aplique o SQL no MySQL correspondente e reinicie a aplicação para concluir a rotação.')
