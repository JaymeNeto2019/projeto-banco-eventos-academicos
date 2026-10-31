"""Verificacoes seguras (sem escrever no MySQL) do projeto Flask.
Execute da raiz: python entrega_urgente/verificar_projeto.py
"""
from pathlib import Path
import ast, re, sys, importlib.util
root=Path(__file__).resolve().parent.parent
fails=[]
def check(label, ok, detail=''):
    print(('OK    ' if ok else 'FALHA ') + label + ((' - '+detail) if detail else ''))
    if not ok: fails.append(label)
required=['app/app.py','app/db.py','app/entidades.py','app/melhorias_rotas.py','app/teste_fumaca.py','app/templates/base.html','app/templates/login.html','app/templates/cadastro.html','app/templates/home.html','sql/01_ddl.sql','sql/06_seguranca.sql','sql/11_cadastro_publico.sql']
for path in required: check('Arquivo '+path, (root/path).is_file())
for path in root.glob('app/*.py'):
    try: ast.parse(path.read_text(encoding='utf-8'), filename=str(path));check('Sintaxe '+path.name,True)
    except (SyntaxError,UnicodeError) as e:check('Sintaxe '+path.name,False,str(e))
if (root/'app/melhorias_rotas.py').exists():
    s=(root/'app/melhorias_rotas.py').read_text(encoding='utf-8')
    check('Variavel tipo no cadastro participante',"tipo = request.form.get('tipo_participante'" in s)
if (root/'sql/11_cadastro_publico.sql').exists():
    s=(root/'sql/11_cadastro_publico.sql').read_text(encoding='utf-8')
    check('Banco correto na procedure', 'eventos_academicos_final' not in s and 'USE eventos_academicos;' in s)
if (root/'app/templates/base.html').exists():
    s=(root/'app/templates/base.html').read_text(encoding='utf-8')
    for endpoint in ['home','agenda','validar_certificado','participantes_lista','inscricoes_lista','presencas','op_inscrever','op_encerrar','usuario_novo']:
        check('Menu '+endpoint, "url_for('"+endpoint+"')" in s)
for mod in ['flask','mysql.connector','bcrypt','dotenv','jinja2']:
    try: __import__(mod);check('Dependencia '+mod,True)
    except ImportError:check('Dependencia '+mod,False,'Execute python -m pip install -r app/requirements.txt')
check('Modelo .env.example', (root/'.env.example').is_file())
check('Configuracao local .env', (root/'.env').is_file(), 'Credenciais sao privadas; nunca envie esse arquivo')
print('\nRESULTADO: %d problema(s) detectado(s).'%len(fails))
print('Este diagnostico NAO comprova conectividade MySQL, login real ou transacoes.')
sys.exit(bool(fails))
