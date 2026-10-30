-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados
-- Arquivo: 10_verificacao_regras.sql  (rastreabilidade das RN atendidas "por consulta")
-- Cada consulta lista as LINHAS QUE VIOLAM a regra: resultado vazio = regra respeitada.
-- Pré-requisito: 01_ddl.sql, 02_carga.sql e 04_views.sql (usa vw_evento_status_atual).
-- =============================================================
USE eventos_academicos;

-- RN06 (complemento do CHECK): categoria em ciclo na hierarquia (A -> B -> A). O CHECK só barra "pai de si própria".
WITH RECURSIVE cadeia AS (
  SELECT id_categoria AS origem, id_categoria_pai AS atual, 1 AS nivel FROM categoria_evento WHERE id_categoria_pai IS NOT NULL
  UNION ALL
  SELECT c.origem, e.id_categoria_pai, c.nivel + 1 FROM cadeia c JOIN categoria_evento e ON e.id_categoria = c.atual
  WHERE e.id_categoria_pai IS NOT NULL AND c.nivel < 50)
SELECT DISTINCT origem AS rn06_categoria_em_ciclo FROM cadeia WHERE atual = origem;

-- RN12: evento sem nenhum registro de histórico (não tem "status atual").
SELECT e.id_evento, e.titulo AS rn12_evento_sem_historico
FROM evento e LEFT JOIN historico_status_evento h ON h.id_evento = e.id_evento
WHERE h.id_evento IS NULL;

-- RN15: evento ABERTO para inscrições sem nenhuma atividade cadastrada.
SELECT e.id_evento, e.titulo AS rn15_evento_aberto_sem_atividade
FROM evento e JOIN vw_evento_status_atual s ON s.id_evento = e.id_evento AND s.status_atual = 'ABERTO'
LEFT JOIN atividade a ON a.id_evento = e.id_evento
WHERE a.id_atividade IS NULL;

-- RN18: atividade com mais vagas do que a capacidade de alguma sala usada em suas sessões.
SELECT a.id_atividade, a.titulo, a.vagas, sa.nome AS sala, sa.bloco, sa.capacidade AS rn18_vagas_acima_da_sala
FROM atividade a
JOIN sessao_atividade s ON s.id_atividade = a.id_atividade
JOIN sala sa ON sa.id_sala = s.id_sala
WHERE a.vagas > sa.capacidade;

-- RN22: participante com duas inscrições CONFIRMADAS em sessões de horários sobrepostos.
SELECT DISTINCT ia1.id_participante, ia1.id_atividade AS atividade_a, ia2.id_atividade AS atividade_b
FROM inscricao_atividade ia1
JOIN inscricao_atividade ia2 ON ia2.id_participante = ia1.id_participante AND ia2.id_atividade > ia1.id_atividade
     AND ia1.status_inscricao = 'CONFIRMADA' AND ia2.status_inscricao = 'CONFIRMADA'
JOIN sessao_atividade s1 ON s1.id_atividade = ia1.id_atividade
JOIN sessao_atividade s2 ON s2.id_atividade = ia2.id_atividade AND s1.inicio < s2.fim AND s1.fim > s2.inicio;

-- RN24: evento sem organizador marcado como responsável principal.
SELECT e.id_evento, e.titulo AS rn24_evento_sem_responsavel_principal
FROM evento e
WHERE NOT EXISTS (SELECT 1 FROM organizacao_evento o WHERE o.id_evento = e.id_evento AND o.responsavel_principal = TRUE);

-- RN26: certificado emitido com evento não encerrado ou com média de presença abaixo de 75% nas atividades confirmadas.
SELECT c.id_certificado, c.id_participante, c.id_evento, st.status_atual, ROUND(AVG(ia.percentual_presenca), 1) AS rn26_media_presenca
FROM certificado c
LEFT JOIN vw_evento_status_atual st ON st.id_evento = c.id_evento
LEFT JOIN atividade a ON a.id_evento = c.id_evento
LEFT JOIN inscricao_atividade ia ON ia.id_atividade = a.id_atividade AND ia.id_participante = c.id_participante
     AND ia.status_inscricao = 'CONFIRMADA'
GROUP BY c.id_certificado, c.id_participante, c.id_evento, st.status_atual
HAVING st.status_atual IS NULL OR st.status_atual <> 'ENCERRADO'
    OR AVG(ia.percentual_presenca) IS NULL OR AVG(ia.percentual_presenca) < 75;
