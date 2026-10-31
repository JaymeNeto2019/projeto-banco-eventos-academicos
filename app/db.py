"""Camada de acesso a dados. Toda consulta usa parâmetros (%s): NUNCA concatene valores no SQL."""
import os, re
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Cada perfil da aplicação usa uma conta MySQL diferente (princípio do menor privilégio).
_CONTAS = {
    "ADMIN": ("DB_USER_ADMIN", "DB_PASS_ADMIN"),
    "ORGANIZADOR": ("DB_USER_ORGANIZADOR", "DB_PASS_ORGANIZADOR"),
    "CONSULTA": ("DB_USER_CONSULTA", "DB_PASS_CONSULTA"),
    "AUTH": ("DB_USER_AUTH", "DB_PASS_AUTH"),
}


def conectar(perfil, usuario_app=None):
    user_k, pass_k = _CONTAS[perfil]
    cn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ[user_k],
        password=os.environ[pass_k],
        database=os.getenv("DB_NAME", "eventos_academicos"),
        autocommit=False,
    )
    if usuario_app:  # lido pelos gatilhos de auditoria (05_triggers.sql)
        cur = cn.cursor()
        cur.execute("SET @usuario_app = %s", (usuario_app,))
        cur.close()
    return cn


def consultar(cn, sql, params=()):
    cur = cn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def executar(cn, sql, params=()):
    cur = cn.cursor()
    try:
        cur.execute(sql, params)
        return cur.rowcount, cur.lastrowid
    finally:
        cur.close()


# ---- Tradução de erros do banco para mensagens compreensíveis -------------
REGRAS = {
    "uq_pessoa_email": "Já existe uma pessoa com este e-mail.",
    "uq_instituicao_sigla": "Já existe uma instituição com esta sigla.",
    "uq_sala_nome_bloco": "Já existe uma sala com este nome neste bloco.",
    "uq_categoria_evento_nome": "Já existe uma categoria com este nome.",
    "uq_participante_matricula": "Esta matrícula já está cadastrada.",
    "uq_certificado_participante_evento": "Este participante já possui certificado deste evento.",
    "uq_certificado_codigo": "Código de certificado repetido.",
    "uq_usuario_app_login": "Este login já está em uso.",
    "ck_evento_periodo": "A data de término deve ser posterior à data de início.",
    "ck_evento_valor": "Evento gratuito deve ter valor 0; evento pago deve ter valor maior que 0.",
    "ck_evento_limite": "O limite de participantes deve ser maior que zero.",
    "ck_evento_modalidade": "Modalidade inválida.",
    "ck_atividade_vagas": "O número de vagas deve ser maior que zero.",
    "ck_atividade_carga": "A carga horária deve ser maior que zero.",
    "ck_sala_capacidade": "A capacidade da sala deve ser maior que zero.",
    "ck_instituicao_tipo": "Tipo de instituição inválido.",
    "fk_evento_categoria": "A categoria informada não existe ou está em uso.",
    "fk_evento_instituicao": "A instituição informada não existe ou está em uso.",
    "fk_atividade_evento": "O evento informado não existe.",
    "fk_inscricao_participante": "O participante informado não existe.",
    "fk_inscricao_atividade": "A atividade informada não existe.",
    "fk_certificado_evento": "Este evento possui certificados emitidos e não pode ser excluído.",
    "fk_certificado_participante": "Este participante possui certificados e não pode ser excluído.",
    "fk_sessao_sala": "Esta sala é usada em sessões de atividades e não pode ser excluída.",
    "fk_categoria_pai": "Esta categoria possui subcategorias ou eventos e não pode ser excluída.",
}


def mensagem_erro(e):
    n = getattr(e, "errno", None)
    txt = str(e)
    m = re.search(r"CONSTRAINT `(\w+)`", txt) or re.search(r"[Cc]heck constraint '(\w+)'", txt) \
        or re.search(r"for key '(?:\w+\.)?(\w+)'", txt)
    regra = m.group(1) if m else None
    if regra in REGRAS:
        return REGRAS[regra]
    padrao = {
        1062: "Já existe um registro com este valor (campo único repetido).",
        1451: "Não é possível excluir: existem registros que dependem deste.",
        1452: "Referência inválida: o registro relacionado não existe.",
        3819: "Algum valor viola uma regra do banco. Revise limites, datas e valores.",
        1048: "Há um campo obrigatório sem preenchimento.",
        1406: "Algum texto é longo demais para o campo.",
        1292: "Há um valor de data ou número inválido.",
        1366: "Há um valor inválido em algum campo.",
        1265: "Há um valor truncado ou inválido.",
        1142: "Seu perfil não tem permissão para esta operação.",
        1143: "Seu perfil não tem permissão para esta operação.",
        1044: "Seu perfil não tem permissão para esta operação.",
        1045: "Não foi possível conectar ao banco (credenciais).",
        2003: "O banco de dados está indisponível no momento.",
        1213: "Conflito de concorrência (deadlock): a operação foi desfeita. Tente novamente.",
        1205: "Tempo de espera por bloqueio excedido. Tente novamente.",
    }
    return padrao.get(n, f"Não foi possível concluir a operação (código {n}).")
