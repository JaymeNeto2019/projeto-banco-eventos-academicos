-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 2
-- Arquivo: 08_carga_volume.sql  (apoio ao B4 - estudo de EXPLAIN)
-- Gera dados 100% SINTÉTICOS (nenhuma pessoa real) para dar volume às tabelas.
-- Pré-requisito: 01_ddl.sql + 02_carga.sql (precisa de ao menos 1 categoria,
-- 1 instituição e 1 sala). Não apaga nada: só insere. Todos os registros
-- gerados têm e-mail 'sint<N>@exemplo.test' ou título 'Evento sintético <N>'.
-- Volume: 50.000 pessoas/participantes, 2.000 eventos, 6.000 atividades,
-- 6.000 sessões e 120.000 inscrições. Leva de alguns segundos a poucos minutos.
-- Para remover depois: ver o final deste arquivo.
-- =============================================================
USE eventos_academicos;
SET SESSION cte_max_recursion_depth = 100000;

-- 1) Pessoas e participantes
INSERT INTO pessoa (nome, email, data_nascimento)
WITH RECURSIVE n AS (SELECT 1 AS i UNION ALL SELECT i + 1 FROM n WHERE i < 50000)
SELECT CONCAT(ELT(1 + i % 8, 'Ana','Bruno','Carla','Diego','Elisa','Felipe','Gabriela','Hugo'), ' ',
              ELT(1 + i % 10, 'Silva','Souza','Costa','Lima','Alves','Rocha','Dias','Melo','Nunes','Ramos'), ' ', i),
       CONCAT('sint', i, '@exemplo.test'),
       DATE_ADD('1975-01-01', INTERVAL (i * 7) % 11000 DAY)
FROM n;

INSERT INTO participante (id_pessoa, tipo_participante, matricula_academica)
SELECT id_pessoa,
       ELT(1 + id_pessoa % 3, 'ALUNO', 'PROFESSOR', 'EXTERNO'),
       IF(id_pessoa % 3 = 0, CONCAT('SINT', id_pessoa), NULL)
FROM pessoa WHERE email LIKE 'sint%@exemplo.test';

-- 2) Eventos (categoria e instituição escolhidas entre as existentes)
INSERT INTO evento (id_categoria, id_instituicao_promotora, titulo, data_inicio, data_fim, modalidade, gratuito, valor_inscricao)
WITH RECURSIVE n AS (SELECT 1 AS i UNION ALL SELECT i + 1 FROM n WHERE i < 2000),
     cat AS (SELECT id_categoria, ROW_NUMBER() OVER (ORDER BY id_categoria) AS rn, COUNT(*) OVER () AS tot FROM categoria_evento),
     ins AS (SELECT id_instituicao, ROW_NUMBER() OVER (ORDER BY id_instituicao) AS rn, COUNT(*) OVER () AS tot FROM instituicao)
SELECT cat.id_categoria, ins.id_instituicao, CONCAT('Evento sintético ', n.i),
       DATE_ADD('2024-01-08 08:00:00', INTERVAL (n.i * 13) % 1100 DAY),
       DATE_ADD('2024-01-08 12:00:00', INTERVAL (n.i * 13) % 1100 DAY),
       ELT(1 + n.i % 3, 'PRESENCIAL', 'ONLINE', 'HIBRIDO'), TRUE, 0.00
FROM n JOIN cat ON cat.rn = 1 + (n.i % cat.tot) JOIN ins ON ins.rn = 1 + (n.i % ins.tot);

INSERT INTO historico_status_evento (id_evento, sequencia, status, data_hora)
SELECT id_evento, 1, IF(data_inicio < NOW(), 'ENCERRADO', 'ABERTO'), DATE_SUB(data_inicio, INTERVAL 30 DAY)
FROM evento WHERE titulo LIKE 'Evento sintético %';

-- 3) Atividades (3 por evento) e uma sessão por atividade
INSERT INTO atividade (id_evento, titulo, tipo_atividade, carga_horaria, vagas)
SELECT e.id_evento, CONCAT('Atividade sintética ', k.k, ' do evento ', e.id_evento),
       ELT(1 + (e.id_evento + k.k) % 4, 'PALESTRA', 'MINICURSO', 'MESA_REDONDA', 'OFICINA'), 2.0 * k.k, 20 + 10 * k.k
FROM evento e JOIN (SELECT 1 AS k UNION ALL SELECT 2 UNION ALL SELECT 3) k
WHERE e.titulo LIKE 'Evento sintético %';

INSERT INTO sessao_atividade (id_atividade, numero_sessao, id_sala, inicio, fim)
WITH sal AS (SELECT id_sala, ROW_NUMBER() OVER (ORDER BY id_sala) AS rn, COUNT(*) OVER () AS tot FROM sala)
SELECT a.id_atividade, 1, sal.id_sala, e.data_inicio, DATE_ADD(e.data_inicio, INTERVAL 2 HOUR)
FROM atividade a JOIN evento e ON e.id_evento = a.id_evento
JOIN sal ON sal.rn = 1 + (a.id_atividade % sal.tot)
WHERE a.titulo LIKE 'Atividade sintética %';

-- 4) Inscrições: 20 por atividade sintética (participantes distintos dentro de cada atividade).
-- Tabelas temporárias com chave primária tornam a junção por posição (rn) uma busca direta, não uma varredura.
CREATE TEMPORARY TABLE tmp_pa (rn INT UNSIGNED NOT NULL PRIMARY KEY, id_pessoa BIGINT UNSIGNED NOT NULL);
INSERT INTO tmp_pa
SELECT ROW_NUMBER() OVER (ORDER BY x.id_pessoa), x.id_pessoa
FROM participante x JOIN pessoa p ON p.id_pessoa = x.id_pessoa WHERE p.email LIKE 'sint%@exemplo.test';
SET @tot = (SELECT COUNT(*) FROM tmp_pa);

CREATE TEMPORARY TABLE tmp_at (rn INT UNSIGNED NOT NULL PRIMARY KEY, id_atividade BIGINT UNSIGNED NOT NULL);
INSERT INTO tmp_at
SELECT ROW_NUMBER() OVER (ORDER BY id_atividade), id_atividade FROM atividade WHERE titulo LIKE 'Atividade sintética %';

INSERT INTO inscricao_atividade (id_participante, id_atividade, data_inscricao, status_inscricao, percentual_presenca, nota_avaliacao)
WITH RECURSIVE j AS (SELECT 1 AS j UNION ALL SELECT j + 1 FROM j WHERE j < 20)
SELECT pa.id_pessoa, q.id_atividade,
       DATE_ADD('2024-01-01 09:00:00', INTERVAL (q.arn * 3 + q.j * 17) % 1000 DAY),
       ELT(1 + q.m, 'CONFIRMADA', 'CONFIRMADA', 'CONFIRMADA', 'LISTA_ESPERA', 'CANCELADA'),
       IF(q.m < 3, 50 + (q.arn + q.j) % 51, NULL),
       IF(q.m < 3 AND (q.arn + q.j) % 3 = 0, 5 + (q.arn + q.j) % 6, NULL)
FROM (SELECT t.rn AS arn, t.id_atividade, j.j, (t.rn + j.j) % 5 AS m FROM tmp_at t JOIN j) q
JOIN tmp_pa pa ON pa.rn = 1 + ((q.arn * 37 + q.j * 101) % @tot);

DROP TEMPORARY TABLE tmp_pa;
DROP TEMPORARY TABLE tmp_at;

ANALYZE TABLE pessoa, participante, evento, atividade, sessao_atividade, inscricao_atividade;

SELECT 'pessoa' AS tabela, COUNT(*) AS linhas FROM pessoa UNION ALL SELECT 'evento', COUNT(*) FROM evento
UNION ALL SELECT 'atividade', COUNT(*) FROM atividade UNION ALL SELECT 'inscricao_atividade', COUNT(*) FROM inscricao_atividade;

-- -------------------------------------------------------------
-- LIMPEZA (rode só se quiser remover os dados sintéticos; a ordem importa):
--   DELETE FROM inscricao_atividade WHERE id_atividade IN (SELECT id_atividade FROM atividade WHERE titulo LIKE 'Atividade sintética %');
--   DELETE FROM evento WHERE titulo LIKE 'Evento sintético %';   -- cascata: histórico, atividades e sessões
--   DELETE FROM pessoa WHERE email LIKE 'sint%@exemplo.test';    -- cascata: participante
-- -------------------------------------------------------------
