"""Teste de fumaça da aplicação (Flask test client). Roda contra o banco REAL configurado no .env.
Uso:  python teste_fumaca.py        (precisa do banco criado: 01_ddl, 04, 05, 06 e dados de carga)
Imprime PASSOU/FALHOU por verificação: use a saída como evidência no relatório (B1/B2/B3/B5)."""
import sys, mysql.connector
from app import app
from criar_usuario import criar
from db import conectar, consultar

res = []
def check(nome, cond):
    res.append(cond); print(("PASSOU  " if cond else "FALHOU  ") + nome)

def novo_cliente():
    c = app.test_client(); c.get("/login"); return c

def post(c, url, data=None, seguir=True):
    with c.session_transaction() as s:
        tok = s["_csrf"]
    return c.post(url, data={**(data or {}), "_csrf": tok}, follow_redirects=seguir)

def entrar(login, senha):
    c = novo_cliente(); r = post(c, "/login", dict(login=login, senha=senha)); return c, r

def txt(r): return r.get_data(as_text=True)

def total(sql, p=()):
    c = conectar("ADMIN")
    try: return consultar(c, sql, p)[0]["n"]
    finally: c.close()

SENHA = "SenhaDeTeste#2026"
for lg, pf in (("t_admin", "ADMIN"), ("t_org", "ORGANIZADOR"), ("t_cons", "CONSULTA")):
    try: criar(lg, pf, SENHA)
    except mysql.connector.Error: pass  # já existe

print("== Login e senha com hash+sal ==")
c, r = entrar("t_admin", "senha-errada"); check("login com senha errada é recusado", "inválidos" in txt(r))
adm, r = entrar("t_admin", SENHA); check("login ADMIN ok", "Gestão de Eventos" in txt(r))
h = total("SELECT COUNT(*) AS n FROM usuario_app WHERE senha_hash LIKE '$2b$%' AND login='t_admin'"); check("senha gravada como hash bcrypt (nunca texto claro)", h == 1)
r = adm.post("/crud/sala/novo", data={}); check("POST sem token CSRF é rejeitado (400)", r.status_code == 400)

print("== CRUD e tratamento de erro ==")
post(adm, "/crud/sala/novo", dict(nome="Sala Teste", bloco="Z", capacidade="30"))
check("CRUD: criar sala", "Sala Teste" in txt(adm.get("/crud/sala")))
r = post(adm, "/crud/sala/novo", dict(nome="Sala Teste", bloco="Z", capacidade="30")); check("restrição UNIQUE vira mensagem amigável", "já existe uma sala" in txt(r).lower() and "Traceback" not in txt(r))
r = post(adm, "/crud/sala/novo", dict(nome="Sala X", bloco="Z", capacidade="0")); check("restrição CHECK vira mensagem amigável", "maior que zero" in txt(r))
sid = total("SELECT id_sala AS n FROM sala WHERE nome='Sala Teste' AND bloco='Z'")
post(adm, f"/crud/sala/{sid}/editar", dict(nome="Sala Teste", bloco="Z", capacidade="45"))
check("CRUD: alterar sala", total("SELECT capacidade AS n FROM sala WHERE id_sala=%s", (sid,)) == 45)
post(adm, f"/crud/sala/{sid}/excluir")
check("CRUD: excluir sala", total("SELECT COUNT(*) AS n FROM sala WHERE id_sala=%s", (sid,)) == 0)
cat = total("SELECT MIN(id_categoria) AS n FROM categoria_evento"); inst = total("SELECT MIN(id_instituicao) AS n FROM instituicao")
post(adm, "/crud/evento/novo", dict(id_categoria=cat, id_instituicao_promotora=inst, titulo="Evento CRUD Teste", data_inicio="2026-12-15T08:00",
     data_fim="2026-12-15T12:00", modalidade="ONLINE", valor_inscricao="0.00", gratuito="on"))
check("RN12: evento criado pela aplicação nasce com status PLANEJADO no histórico",
      total("SELECT COUNT(*) AS n FROM historico_status_evento h JOIN evento e ON e.id_evento=h.id_evento WHERE e.titulo='Evento CRUD Teste' AND h.status='PLANEJADO'") >= 1)
for ent in ("instituicao", "categoria_evento", "evento", "atividade"):
    check(f"CRUD: listagem de {ent}", adm.get(f"/crud/{ent}").status_code == 200)

print("== Consultas parametrizadas, relatório e SQL injection ==")
r = adm.get("/consulta/ocupacao?tipo=OFICINA&minimo=0"); check("consulta de ocupação (JOIN+GROUP BY+HAVING)", r.status_code == 200)
r = adm.get("/consulta/participacao?tipo=ALUNO&minimo=0"); check("consulta de participação", r.status_code == 200)
r = adm.get("/consulta/participacao?instituicao=%27+OR+%271%27%3D%271&minimo=0")
check("injeção ' OR '1'='1 tratada como texto (sem erro, sem vazamento)", r.status_code == 200 and "Nenhum resultado" in txt(r))
r = adm.get("/consulta/ocupacao?tipo=PALESTRA%27%3B+DROP+TABLE+sala%3B--&minimo=0")
check("injeção '; DROP TABLE ... não executa", r.status_code == 200 and total("SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='sala'") == 1)
check("relatório consolidado (view)", adm.get("/relatorio").status_code == 200)

print("== Transações (B3) ==")
import uuid
_c = conectar("ADMIN", "t_admin"); _cur = _c.cursor()  # dados fictícios só para o teste
_cur.execute("INSERT INTO evento (id_categoria, id_instituicao_promotora, titulo, data_inicio, data_fim, modalidade) "
             "SELECT (SELECT MIN(id_categoria) FROM categoria_evento), (SELECT MIN(id_instituicao) FROM instituicao), "
             "'Evento Teste Fumaça', '2026-12-10 08:00', '2026-12-10 12:00', 'ONLINE'")
ev = _cur.lastrowid
_cur.execute("INSERT INTO historico_status_evento (id_evento, sequencia, status, data_hora) VALUES (%s, 1, 'ABERTO', NOW())", (ev,))
_cur.execute("INSERT INTO atividade (id_evento, titulo, tipo_atividade, carga_horaria, vagas) VALUES (%s, 'Atividade Teste', 'OFICINA', 2.0, 10)", (ev,))
ativ = _cur.lastrowid
_cur.execute("INSERT INTO pessoa (nome, email) VALUES ('Participante Teste', %s)", (f"teste-{uuid.uuid4().hex[:8]}@exemplo.test",))
part = _cur.lastrowid
_cur.execute("INSERT INTO participante (id_pessoa, tipo_participante) VALUES (%s, 'EXTERNO')", (part,))
_cur.execute("INSERT INTO pessoa (nome, email) VALUES ('Participante Baixa Presenca', %s)", (f"teste-{uuid.uuid4().hex[:8]}@exemplo.test",)); part2 = _cur.lastrowid
_cur.execute("INSERT INTO participante (id_pessoa, tipo_participante) VALUES (%s, 'EXTERNO')", (part2,))
_cur.execute("INSERT INTO inscricao_atividade (id_participante, id_atividade, data_inscricao, status_inscricao, percentual_presenca) VALUES (%s, %s, NOW(), 'CONFIRMADA', 50)", (part2, ativ))
_cur.execute("SELECT MIN(id_sala) FROM sala"); sala = _cur.fetchone()[0]   # 2a atividade com sessao SOBREPOSTA (RN22)
_cur.execute("INSERT INTO atividade (id_evento,titulo,tipo_atividade,carga_horaria,vagas) VALUES (%s,'Atividade Sobreposta','OFICINA',2.0,10)", (ev,)); ativ2 = _cur.lastrowid
_cur.execute("INSERT INTO sessao_atividade (id_atividade,numero_sessao,id_sala,inicio,fim) VALUES (%s,1,%s,'2026-12-10 09:00','2026-12-10 11:00'),(%s,1,%s,'2026-12-10 10:00','2026-12-10 12:00')", (ativ, sala, ativ2, sala))
_c.commit(); _c.close()

antes = total("SELECT COUNT(*) AS n FROM inscricao_atividade")
post(adm, "/operacoes/inscrever", dict(id_participante=part, id_atividade=ativ, simular_falha="on"))
check("falha simulada: ROLLBACK, banco íntegro (mesma contagem)", total("SELECT COUNT(*) AS n FROM inscricao_atividade") == antes)
post(adm, "/operacoes/inscrever", dict(id_participante=part, id_atividade=ativ))
check("inscrição com sucesso: COMMIT", total("SELECT COUNT(*) AS n FROM inscricao_atividade") == antes + 1)
r = post(adm, "/operacoes/inscrever", dict(id_participante=part, id_atividade=ativ)); check("inscrição duplicada: mensagem amigável", "já existe" in txt(r).lower())
r = post(adm, "/operacoes/inscrever", dict(id_participante=part, id_atividade=ativ2))
check("RN22: inscrição CONFIRMADA em horário sobreposto é barrada", "sobreposto" in txt(r) and total("SELECT COUNT(*) AS n FROM inscricao_atividade WHERE id_participante=%s AND id_atividade=%s", (part, ativ2)) == 0)

_c = conectar("ADMIN", "t_admin"); _cur = _c.cursor()  # presença registrada (dispara a auditoria com autor t_admin)
_cur.execute("UPDATE inscricao_atividade SET percentual_presenca = 90 WHERE id_atividade=%s AND id_participante=%s AND status_inscricao='CONFIRMADA'", (ativ, part)); _c.commit(); _c.close()
H = "SELECT COUNT(*) AS n FROM historico_status_evento WHERE id_evento=%s"; C = "SELECT COUNT(*) AS n FROM certificado WHERE id_evento=%s"
post(adm, "/operacoes/encerrar-evento", dict(id_evento=ev, minimo="75", simular_falha="on"))
check("encerrar evento com falha: nada gravado nas 2 tabelas", total(H, (ev,)) == 1 and total(C, (ev,)) == 0)
post(adm, "/operacoes/encerrar-evento", dict(id_evento=ev, minimo="75"))
check("encerrar evento com sucesso: status + certificado (2 tabelas, 1 transação)", total(H, (ev,)) == 2 and total(C, (ev,)) == 1)
check("RN26: média de presença abaixo de 75% NÃO recebe certificado", total("SELECT COUNT(*) AS n FROM certificado WHERE id_evento=%s AND id_participante=%s", (ev, part2)) == 0)
r = post(adm, "/operacoes/encerrar-evento", dict(id_evento=ev, minimo="75"))
check("encerrar de novo é barrado (sem status duplicado)", "não pode ser encerrado novamente" in txt(r) and total(H, (ev,)) == 2)
_c = conectar("ADMIN"); _cur = _c.cursor()  # reabre o evento por fora para provocar o erro de certificado duplicado
_cur.execute("INSERT INTO historico_status_evento (id_evento, sequencia, status, data_hora) VALUES (%s, 3, 'ABERTO', NOW())", (ev,)); _c.commit(); _c.close()
r = post(adm, "/operacoes/encerrar-evento", dict(id_evento=ev, minimo="75"))
check("certificado duplicado: erro amigável e o status ENCERRADO também foi desfeito (ROLLBACK)",
      "já possui certificado" in txt(r) and total(H, (ev,)) == 3 and total(C, (ev,)) == 1)

print("== Perfis e auditoria (B5/B6) ==")
org, _ = entrar("t_org", SENHA); cons, _ = entrar("t_cons", SENHA)
check("organizador consegue listar eventos", org.get("/crud/evento").status_code == 200)
r = org.get("/auditoria"); check("organizador NÃO acessa auditoria (negado pelo banco)", r.status_code == 403 and "permissão" in txt(r))
r = post(org, "/crud/evento/1/excluir"); check("organizador NÃO exclui evento (negado pelo banco)", "permissão" in txt(r))
check("consulta vê a agenda pública", cons.get("/agenda").status_code == 200)
r = cons.get("/crud/instituicao"); check("consulta NÃO lê tabelas (negado pelo banco)", r.status_code == 403)
check("consulta NÃO vê o relatório", cons.get("/relatorio").status_code == 403)
check("admin vê a auditoria", adm.get("/auditoria").status_code == 200)
check("auditoria registrou o autor da aplicação (não o usuário do banco)", total("SELECT COUNT(*) AS n FROM auditoria WHERE autor IN ('t_admin','t_org')") >= 1)

print(f"\n{sum(res)}/{len(res)} verificações passaram")
sys.exit(0 if all(res) else 1)
