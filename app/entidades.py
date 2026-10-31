"""Configuração dos CRUDs. Nomes de tabela/coluna vêm DESTE arquivo (nunca do usuário);
os VALORES sempre vão como parâmetros."""
def campo(n, r, t="text", req=True, **kw):
    return dict(n=n, r=r, t=t, req=req, **kw)

ENTIDADES = {
    "instituicao": dict(
        titulo="Instituições", pk="id_instituicao", ordem="nome",
        lista=["id_instituicao", "nome", "sigla", "tipo", "cidade", "uf"],
        campos=[campo("nome", "Nome"), campo("sigla", "Sigla"),
                campo("tipo", "Tipo", "select", opts=["PUBLICA", "PRIVADA", "OUTRA"]),
                campo("cidade", "Cidade"), campo("uf", "UF"), campo("site", "Site", req=False)]),
    "sala": dict(
        titulo="Salas", pk="id_sala", ordem="bloco, nome",
        lista=["id_sala", "nome", "bloco", "capacidade", "acessivel"],
        campos=[campo("nome", "Nome"), campo("bloco", "Bloco"),
                campo("capacidade", "Capacidade", "int"), campo("acessivel", "Acessível", "bool", req=False)]),
    "categoria_evento": dict(
        titulo="Categorias de evento", pk="id_categoria", ordem="nome",
        lista=["id_categoria", "nome", "descricao", "id_categoria_pai"],
        campos=[campo("nome", "Nome"), campo("descricao", "Descrição", req=False),
                campo("id_categoria_pai", "Categoria pai", "fk", req=False,
                      q="SELECT id_categoria AS v, nome AS t FROM categoria_evento ORDER BY nome")]),
    "evento": dict(
        titulo="Eventos", pk="id_evento", ordem="data_inicio DESC",
        lista=["id_evento", "titulo", "data_inicio", "data_fim", "modalidade", "gratuito", "valor_inscricao"],
        campos=[campo("id_categoria", "Categoria", "fk",
                      q="SELECT id_categoria AS v, nome AS t FROM categoria_evento ORDER BY nome"),
                campo("id_instituicao_promotora", "Instituição promotora", "fk",
                      q="SELECT id_instituicao AS v, sigla AS t FROM instituicao ORDER BY sigla"),
                campo("titulo", "Título"), campo("descricao", "Descrição", "textarea", req=False),
                campo("data_inicio", "Início", "datetime"), campo("data_fim", "Término", "datetime"),
                campo("modalidade", "Modalidade", "select", opts=["PRESENCIAL", "ONLINE", "HIBRIDO"]),
                campo("limite_participantes", "Limite de participantes", "int", req=False),
                campo("gratuito", "Gratuito", "bool", req=False),
                campo("valor_inscricao", "Valor da inscrição", "dec", padrao="0.00"),
                campo("url_evento", "URL do evento", req=False)]),
    "atividade": dict(
        titulo="Atividades", pk="id_atividade", ordem="id_atividade DESC",
        lista=["id_atividade", "id_evento", "titulo", "tipo_atividade", "carga_horaria", "vagas"],
        campos=[campo("id_evento", "Evento", "fk",
                      q="SELECT id_evento AS v, titulo AS t FROM evento ORDER BY data_inicio DESC LIMIT 500"),
                campo("titulo", "Título"),
                campo("tipo_atividade", "Tipo", "select", opts=["PALESTRA", "MINICURSO", "MESA_REDONDA", "OFICINA"]),
                campo("descricao", "Descrição", "textarea", req=False),
                campo("carga_horaria", "Carga horária (h)", "dec"), campo("vagas", "Vagas", "int"),
                campo("obrigatoria", "Obrigatória", "bool", req=False)]),
}
