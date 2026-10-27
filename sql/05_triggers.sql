-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 2
-- Arquivo: 05_triggers.sql  (B6 - Gatilhos e auditoria)
-- Pré-requisito: 01_ddl.sql
--
-- O que é auditado e por quê (justificativa pelo domínio):
--  1) inscricao_atividade: status e presença. É a base para emitir
--     certificado; mudar CONFIRMADA -> CANCELADA ou alterar a presença
--     muda quem tem direito ao certificado.
--  2) evento: datas, modalidade, limite e valor. Alterar essas
--     informações depois de abertas as inscrições afeta os inscritos.
--
-- Autor da alteração: a aplicação deve executar, logo após o login e em
-- cada conexão, SET @usuario_app = '<login do usuário da aplicação>';
-- Sem isso, o gatilho grava o usuário do banco (USER()).
-- ATENÇÃO: a variável de sessão pode ser alterada por quem tem acesso ao
-- banco; ela identifica o usuário da aplicação, não é prova criptográfica.
-- =============================================================
USE eventos_academicos;

CREATE TABLE IF NOT EXISTS auditoria (
  id_auditoria     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  tabela_afetada   VARCHAR(64)  NOT NULL,
  operacao         VARCHAR(10)  NOT NULL,
  chave_registro   VARCHAR(100) NOT NULL,
  autor            VARCHAR(120) NOT NULL,
  data_hora        DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  valor_anterior   JSON NULL,
  valor_posterior  JSON NULL,
  CONSTRAINT pk_auditoria PRIMARY KEY (id_auditoria),
  CONSTRAINT ck_auditoria_operacao CHECK (operacao IN ('INSERT','UPDATE','DELETE'))
) ENGINE=InnoDB;

CREATE INDEX idx_auditoria_tabela_data ON auditoria (tabela_afetada, data_hora);

DROP TRIGGER IF EXISTS trg_aud_inscricao_atividade_upd;
DROP TRIGGER IF EXISTS trg_aud_evento_upd;

DELIMITER $$

CREATE TRIGGER trg_aud_inscricao_atividade_upd
AFTER UPDATE ON inscricao_atividade
FOR EACH ROW
BEGIN
  IF NOT (OLD.status_inscricao <=> NEW.status_inscricao)
     OR NOT (OLD.percentual_presenca <=> NEW.percentual_presenca) THEN
    INSERT INTO auditoria
      (tabela_afetada, operacao, chave_registro, autor, valor_anterior, valor_posterior)
    VALUES
      ('inscricao_atividade', 'UPDATE',
       CONCAT('participante=', OLD.id_participante, ';atividade=', OLD.id_atividade),
       COALESCE(@usuario_app, USER()),
       JSON_OBJECT('status_inscricao', OLD.status_inscricao,
                   'percentual_presenca', OLD.percentual_presenca),
       JSON_OBJECT('status_inscricao', NEW.status_inscricao,
                   'percentual_presenca', NEW.percentual_presenca));
  END IF;
END$$

CREATE TRIGGER trg_aud_evento_upd
AFTER UPDATE ON evento
FOR EACH ROW
BEGIN
  IF NOT (OLD.data_inicio <=> NEW.data_inicio)
     OR NOT (OLD.data_fim <=> NEW.data_fim)
     OR NOT (OLD.modalidade <=> NEW.modalidade)
     OR NOT (OLD.limite_participantes <=> NEW.limite_participantes)
     OR NOT (OLD.valor_inscricao <=> NEW.valor_inscricao) THEN
    INSERT INTO auditoria
      (tabela_afetada, operacao, chave_registro, autor, valor_anterior, valor_posterior)
    VALUES
      ('evento', 'UPDATE',
       CONCAT('evento=', OLD.id_evento),
       COALESCE(@usuario_app, USER()),
       JSON_OBJECT('data_inicio', OLD.data_inicio,
                   'data_fim', OLD.data_fim,
                   'modalidade', OLD.modalidade,
                   'limite_participantes', OLD.limite_participantes,
                   'valor_inscricao', OLD.valor_inscricao),
       JSON_OBJECT('data_inicio', NEW.data_inicio,
                   'data_fim', NEW.data_fim,
                   'modalidade', NEW.modalidade,
                   'limite_participantes', NEW.limite_participantes,
                   'valor_inscricao', NEW.valor_inscricao));
  END IF;
END$$

DELIMITER ;
