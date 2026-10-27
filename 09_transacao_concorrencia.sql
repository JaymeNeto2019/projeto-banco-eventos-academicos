-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 2
-- Arquivo: 09_transacao_concorrencia.sql  (B3 - roteiro manual para duas sessões)
-- NÃO é para executar de uma vez: abra DOIS terminais (sessão A e sessão B) e rode os
-- comandos na ordem indicada, copiando a saída para o relatório. Troque os IDs por reais.
-- =============================================================

-- ---------- PARTE 1: transação multitabela (COMMIT) e falha provocada (ROLLBACK) ----------
-- (a aplicação faz isto em /operacoes/encerrar-evento; aqui é a versão "na mão" para mostrar o SQL)
USE eventos_academicos;
SET @ev = 1;                                            -- um evento ABERTO com inscrições presentes

START TRANSACTION;
  INSERT INTO historico_status_evento (id_evento, sequencia, status, data_hora, observacao)
  SELECT @ev, COALESCE(MAX(sequencia),0)+1, 'ENCERRADO', NOW(), 'demo' FROM historico_status_evento WHERE id_evento=@ev;
  SELECT COUNT(*) AS historico_dentro_da_transacao FROM historico_status_evento WHERE id_evento=@ev;
ROLLBACK;                                               -- falha provocada: desfaz
SELECT COUNT(*) AS historico_depois_do_rollback FROM historico_status_evento WHERE id_evento=@ev;  -- igual ao de antes

-- ---------- PARTE 2: nível de isolamento em vigor ----------
SELECT @@transaction_isolation AS isolamento_padrao;     -- no MySQL/InnoDB o padrão é REPEATABLE-READ

-- ---------- PARTE 3: bloqueio (espera) com duas sessões ----------
-- SESSÃO A:
--   START TRANSACTION;
--   SELECT vagas FROM atividade WHERE id_atividade = 1 FOR UPDATE;   -- A trava a linha e NÃO dá commit
-- SESSÃO B (outro terminal):
--   START TRANSACTION;
--   UPDATE atividade SET vagas = vagas + 1 WHERE id_atividade = 1;   -- B fica ESPERANDO (bloqueada)
--   -- anote: quanto tempo esperou; depois de ~50 s (innodb_lock_wait_timeout) ocorre o erro 1205
-- SESSÃO C (opcional, terceiro terminal) para ver quem bloqueia quem:
--   SELECT * FROM performance_schema.data_lock_waits\G
--   SELECT * FROM sys.innodb_lock_waits\G
-- SESSÃO A:  COMMIT;     -- B é liberada e conclui; B então: COMMIT;

-- ---------- PARTE 4: deadlock (duas sessões travando em ordem inversa) ----------
-- SESSÃO A: START TRANSACTION; UPDATE atividade SET vagas = vagas WHERE id_atividade = 1;
-- SESSÃO B: START TRANSACTION; UPDATE atividade SET vagas = vagas WHERE id_atividade = 2;
-- SESSÃO A: UPDATE atividade SET vagas = vagas WHERE id_atividade = 2;   -- A espera por B
-- SESSÃO B: UPDATE atividade SET vagas = vagas WHERE id_atividade = 1;   -- deadlock! o MySQL desfaz uma delas (erro 1213)
--   SHOW ENGINE INNODB STATUS\G     -- seção "LATEST DETECTED DEADLOCK": copie para o relatório
-- Depois: ROLLBACK; nas duas sessões. (Precisa de atividades 1 e 2 existentes.)

-- ---------- PARTE 5: efeito do nível de isolamento (leitura não repetível) ----------
-- SESSÃO A: SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED; START TRANSACTION;
--           SELECT vagas FROM atividade WHERE id_atividade = 1;          -- anote o valor
-- SESSÃO B: UPDATE atividade SET vagas = vagas + 5 WHERE id_atividade = 1;  (autocommit)
-- SESSÃO A: SELECT vagas FROM atividade WHERE id_atividade = 1;          -- READ COMMITTED: VÊ o novo valor
--           ROLLBACK;  e repita tudo com REPEATABLE READ: A continua vendo o valor antigo.
-- Reponha o valor alterado depois do teste (UPDATE atividade SET vagas = vagas - 5 ...).
-- Justificativa sugerida para o relatório: REPEATABLE READ (padrão) + SELECT ... FOR UPDATE nos pontos
-- críticos (controle de vagas) garante que duas inscrições simultâneas não ultrapassem o limite.
