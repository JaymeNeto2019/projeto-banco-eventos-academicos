"""Aplicação web do projeto (Flask). O que se avalia aqui é o que ela revela sobre o BANCO:
consultas parametrizadas, transações explícitas, erros de restrição tratados e acesso por perfil."""
import os, secrets, functools
from datetime import datetime
from decimal import Decimal, InvalidOperation

import bcrypt
import mysql.connector
from dotenv import load_dotenv
from flask import (Flask, abort, flash, g, redirect, render_template, request, session, url_for)

load_dotenv()
from db import conectar, consultar, executar, mensagem_erro  # noqa: E402
from entidades import ENTIDADES  # noqa: E402

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
PERFIS = ("ADMIN", "ORGANIZADOR", "CONSULTA")


# ----------------------------------------------------------------- infraestrutura
def cn():
    """Conexão do request, com a conta MySQL do PERFIL logado. O banco é quem barra o acesso indevido."""
    if "cn" not in g:
        g.cn = conectar(session["perfil"], session.get("login"))
    return g.cn


@app.teardown_appcontext
def fechar(_exc):
    c = g.pop("cn", None)
    if c is not None:
        try:
            c.close()  # transação pendente é desfeita
        except Exception:
            pass


@app.before_request
def proteger_csrf():
    if request.method == "POST":
        tok = session.get("_csrf", "")
        if not tok or not secrets.compare_digest(tok, request.form.get("_csrf", "")):
            abort(400)


@app.context_processor
def contexto():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return dict(csrf=session["_csrf"], perfil=session.get("perfil"), login=session.get("login"))


def login_required(f):
    @functools.wraps(f)
    def w(*a, **k):
        if "perfil" not in session:
            return redirect(url_for("login"))
        return f(*a, **k)
    return w


@app.errorhandler(mysql.connector.Error)
def erro_banco(e):
    msg = mensagem_erro(e)  # nunca mostramos a exceção bruta do driver ao usuário
    if request.method == "POST":
        flash(msg, "erro")
        return redirect(request.referrer or url_for("home"))
    return render_template("erro.html", msg=msg), 403 if getattr(e, "errno", 0) in (1142, 1143, 1044) else 400


# ----------------------------------------------------------------- login / usuários
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        lg = request.form.get("login", "").strip()
        senha = request.form.get("senha", "").encode()
        try:
            c = conectar("AUTH")  # conta mínima: só lê usuario_app e atualiza ultimo_login
        except (KeyError, mysql.connector.Error) as e:
            flash("A configuração do banco não está disponível. Preencha o arquivo .env e confira o MySQL.", "erro")
            return render_template("login.html")
        try:
            rows = consultar(c, "SELECT id_usuario, senha_hash, perfil, ativo FROM usuario_app WHERE login = %s", (lg,))
            u = rows[0] if rows else None
            hash_ = u["senha_hash"].encode() if u else bcrypt.hashpw(b"x", bcrypt.gensalt())  # tempo parecido
            ok = bcrypt.checkpw(senha, hash_) and u is not None and u["ativo"]
            if ok:
                executar(c, "UPDATE usuario_app SET ultimo_login = NOW() WHERE id_usuario = %s", (u["id_usuario"],))
                c.commit()
        finally:
            c.close()
        if ok:
            session.clear()
            session.update(login=lg, perfil=u["perfil"], _csrf=secrets.token_hex(16))
            return redirect(url_for("agenda" if u["perfil"] == "CONSULTA" else "home"))
        flash("Login ou senha inválidos.", "erro")
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def hash_senha(senha: str) -> str:
    """bcrypt gera o SAL aleatório e o embute no hash ($2b$12$<sal><hash>)."""
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(rounds=12)).decode()


@app.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
def usuario_novo():
    if request.method == "POST":
        lg, senha, perf = request.form["login"].strip(), request.form["senha"], request.form["perfil"]
        if len(lg) < 3 or len(senha) < 8 or perf not in PERFIS:
            flash("Login com 3+ caracteres, senha com 8+ e perfil válido são obrigatórios.", "erro")
        else:
            executar(cn(), "INSERT INTO usuario_app (login, senha_hash, perfil) VALUES (%s, %s, %s)",
                     (lg, hash_senha(senha), perf))
            cn().commit()
            flash(f"Usuário {lg} criado.", "ok")
            return redirect(url_for("usuario_novo"))
    return render_template("usuario_novo.html", perfis=PERFIS)


@app.route("/")
@login_required
def home():
    return render_template("home.html", entidades=ENTIDADES)


# ----------------------------------------------------------------- CRUD genérico
def converter(c, bruto):
    t = c["t"]
    if t == "bool":
        return 1 if bruto in ("on", "1", "true") else 0
    if bruto is None or bruto.strip() == "":
        return None
    bruto = bruto.strip()
    if t == "int":
        return int(bruto)
    if t == "dec":
        return Decimal(bruto.replace(",", "."))
    if t == "datetime":
        return bruto.replace("T", " ")
    return bruto


def ler_form(ent):
    vals, erros = [], []
    for c in ent["campos"]:
        try:
            v = converter(c, request.form.get(c["n"]))
        except (ValueError, InvalidOperation):
            erros.append(f"Valor inválido em «{c['r']}».")
            v = None
        if v is None and c["req"] and c["t"] != "bool":
            erros.append(f"«{c['r']}» é obrigatório.")
        vals.append(v)
    return vals, erros


def opcoes(ent):
    return {c["n"]: consultar(cn(), c["q"]) for c in ent["campos"] if c["t"] == "fk"}


def ent_or_404(nome):
    if nome not in ENTIDADES:
        abort(404)
    return ENTIDADES[nome]


@app.route("/crud/<nome>")
@login_required
def crud_lista(nome):
    e = ent_or_404(nome)
    sql = f"SELECT {', '.join(e['lista'])} FROM {nome} ORDER BY {e['ordem']} LIMIT 200"  # identificadores fixos do config
    return render_template("crud_lista.html", nome=nome, e=e, rows=consultar(cn(), sql))


@app.route("/crud/<nome>/novo", methods=["GET", "POST"])
@app.route("/crud/<nome>/<int:pk>/editar", methods=["GET", "POST"])
@login_required
def crud_form(nome, pk=None):
    e = ent_or_404(nome)
    valores = {}
    if request.method == "POST":
        vals, erros = ler_form(e)
        valores = request.form
        if not erros:
            cols = [c["n"] for c in e["campos"]]
            try:
                if pk is None:
                    _, novo_id = executar(cn(), f"INSERT INTO {nome} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})", vals)
                    if nome == "evento":  # RN12: todo evento nasce com status inicial no histórico (mesma transação)
                        executar(cn(), "INSERT INTO historico_status_evento (id_evento, sequencia, status, data_hora, observacao) "
                                       "VALUES (%s, 1, 'PLANEJADO', NOW(), 'Criado pela aplicação')", (novo_id,))
                else:
                    executar(cn(), f"UPDATE {nome} SET {', '.join(c + ' = %s' for c in cols)} WHERE {e['pk']} = %s", vals + [pk])
                cn().commit()
                flash("Registro salvo.", "ok")
                return redirect(url_for("crud_lista", nome=nome))
            except mysql.connector.Error as ex:
                cn().rollback()
                erros.append(mensagem_erro(ex))
        for m in erros:
            flash(m, "erro")
    elif pk is not None:
        r = consultar(cn(), f"SELECT * FROM {nome} WHERE {e['pk']} = %s", (pk,))
        if not r:
            abort(404)
        valores = {k: (v.strftime("%Y-%m-%dT%H:%M") if isinstance(v, datetime) else v) for k, v in r[0].items()}
    return render_template("crud_form.html", nome=nome, e=e, pk=pk, v=valores, opc=opcoes(e))


@app.post("/crud/<nome>/<int:pk>/excluir")
@login_required
def crud_excluir(nome, pk):
    e = ent_or_404(nome)
    try:
        executar(cn(), f"DELETE FROM {nome} WHERE {e['pk']} = %s", (pk,))
        cn().commit()
        flash("Registro excluído.", "ok")
    except mysql.connector.Error as ex:
        cn().rollback()
        flash(mensagem_erro(ex), "erro")
    return redirect(url_for("crud_lista", nome=nome))


# ----------------------------------------------------------------- consultas parametrizadas (JOIN + agregação)
def nulo(v):
    v = (v or "").strip()
    return v or None


@app.route("/consulta/ocupacao")
@login_required
def consulta_ocupacao():
    f = {k: nulo(request.args.get(k)) for k in ("tipo", "de", "ate")}
    minimo = nulo(request.args.get("minimo")) or "0"
    rows = None
    if request.args:
        rows = consultar(cn(), """
            SELECT e.titulo AS evento, a.titulo AS atividade, a.tipo_atividade AS tipo, a.vagas,
                   COALESCE(SUM(ia.status_inscricao = 'CONFIRMADA'), 0)   AS confirmadas,
                   COALESCE(SUM(ia.status_inscricao = 'LISTA_ESPERA'), 0) AS lista_espera,
                   ROUND(100 * COALESCE(SUM(ia.status_inscricao = 'CONFIRMADA'), 0) / a.vagas, 1) AS ocupacao_pct
            FROM atividade a
            JOIN evento e ON e.id_evento = a.id_evento
            LEFT JOIN inscricao_atividade ia ON ia.id_atividade = a.id_atividade
            WHERE (%s IS NULL OR a.tipo_atividade = %s)
              AND (%s IS NULL OR e.data_inicio >= %s)
              AND (%s IS NULL OR e.data_inicio < DATE_ADD(%s, INTERVAL 1 DAY))
            GROUP BY a.id_atividade, e.titulo, a.titulo, a.tipo_atividade, a.vagas
            HAVING ocupacao_pct >= %s
            ORDER BY ocupacao_pct DESC, e.titulo
            LIMIT 200""", (f["tipo"], f["tipo"], f["de"], f["de"], f["ate"], f["ate"], minimo))
    campos = [dict(n="tipo", r="Tipo de atividade", t="select", opts=["", "PALESTRA", "MINICURSO", "MESA_REDONDA", "OFICINA"]),
              dict(n="de", r="Evento a partir de", t="date"), dict(n="ate", r="Evento até", t="date"),
              dict(n="minimo", r="Ocupação mínima (%)", t="number")]
    return render_template("consulta.html", titulo="Ocupação das atividades", campos=campos, rows=rows,
                           v=dict(request.args), sql_info="JOIN + LEFT JOIN + GROUP BY + HAVING")


@app.route("/consulta/participacao")
@login_required
def consulta_participacao():
    tipo, inst = nulo(request.args.get("tipo")), nulo(request.args.get("instituicao"))
    minimo = nulo(request.args.get("minimo")) or "0"
    rows = None
    if request.args:
        rows = consultar(cn(), """
            SELECT COALESCE(i.sigla, '(sem instituição)') AS instituicao, pa.tipo_participante AS tipo,
                   COUNT(DISTINCT pa.id_pessoa) AS participantes,
                   COUNT(ia.id_atividade)       AS inscricoes_ativas
            FROM participante pa
            LEFT JOIN instituicao i ON i.id_instituicao = pa.id_instituicao_origem
            LEFT JOIN inscricao_atividade ia ON ia.id_participante = pa.id_pessoa AND ia.status_inscricao <> 'CANCELADA'
            WHERE (%s IS NULL OR pa.tipo_participante = %s)
              AND (%s IS NULL OR i.sigla LIKE CONCAT('%%', %s, '%%'))
            GROUP BY i.id_instituicao, i.sigla, pa.tipo_participante
            HAVING COUNT(ia.id_atividade) >= %s
            ORDER BY inscricoes_ativas DESC
            LIMIT 200""", (tipo, tipo, inst, inst, minimo))
    campos = [dict(n="tipo", r="Tipo de participante", t="select", opts=["", "ALUNO", "PROFESSOR", "EXTERNO"]),
              dict(n="instituicao", r="Sigla da instituição contém", t="text"),
              dict(n="minimo", r="Mínimo de inscrições", t="number")]
    return render_template("consulta.html", titulo="Participação por instituição", campos=campos, rows=rows,
                           v=dict(request.args), sql_info="LEFT JOIN + GROUP BY + HAVING + LIKE")


# ----------------------------------------------------------------- relatório (view) e telas por perfil
@app.route("/relatorio")
@login_required
def relatorio():
    rows = consultar(cn(), "SELECT * FROM vw_relatorio_eventos ORDER BY data_inicio DESC LIMIT 200")
    return render_template("consulta.html", titulo="Relatório consolidado de eventos", campos=[], rows=rows,
                           v={}, sql_info="alimentado pela view vw_relatorio_eventos")


@app.route("/agenda")
@login_required
def agenda():
    rows = consultar(cn(), "SELECT * FROM vw_agenda_publica ORDER BY inicio LIMIT 200")
    return render_template("consulta.html", titulo="Agenda pública", campos=[], rows=rows, v={},
                           sql_info="view vw_agenda_publica (sem dados pessoais, sem eventos cancelados)")


@app.route("/certificados/validar")
@login_required
def validar_certificado():
    cod = nulo(request.args.get("codigo"))
    rows = consultar(cn(), "SELECT * FROM vw_validacao_certificado WHERE codigo_validacao = %s", (cod,)) if cod else None
    campos = [dict(n="codigo", r="Código de validação", t="text")]
    return render_template("consulta.html", titulo="Validar certificado", campos=campos, rows=rows,
                           v=dict(request.args), sql_info="view vw_validacao_certificado (titular mascarado)")


@app.route("/auditoria")
@login_required
def auditoria():
    rows = consultar(cn(), "SELECT id_auditoria, tabela_afetada, chave_registro, autor, data_hora, "
                           "valor_anterior, valor_posterior FROM auditoria ORDER BY id_auditoria DESC LIMIT 100")
    return render_template("consulta.html", titulo="Auditoria (últimas 100)", campos=[], rows=rows, v={},
                           sql_info="tabela auditoria, preenchida pelos gatilhos")


# ----------------------------------------------------------------- operações transacionais (B1/B3)
class FalhaSimulada(Exception):
    pass


@app.route("/operacoes/inscrever", methods=["GET", "POST"])
@login_required
def op_inscrever():
    """Inscrição com controle de vagas. FOR UPDATE trava a atividade: duas inscrições simultâneas
    não ultrapassam o limite. 'pausa' segura o bloqueio para o experimento de concorrência (B3)."""
    msg = None
    if request.method == "POST":
        try:
            part, ativ = int(request.form["id_participante"]), int(request.form["id_atividade"])
            pausa = min(max(int(request.form.get("pausa") or 0), 0), 30)
        except ValueError:
            flash("Informe números válidos.", "erro")
            return redirect(url_for("op_inscrever"))
        simular = request.form.get("simular_falha") == "on"
        c = cn()
        try:
            c.start_transaction()  # BEGIN explícito
            at = consultar(c, "SELECT vagas FROM atividade WHERE id_atividade = %s FOR UPDATE", (ativ,))
            if not at:
                c.rollback()
                flash("Atividade não encontrada.", "erro")
                return redirect(url_for("op_inscrever"))
            if pausa:
                consultar(c, "SELECT SLEEP(%s) AS s", (pausa,))
            conf = consultar(c, "SELECT COUNT(*) AS n FROM inscricao_atividade "
                                "WHERE id_atividade = %s AND status_inscricao = 'CONFIRMADA'", (ativ,))[0]["n"]
            status = "CONFIRMADA" if conf < at[0]["vagas"] else "LISTA_ESPERA"
            if status == "CONFIRMADA":  # RN22: sem inscrições CONFIRMADAS em sessões com horários sobrepostos
                if consultar(c, """SELECT 1 AS x FROM sessao_atividade novo
                                  JOIN sessao_atividade velho ON velho.id_atividade <> novo.id_atividade
                                       AND velho.inicio < novo.fim AND velho.fim > novo.inicio
                                  JOIN inscricao_atividade ia ON ia.id_atividade = velho.id_atividade
                                       AND ia.id_participante = %s AND ia.status_inscricao = 'CONFIRMADA'
                                  WHERE novo.id_atividade = %s LIMIT 1""", (part, ativ)):
                    c.rollback()
                    flash("RN22: o participante já tem inscrição CONFIRMADA em horário sobreposto.", "erro")
                    return redirect(url_for("op_inscrever"))
            executar(c, "INSERT INTO inscricao_atividade (id_participante, id_atividade, data_inscricao, status_inscricao) "
                        "VALUES (%s, %s, NOW(), %s)", (part, ativ, status))
            if simular:
                raise FalhaSimulada()
            c.commit()  # COMMIT
            flash(f"Inscrição registrada como {status} ({conf + (status == 'CONFIRMADA')}/{at[0]['vagas']} vagas).", "ok")
        except FalhaSimulada:
            c.rollback()  # ROLLBACK
            flash("Falha simulada no meio da transação: ROLLBACK executado, nada foi gravado.", "erro")
        except mysql.connector.Error as ex:
            c.rollback()
            flash(mensagem_erro(ex), "erro")
        return redirect(url_for("op_inscrever"))
    return render_template("operacao.html", titulo="Inscrever participante em atividade", acao=url_for("op_inscrever"),
                           campos=[dict(n="id_participante", r="ID do participante", t="number"),
                                   dict(n="id_atividade", r="ID da atividade", t="number"),
                                   dict(n="pausa", r="Segurar o bloqueio por N segundos (experimento de concorrência)", t="number")],
                           info="Tabelas: atividade (trava), inscricao_atividade (insere).")


@app.route("/operacoes/encerrar-evento", methods=["GET", "POST"])
@login_required
def op_encerrar():
    """Operação central do B1: em UMA transação, muda o status do evento (historico_status_evento)
    e emite certificados (certificado). Se qualquer passo falhar, nada fica gravado."""
    if request.method == "POST":
        try:
            ev, minimo = int(request.form["id_evento"]), Decimal(request.form.get("minimo") or "75")
        except (ValueError, InvalidOperation):
            flash("Informe números válidos.", "erro")
            return redirect(url_for("op_encerrar"))
        simular = request.form.get("simular_falha") == "on"
        c = cn()
        try:
            c.start_transaction()
            if not consultar(c, "SELECT 1 AS x FROM evento WHERE id_evento = %s FOR UPDATE", (ev,)):
                c.rollback()
                flash("Evento não encontrado.", "erro")
                return redirect(url_for("op_encerrar"))
            st = consultar(c, "SELECT status_atual FROM vw_evento_status_atual WHERE id_evento = %s", (ev,))
            if st and st[0]["status_atual"] in ("CANCELADO", "ENCERRADO"):
                c.rollback()
                flash(f"Evento {st[0]['status_atual'].lower()} não pode ser encerrado novamente.", "erro")
                return redirect(url_for("op_encerrar"))
            executar(c, "INSERT INTO historico_status_evento (id_evento, sequencia, status, data_hora, observacao) "
                        "SELECT %s, COALESCE(MAX(sequencia), 0) + 1, 'ENCERRADO', NOW(), 'Encerrado pela aplicação' "
                        "FROM historico_status_evento WHERE id_evento = %s", (ev, ev))
            n, _ = executar(c, """
                INSERT INTO certificado (id_participante, id_evento, codigo_validacao, emitido_em, carga_horaria)
                SELECT ia.id_participante, a.id_evento,
                       CONCAT('CERT-', a.id_evento, '-', ia.id_participante, '-', UPPER(SUBSTRING(UUID(), 1, 8))),
                       NOW(), SUM(a.carga_horaria)
                FROM inscricao_atividade ia
                JOIN atividade a ON a.id_atividade = ia.id_atividade
                WHERE a.id_evento = %s AND ia.status_inscricao = 'CONFIRMADA'
                GROUP BY ia.id_participante, a.id_evento
                HAVING COUNT(ia.percentual_presenca) = COUNT(*)      -- presença registrada em TODAS as atividades confirmadas
                   AND AVG(ia.percentual_presenca) >= %s""", (ev, minimo))   # RN26: média de presença >= mínimo
            if simular:
                raise FalhaSimulada()
            c.commit()
            flash(f"Evento encerrado e {n} certificado(s) emitido(s).", "ok")
        except FalhaSimulada:
            c.rollback()
            flash("Falha simulada depois de gravar o status e os certificados: ROLLBACK executado, banco íntegro.", "erro")
        except mysql.connector.Error as ex:
            c.rollback()  # ex.: certificados já emitidos (uq_certificado_participante_evento) desfaz também o status
            flash(mensagem_erro(ex), "erro")
        return redirect(url_for("op_encerrar"))
    return render_template("operacao.html", titulo="Encerrar evento e emitir certificados", acao=url_for("op_encerrar"),
                           campos=[dict(n="id_evento", r="ID do evento", t="number"),
                                   dict(n="minimo", r="Presença mínima (%)", t="number")],
                           info="Tabelas alteradas na mesma transação: historico_status_evento e certificado.")


if __name__ == "__main__":
    app.run(debug=False, port=5000)
