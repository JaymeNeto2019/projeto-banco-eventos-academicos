-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 1
-- Tema: Sistema de Gestão de Eventos Acadêmicos
-- Arquivo: 03_consultas.sql
-- 5 básicas + 5 com junção/agregação + 5 avançadas
-- =============================================================

USE eventos_academicos;

-- =============================================================
-- CONSULTAS BÁSICAS (5)
-- =============================================================

-- Q01 - Pergunta de negócio: quais eventos começam entre 25/09/2026 e 31/12/2026,
-- e em que ordem ocorrerão?
SELECT id_evento, titulo, data_inicio, data_fim, modalidade
FROM evento
WHERE data_inicio BETWEEN '2026-09-25 00:00:00' AND '2026-12-31 23:59:59'
ORDER BY data_inicio, titulo;

-- Q02 - Pergunta de negócio: quais pessoas possuem "Ana" em qualquer parte do nome?
SELECT id_pessoa, nome, email
FROM pessoa
WHERE nome LIKE '%Ana%'
ORDER BY nome;

-- Q03 - Pergunta de negócio: quais salas dos blocos A ou B possuem capacidade de pelo menos 80 pessoas?
SELECT id_sala, nome, bloco, capacidade, acessivel
FROM sala
WHERE bloco IN ('Bloco A','Bloco B')
  AND capacidade >= 80
ORDER BY capacidade DESC, nome;

-- Q04 - Pergunta de negócio: quais eventos ainda não possuem URL pública cadastrada?
SELECT id_evento, titulo, modalidade, url_evento
FROM evento
WHERE url_evento IS NULL
ORDER BY id_evento;

-- Q05 - Pergunta de negócio: quais inscrições estão em lista de espera ou foram canceladas?
SELECT id_participante, id_atividade, data_inscricao, status_inscricao
FROM inscricao_atividade
WHERE status_inscricao IN ('LISTA_ESPERA','CANCELADA')
ORDER BY data_inscricao DESC;

-- =============================================================
-- JUNÇÕES E AGREGAÇÃO (5)
-- =============================================================

-- Q06 - Pergunta de negócio: quais eventos possuem pelo menos duas atividades cadastradas?
-- Usa EVENTO + ATIVIDADE, GROUP BY e HAVING.
SELECT e.id_evento, e.titulo, COUNT(a.id_atividade) AS qtd_atividades
FROM evento e
JOIN atividade a ON a.id_evento = e.id_evento
GROUP BY e.id_evento, e.titulo
HAVING COUNT(a.id_atividade) >= 2
ORDER BY qtd_atividades DESC, e.titulo;

-- Q07 - Pergunta de negócio: quais participantes estão cadastrados e quantas inscrições possuem,
-- inclusive participantes sem inscrição? Usa LEFT JOIN.
SELECT p.id_pessoa, pe.nome, COUNT(ia.id_atividade) AS qtd_inscricoes
FROM participante p
JOIN pessoa pe ON pe.id_pessoa = p.id_pessoa
LEFT JOIN inscricao_atividade ia ON ia.id_participante = p.id_pessoa
GROUP BY p.id_pessoa, pe.nome
ORDER BY qtd_inscricoes DESC, pe.nome;

-- Q08 - Pergunta de negócio: em quais salas e horários ocorrerão as sessões de cada evento?
-- Usa mais de três tabelas.
SELECT e.titulo AS evento, a.titulo AS atividade,
       sa.numero_sessao, s.nome AS sala, s.bloco,
       sa.inicio, sa.fim
FROM evento e
JOIN atividade a ON a.id_evento = e.id_evento
JOIN sessao_atividade sa ON sa.id_atividade = a.id_atividade
JOIN sala s ON s.id_sala = sa.id_sala
ORDER BY e.data_inicio, a.id_atividade, sa.numero_sessao;

-- Q09 - Pergunta de negócio: quais atividades confirmadas apresentam presença média de pelo menos 75%?
SELECT a.id_atividade, a.titulo,
       COUNT(ia.id_participante) AS confirmados_com_presenca,
       ROUND(AVG(ia.percentual_presenca),2) AS media_presenca
FROM atividade a
JOIN inscricao_atividade ia ON ia.id_atividade = a.id_atividade
WHERE ia.status_inscricao = 'CONFIRMADA'
  AND ia.percentual_presenca IS NOT NULL
GROUP BY a.id_atividade, a.titulo
HAVING AVG(ia.percentual_presenca) >= 75
ORDER BY media_presenca DESC, a.titulo;

-- Q10 - Pergunta de negócio: quantos eventos cada organizador integra e em quantos é responsável principal?
SELECT o.id_pessoa, p.nome,
       COUNT(oe.id_evento) AS qtd_eventos,
       SUM(CASE WHEN oe.responsavel_principal = TRUE THEN 1 ELSE 0 END) AS qtd_como_principal
FROM organizador o
JOIN pessoa p ON p.id_pessoa = o.id_pessoa
LEFT JOIN organizacao_evento oe ON oe.id_organizador = o.id_pessoa
GROUP BY o.id_pessoa, p.nome
ORDER BY qtd_como_principal DESC, qtd_eventos DESC, p.nome;

-- =============================================================
-- CONSULTAS AVANÇADAS (5)
-- =============================================================

-- Q11 - Pergunta de negócio: quais atividades têm mais inscrições que a média das atividades do mesmo evento?
-- Subconsulta correlacionada.
SELECT a.id_atividade, a.id_evento, a.titulo,
       (SELECT COUNT(*)
          FROM inscricao_atividade ia
         WHERE ia.id_atividade = a.id_atividade) AS total_inscricoes
FROM atividade a
WHERE (SELECT COUNT(*)
         FROM inscricao_atividade ia
        WHERE ia.id_atividade = a.id_atividade)
      >
      (SELECT AVG(contagem)
         FROM (
              SELECT a2.id_evento, a2.id_atividade, COUNT(ia2.id_participante) AS contagem
              FROM atividade a2
              LEFT JOIN inscricao_atividade ia2 ON ia2.id_atividade = a2.id_atividade
              GROUP BY a2.id_evento, a2.id_atividade
         ) medias
        WHERE medias.id_evento = a.id_evento)
ORDER BY a.id_evento, total_inscricoes DESC;

-- Q12 - Pergunta de negócio: quais participantes possuem ao menos uma inscrição em atividade
-- de evento da categoria Computação? Usa EXISTS.
SELECT p.id_pessoa, pe.nome, pe.email
FROM participante p
JOIN pessoa pe ON pe.id_pessoa = p.id_pessoa
WHERE EXISTS (
    SELECT 1
    FROM inscricao_atividade ia
    JOIN atividade a ON a.id_atividade = ia.id_atividade
    JOIN evento e ON e.id_evento = a.id_evento
    JOIN categoria_evento c ON c.id_categoria = e.id_categoria
    WHERE ia.id_participante = p.id_pessoa
      AND c.nome = 'Computação'
)
ORDER BY pe.nome;

-- Q13 - Pergunta de negócio: qual é o status atual de cada evento, obtido do registro histórico mais recente?
WITH status_ordenado AS (
    SELECT h.*,
           ROW_NUMBER() OVER (
              PARTITION BY h.id_evento
              ORDER BY h.data_hora DESC, h.sequencia DESC
           ) AS rn
    FROM historico_status_evento h
)
SELECT e.id_evento, e.titulo, so.status AS status_atual, so.data_hora AS atualizado_em
FROM evento e
JOIN status_ordenado so ON so.id_evento = e.id_evento AND so.rn = 1
ORDER BY e.id_evento;

-- Q14 - Pergunta de negócio: quais atividades violariam a RN18 porque têm mais vagas
-- do que a capacidade de alguma sala usada por suas sessões?
SELECT DISTINCT a.id_atividade, a.titulo, a.vagas,
       s.id_sala, s.nome AS sala, s.capacidade
FROM atividade a
JOIN sessao_atividade sa ON sa.id_atividade = a.id_atividade
JOIN sala s ON s.id_sala = sa.id_sala
WHERE a.vagas > s.capacidade
ORDER BY a.id_atividade, s.capacidade;

-- Q15 - Pergunta de negócio não trivial: quais participantes estariam elegíveis a certificado
-- em eventos encerrados segundo a RN26 e ainda não possuem certificado emitido?
WITH status_atual AS (
    SELECT id_evento, status
    FROM (
        SELECT h.id_evento, h.status,
               ROW_NUMBER() OVER (
                   PARTITION BY h.id_evento
                   ORDER BY h.data_hora DESC, h.sequencia DESC
               ) AS rn
        FROM historico_status_evento h
    ) x
    WHERE rn = 1
), presenca_evento AS (
    SELECT ia.id_participante, a.id_evento,
           AVG(ia.percentual_presenca) AS media_presenca,
           COUNT(*) AS qtd_atividades_confirmadas
    FROM inscricao_atividade ia
    JOIN atividade a ON a.id_atividade = ia.id_atividade
    WHERE ia.status_inscricao = 'CONFIRMADA'
      AND ia.percentual_presenca IS NOT NULL
    GROUP BY ia.id_participante, a.id_evento
)
SELECT pe.id_pessoa, pe.nome, e.id_evento, e.titulo,
       ROUND(pr.media_presenca,2) AS media_presenca
FROM presenca_evento pr
JOIN status_atual sa ON sa.id_evento = pr.id_evento AND sa.status = 'ENCERRADO'
JOIN participante p ON p.id_pessoa = pr.id_participante
JOIN pessoa pe ON pe.id_pessoa = p.id_pessoa
JOIN evento e ON e.id_evento = pr.id_evento
LEFT JOIN certificado c
       ON c.id_participante = pr.id_participante
      AND c.id_evento = pr.id_evento
WHERE pr.media_presenca >= 75
  AND c.id_certificado IS NULL
ORDER BY pr.media_presenca DESC, pe.nome;
