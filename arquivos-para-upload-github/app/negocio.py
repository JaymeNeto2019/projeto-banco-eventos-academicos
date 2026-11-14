"""Regras transacionais compartilhadas pelas operações da aplicação."""
from db import consultar, executar


class RegraNegocio(ValueError):
    pass


def travar_evento(c, evento):
    rows = consultar(c, 'SELECT *, data_inicio > NOW() AS aceita_inscricao FROM evento WHERE id_evento=%s FOR UPDATE', (evento,))
    if not rows:
        raise RegraNegocio('Evento não encontrado.')
    st = consultar(c, 'SELECT status FROM historico_status_evento WHERE id_evento=%s ORDER BY sequencia DESC LIMIT 1', (evento,))
    return rows[0], st[0]['status'] if st else None


def inscrever(c, participante, atividade, pausa=0):
    """Ordem de bloqueios: evento, participante e atividade. O chamador confirma/desfaz."""
    rows = consultar(c, 'SELECT id_evento FROM atividade WHERE id_atividade=%s', (atividade,))
    if not rows:
        raise RegraNegocio('Atividade não encontrada.')
    evento = rows[0]['id_evento']
    ev, estado = travar_evento(c, evento)
    if estado != 'ABERTO' or not ev['aceita_inscricao']:
        raise RegraNegocio('Inscrições disponíveis somente em evento ABERTO e antes do seu início.')
    if not consultar(c, 'SELECT id_pessoa FROM participante WHERE id_pessoa=%s FOR UPDATE', (participante,)):
        raise RegraNegocio('Participante não encontrado.')
    at = consultar(c, 'SELECT id_evento, vagas FROM atividade WHERE id_atividade=%s FOR UPDATE', (atividade,))
    if not at or at[0]['id_evento'] != evento:
        raise RegraNegocio('A atividade mudou. Atualize a página e tente novamente.')
    if pausa:
        consultar(c, 'SELECT SLEEP(%s) AS s', (pausa,))
    if consultar(c, 'SELECT 1 FROM inscricao_atividade WHERE id_participante=%s AND id_atividade=%s', (participante, atividade)):
        raise RegraNegocio('Já existe uma inscrição deste participante nesta atividade.')
    conf = consultar(c, "SELECT COUNT(*) AS n FROM inscricao_atividade WHERE id_atividade=%s AND status_inscricao='CONFIRMADA'", (atividade,))[0]['n']
    status = 'CONFIRMADA' if conf < at[0]['vagas'] else 'LISTA_ESPERA'
    if status == 'CONFIRMADA' and ev['limite_participantes'] is not None:
        limite = consultar(c, """SELECT COUNT(DISTINCT ia.id_participante) AS total,
                COALESCE(MAX(ia.id_participante=%s),0) AS ja_participa
            FROM inscricao_atividade ia JOIN atividade a USING(id_atividade)
            WHERE a.id_evento=%s AND ia.status_inscricao='CONFIRMADA'""", (participante, evento))[0]
        if not limite['ja_participa'] and limite['total'] >= ev['limite_participantes']:
            status = 'LISTA_ESPERA'
    if status == 'CONFIRMADA' and consultar(c, """SELECT 1 FROM sessao_atividade novo
            JOIN sessao_atividade velho ON velho.id_atividade <> novo.id_atividade
                AND velho.inicio < novo.fim AND velho.fim > novo.inicio
            JOIN inscricao_atividade ia ON ia.id_atividade=velho.id_atividade
                AND ia.id_participante=%s AND ia.status_inscricao='CONFIRMADA'
            WHERE novo.id_atividade=%s LIMIT 1""", (participante, atividade)):
        raise RegraNegocio('RN22: o participante já tem inscrição CONFIRMADA em horário sobreposto.')
    executar(c, 'INSERT INTO inscricao_atividade (id_participante,id_atividade,data_inscricao,status_inscricao) VALUES (%s,%s,NOW(),%s)',
             (participante, atividade, status))
    return status


def validar_edicao(c, nome, pk, dados):
    if nome == 'atividade':
        # Bloqueia primeiro o evento de destino, compartilhado com inscrições/encerramento.
        _, estado = travar_evento(c, dados['id_evento'])
        if estado in ('ENCERRADO', 'CANCELADO'):
            raise RegraNegocio('Não é possível alterar atividades de evento encerrado ou cancelado.')
        if consultar(c, 'SELECT 1 FROM certificado WHERE id_evento=%s LIMIT 1', (dados['id_evento'],)):
            raise RegraNegocio('Não é possível alterar atividades de evento que já possui certificados.')
        if pk is not None:
            atual = consultar(c, 'SELECT id_evento FROM atividade WHERE id_atividade=%s FOR UPDATE', (pk,))
            if not atual:
                raise RegraNegocio('Atividade não encontrada.')
            if str(atual[0]['id_evento']) != str(dados['id_evento']):
                raise RegraNegocio('O evento de uma atividade existente não pode ser alterado.')
            salas = consultar(c, 'SELECT sa.capacidade FROM sessao_atividade s JOIN sala sa USING(id_sala) WHERE s.id_atividade=%s FOR UPDATE', (pk,))
            if any(dados['vagas'] > sala['capacidade'] for sala in salas):
                raise RegraNegocio('RN18: as vagas não podem superar a capacidade das salas da atividade.')
            total = consultar(c, "SELECT COUNT(*) AS n FROM inscricao_atividade WHERE id_atividade=%s AND status_inscricao='CONFIRMADA'", (pk,))[0]['n']
            if dados['vagas'] < total:
                raise RegraNegocio('As vagas não podem ficar abaixo das inscrições confirmadas.')
    elif nome == 'sala' and pk is not None:
        consultar(c, 'SELECT id_sala FROM sala WHERE id_sala=%s FOR UPDATE', (pk,))
        atividades = consultar(c, 'SELECT a.vagas FROM sessao_atividade s JOIN atividade a USING(id_atividade) WHERE s.id_sala=%s FOR UPDATE', (pk,))
        if any(dados['capacidade'] < a['vagas'] for a in atividades):
            raise RegraNegocio('RN18: a capacidade não pode ficar abaixo das vagas das atividades agendadas.')
    elif nome == 'evento':
        if pk is not None:
            travar_evento(c, pk)
            total = consultar(c, "SELECT COUNT(DISTINCT ia.id_participante) AS n FROM inscricao_atividade ia JOIN atividade a USING(id_atividade) WHERE a.id_evento=%s AND ia.status_inscricao='CONFIRMADA'", (pk,))[0]['n']
            if dados['limite_participantes'] is not None and dados['limite_participantes'] < total:
                raise RegraNegocio('O limite do evento não pode ficar abaixo dos participantes confirmados.')
        if not consultar(c, 'SELECT id_pessoa FROM organizador WHERE id_pessoa=%s AND ativo=TRUE FOR UPDATE', (dados['id_responsavel'],)):
            raise RegraNegocio('Escolha um organizador ativo como responsável principal.')


def salvar_responsavel(c, evento, organizador):
    executar(c, 'UPDATE organizacao_evento SET responsavel_principal=FALSE WHERE id_evento=%s', (evento,))
    executar(c, """INSERT INTO organizacao_evento (id_organizador,id_evento,papel,data_inicio_atuacao,responsavel_principal)
        VALUES (%s,%s,'Responsável principal',CURRENT_DATE,TRUE)
        ON DUPLICATE KEY UPDATE responsavel_principal=TRUE""", (organizador, evento))
