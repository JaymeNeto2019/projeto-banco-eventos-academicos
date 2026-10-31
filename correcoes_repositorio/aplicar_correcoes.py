#!/usr/bin/env python3
"""Aplica correcoes verificadas no projeto Flask/MySQL. Nao conecta ao banco."""
from pathlib import Path
import shutil, datetime, sys

root = Path(__file__).resolve().parent.parent
if not (root / 'app' / 'app.py').exists():
    print('ERRO: coloque a pasta correcoes_repositorio na RAIZ do repositorio.'); sys.exit(1)
backups = root / '.backup_correcoes' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
changes = []

def change(path, before, after):
    p = root / path
    if not p.is_file(): raise RuntimeError(f'Arquivo nao encontrado: {path}')
    s = p.read_text(encoding='utf-8')
    if after in s and before not in s:
        print('JA CORRIGIDO:', path); return
    count = s.count(before)
    if count != 1: raise RuntimeError(f'{path}: trecho esperado encontrado {count} vezes; nao alterado')
    dest = backups / path; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, dest)
    p.write_text(s.replace(before, after, 1), encoding='utf-8')
    changes.append(path)
    print('CORRIGIDO:', path)

try:
    change('app/melhorias_rotas.py',
        "            matricula = request.form.get('matricula_academica', '').strip()\n",
        "            matricula = request.form.get('matricula_academica', '').strip()\n            tipo = request.form.get('tipo_participante', '').strip()\n")
    change('sql/11_cadastro_publico.sql', 'USE eventos_academicos_final;', 'USE eventos_academicos;')
    change('sql/11_cadastro_publico.sql', 'ON PROCEDURE eventos_academicos_final.cadastrar_usuario_publico', 'ON PROCEDURE eventos_academicos.cadastrar_usuario_publico')
    change('app/templates/base.html', '<span class="nav-index">10</span> Encerrar evento / certificados', '<span class="nav-index">13</span> Encerrar evento / certificados')
    change('app/templates/base.html', '<span class="nav-index">11</span> Ocupação de atividades', '<span class="nav-index">14</span> Ocupação de atividades')
    change('app/templates/base.html', '<span class="nav-index">12</span> Participação por instituição', '<span class="nav-index">15</span> Participação por instituição')
    change('app/templates/base.html', '<span class="nav-index">13</span> Relatório de eventos', '<span class="nav-index">16</span> Relatório de eventos')
    change('app/templates/base.html', '<span class="nav-index">14</span> Criar usuário', '<span class="nav-index">17</span> Criar usuário')
    change('app/templates/base.html', '<span class="nav-index">15</span> Auditoria', '<span class="nav-index">18</span> Auditoria')
    change('app/README.md',
        '   `06_seguranca.sql` e o seu `06_usuarios.local.sql` (cópia de `06_usuarios.exemplo.sql` com senhas reais).',
        '   `06_seguranca.sql`, o seu `06_usuarios.local.sql` (cópia de `06_usuarios.exemplo.sql` com senhas reais) **e `sql/11_cadastro_publico.sql`**, necessário para criar contas na tela `/cadastro`. Execute os SQL a partir da raiz do repositório. O banco configurado em `.env` deve ser `eventos_academicos`.')
except Exception as e:
    print('PAROU:', e)
    print('Backups criados em:', backups)
    sys.exit(1)

print('\nArquivos alterados:', len(set(changes)))
print('Backups:', backups)
print('Verificacao de sintaxe:')
import ast
for path in ['app/app.py', 'app/melhorias_rotas.py', 'app/db.py']:
    ast.parse((root/path).read_text(encoding='utf-8'), filename=path)
    print(' OK', path)
print('Concluido. Rode os testes com MySQL antes da apresentacao.')
