-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 2
-- Arquivo: 07_estudo_indices.sql  (B4 - Otimização de consultas)
-- Pré-requisito: 01_ddl.sql, 02_carga.sql e 08_carga_volume.sql (para ter volume).
-- Para CADA estudo: EXPLAIN ANALYZE antes -> CREATE INDEX -> EXPLAIN ANALYZE depois.
-- EXPLAIN ANALYZE (MySQL 8.0.18+) executa a consulta e mostra o TEMPO REAL medido.
-- Copie a saída de cada passo para o relatório e escreva a leitura do plano em texto.
-- Rode cada bloco 3 vezes e use a mediana (a 1ª execução esquenta o cache).
-- Os índices abaixo NÃO existem no 01_ddl.sql de propósito (senão não haveria "antes").
-- =============================================================
USE eventos_academicos;

-- Garantia de reexecução: remove os índices do estudo se já existirem (ignore o erro 1091 na 1ª vez).
-- DROP INDEX idx_inscricao_data       ON inscricao_atividade;
-- DROP INDEX idx_pessoa_nome          ON pessoa;
-- DROP INDEX idx_sessao_sala_inicio   ON sessao_atividade;

-- ============ ESTUDO 1: inscrições em um intervalo de datas ============
-- Pergunta de negócio: quantas inscrições por status foram feitas no 1º semestre de 2025?
-- Hipótese: sem índice em data_inscricao o MySQL lê a tabela inteira (type=ALL).
EXPLAIN ANALYZE
SELECT status_inscricao, COUNT(*) AS total
FROM inscricao_atividade
WHERE data_inscricao BETWEEN '2025-01-01' AND '2025-06-30 23:59:59'
GROUP BY status_inscricao;

CREATE INDEX idx_inscricao_data ON inscricao_atividade (data_inscricao, status_inscricao);
-- Por que estas colunas e nesta ordem: o filtro é um INTERVALO em data_inscricao, então ela vem
-- primeiro; status_inscricao vem depois para o índice ser "de cobertura" (a consulta é respondida
-- só com o índice, sem ir à tabela). Com a ordem inversa, o intervalo não conseguiria usar o índice.
EXPLAIN ANALYZE
SELECT status_inscricao, COUNT(*) AS total
FROM inscricao_atividade
WHERE data_inscricao BETWEEN '2025-01-01' AND '2025-06-30 23:59:59'
GROUP BY status_inscricao;

-- ============ ESTUDO 2: busca de pessoa pelo início do nome ============
-- Pergunta de negócio: a secretaria digita "Ana S" e quer achar a pessoa.
-- Hipótese: LIKE com prefixo fixo ('Ana S%') consegue usar índice; LIKE '%Ana' NÃO consegue.
EXPLAIN ANALYZE SELECT id_pessoa, nome, email FROM pessoa WHERE nome LIKE 'Ana S%';

CREATE INDEX idx_pessoa_nome ON pessoa (nome);
EXPLAIN ANALYZE SELECT id_pessoa, nome, email FROM pessoa WHERE nome LIKE 'Ana S%';
-- Contraexemplo para a discussão honesta (o índice NÃO ajuda quando o curinga vem antes):
EXPLAIN ANALYZE SELECT id_pessoa, nome FROM pessoa WHERE nome LIKE '%Souza%';

-- ============ ESTUDO 3: sessões de uma sala em um período (possível resultado NEGATIVO) ============
-- Pergunta de negócio: a sala 1 está livre no 2º semestre de 2025? (detecção de conflito de horário)
-- O 01_ddl.sql já tem índice em id_sala (criado pela chave estrangeira). O composto (id_sala, inicio)
-- melhora ou não? Meça e relate honestamente, mesmo que o ganho seja pequeno.
EXPLAIN ANALYZE
SELECT id_atividade, numero_sessao, inicio, fim
FROM sessao_atividade
WHERE id_sala = 1 AND inicio BETWEEN '2025-07-01' AND '2025-12-31 23:59:59'
ORDER BY inicio;

CREATE INDEX idx_sessao_sala_inicio ON sessao_atividade (id_sala, inicio);
-- Ordem: igualdade (id_sala) primeiro, intervalo/ordenação (inicio) depois: o índice já entrega
-- as linhas ordenadas e elimina o passo de "filesort".
EXPLAIN ANALYZE
SELECT id_atividade, numero_sessao, inicio, fim
FROM sessao_atividade
WHERE id_sala = 1 AND inicio BETWEEN '2025-07-01' AND '2025-12-31 23:59:59'
ORDER BY inicio;

-- ============ Para o relatório, anote em cada estudo ============
-- 1) tipo de acesso antes/depois (ALL -> range/ref), 2) linhas estimadas e lidas,
-- 3) tempo real "actual time" antes/depois, 4) volume (SELECT COUNT(*) da tabela),
-- 5) custo do índice: INSERT/UPDATE ficam um pouco mais lentos e o índice ocupa espaço
--    (SELECT index_length FROM information_schema.tables WHERE table_name='...').
