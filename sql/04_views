-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 2
-- Arquivo: 04_views.sql
-- Pré-requisito: 01_ddl.sql (e, para testar com dados, 02_carga.sql)
-- Visões usadas por: B1 (relatório consolidado) e B5 (restrição de acesso)
-- =============================================================
USE eventos_academicos;

-- -------------------------------------------------------------
-- Visão auxiliar: situação ATUAL de cada evento.
-- O histórico (historico_status_evento) guarda vários registros por evento;
-- a situação atual é a de maior "sequencia" (RN12/RN13).
-- -------------------------------------------------------------
CREATE OR REPLACE ALGORITHM=UNDEFINED SQL SECURITY DEFINER
VIEW vw_evento_status_atual AS
SELECT h.id_evento,
       h.status    AS status_atual,
       h.data_hora AS desde
FROM historico_status_evento h
WHERE h.sequencia = (SELECT MAX(h2.sequencia)
                     FROM historico_status_evento h2
                     WHERE h2.id_evento = h.id_evento);

-- -------------------------------------------------------------
-- B1: tela de RELATÓRIO CONSOLIDADO (uma linha por evento).
-- Cada agregação é feita em uma subconsulta própria para evitar
-- multiplicação de linhas entre atividades, inscrições e certificados.
-- -------------------------------------------------------------
CREATE OR REPLACE ALGORITHM=UNDEFINED SQL SECURITY DEFINER
VIEW vw_relatorio_eventos AS
SELECT e.id_evento,
       e.titulo                                   AS evento,
       c.nome                                     AS categoria,
       cp.nome                                    AS categoria_pai,
       i.sigla                                    AS instituicao_promotora,
       e.modalidade,
       e.data_inicio,
       e.data_fim,
       COALESCE(st.status_atual, 'SEM_HISTORICO') AS status_atual,
       COALESCE(a.qtd_atividades, 0)              AS qtd_atividades,
       COALESCE(a.vagas_totais, 0)                AS vagas_totais,
       COALESCE(ins.confirmadas, 0)               AS inscricoes_confirmadas,
       COALESCE(ins.lista_espera, 0)              AS inscricoes_lista_espera,
       COALESCE(ins.canceladas, 0)                AS inscricoes_canceladas,
       ROUND(100 * COALESCE(ins.confirmadas, 0) / NULLIF(a.vagas_totais, 0), 1)
                                                  AS taxa_ocupacao_pct,
       ins.nota_media,
       COALESCE(ce.certificados_emitidos, 0)      AS certificados_emitidos
FROM evento e
JOIN categoria_evento c        ON c.id_categoria   = e.id_categoria
LEFT JOIN categoria_evento cp  ON cp.id_categoria  = c.id_categoria_pai
JOIN instituicao i             ON i.id_instituicao = e.id_instituicao_promotora
LEFT JOIN vw_evento_status_atual st ON st.id_evento = e.id_evento
LEFT JOIN (SELECT id_evento,
                  COUNT(*)    AS qtd_atividades,
                  SUM(vagas)  AS vagas_totais
           FROM atividade
           GROUP BY id_evento) a ON a.id_evento = e.id_evento
LEFT JOIN (SELECT at.id_evento,
                  SUM(ia.status_inscricao = 'CONFIRMADA')   AS confirmadas,
                  SUM(ia.status_inscricao = 'LISTA_ESPERA') AS lista_espera,
                  SUM(ia.status_inscricao = 'CANCELADA')    AS canceladas,
                  ROUND(AVG(ia.nota_avaliacao), 2)          AS nota_media
           FROM inscricao_atividade ia
           JOIN atividade at ON at.id_atividade = ia.id_atividade
           GROUP BY at.id_evento) ins ON ins.id_evento = e.id_evento
LEFT JOIN (SELECT id_evento, COUNT(*) AS certificados_emitidos
           FROM certificado
           GROUP BY id_evento) ce ON ce.id_evento = e.id_evento;

-- -------------------------------------------------------------
-- B5: visão de RESTRIÇÃO para o perfil de consulta pública.
-- Restringe LINHAS (esconde eventos cujo status atual é CANCELADO) e
-- COLUNAS (não expõe e-mail, telefone, nascimento nem dados de inscritos).
-- -------------------------------------------------------------
CREATE OR REPLACE ALGORITHM=UNDEFINED SQL SECURITY DEFINER
VIEW vw_agenda_publica AS
SELECT e.id_evento,
       e.titulo         AS evento,
       e.modalidade,
       a.id_atividade,
       a.titulo         AS atividade,
       a.tipo_atividade,
       a.carga_horaria,
       s.numero_sessao,
       s.inicio,
       s.fim,
       sa.nome          AS sala,
       sa.bloco
FROM evento e
LEFT JOIN vw_evento_status_atual st ON st.id_evento = e.id_evento
JOIN atividade a         ON a.id_evento    = e.id_evento
JOIN sessao_atividade s  ON s.id_atividade = a.id_atividade
JOIN sala sa             ON sa.id_sala     = s.id_sala
WHERE COALESCE(st.status_atual, 'PLANEJADO') <> 'CANCELADO';

-- -------------------------------------------------------------
-- B5: validação pública de certificados.
-- Mascara o nome do titular (ex.: "Maria S.") para reduzir a exposição
-- de dado pessoal; o código de validação é a chave de consulta.
-- -------------------------------------------------------------
CREATE OR REPLACE ALGORITHM=UNDEFINED SQL SECURITY DEFINER
VIEW vw_validacao_certificado AS
SELECT c.codigo_validacao,
       CONCAT(SUBSTRING_INDEX(p.nome, ' ', 1), ' ',
              LEFT(SUBSTRING_INDEX(p.nome, ' ', -1), 1), '.') AS titular_mascarado,
       e.titulo         AS evento,
       c.carga_horaria,
       c.emitido_em
FROM certificado c
JOIN pessoa p ON p.id_pessoa = c.id_participante
JOIN evento e ON e.id_evento = c.id_evento;
