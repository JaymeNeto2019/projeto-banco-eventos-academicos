-- Atualização sem DROP DATABASE e sem alteração dos dados existentes.
-- Executar como administrador após 04, 05, 06 e 11. Reexecutável.
USE eventos_academicos;

GRANT SELECT ON eventos_academicos.vw_agenda_publica TO 'r_admin_eventos', 'r_organizador';
GRANT SELECT ON eventos_academicos.vw_validacao_certificado TO 'r_admin_eventos', 'r_organizador';
GRANT INSERT, UPDATE ON eventos_academicos.organizacao_evento TO 'r_organizador';

-- RN18 também protege alterações diretas e remarcações feitas pelo banco.
DROP TRIGGER IF EXISTS trg_rn18_atividade_upd;
DROP TRIGGER IF EXISTS trg_rn18_sala_upd;
DROP TRIGGER IF EXISTS trg_rn18_sessao_ins;
DROP TRIGGER IF EXISTS trg_rn18_sessao_upd;
DELIMITER $$
CREATE TRIGGER trg_rn18_atividade_upd BEFORE UPDATE ON atividade FOR EACH ROW
BEGIN
  DECLARE capacidade_minima INT;
  SELECT MIN(sa.capacidade) INTO capacidade_minima
    FROM sessao_atividade s JOIN sala sa USING(id_sala)
    WHERE s.id_atividade=OLD.id_atividade FOR UPDATE;
  IF NEW.vagas > capacidade_minima THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='RN18: vagas acima da capacidade da sala';
  END IF;
END$$
CREATE TRIGGER trg_rn18_sala_upd BEFORE UPDATE ON sala FOR EACH ROW
BEGIN
  DECLARE vagas_maximas INT;
  SELECT MAX(a.vagas) INTO vagas_maximas
    FROM sessao_atividade s JOIN atividade a USING(id_atividade)
    WHERE s.id_sala=OLD.id_sala FOR UPDATE;
  IF NEW.capacidade < vagas_maximas THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='RN18: capacidade abaixo das vagas agendadas';
  END IF;
END$$
CREATE TRIGGER trg_rn18_sessao_ins BEFORE INSERT ON sessao_atividade FOR EACH ROW
BEGIN
  DECLARE capacidade_sala INT;
  DECLARE vagas_atividade INT;
  SELECT capacidade INTO capacidade_sala FROM sala WHERE id_sala=NEW.id_sala FOR UPDATE;
  SELECT vagas INTO vagas_atividade FROM atividade WHERE id_atividade=NEW.id_atividade FOR UPDATE;
  IF vagas_atividade > capacidade_sala THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='RN18: vagas acima da capacidade da sala';
  END IF;
END$$
CREATE TRIGGER trg_rn18_sessao_upd BEFORE UPDATE ON sessao_atividade FOR EACH ROW
BEGIN
  DECLARE capacidade_sala INT;
  DECLARE vagas_atividade INT;
  SELECT capacidade INTO capacidade_sala FROM sala WHERE id_sala=NEW.id_sala FOR UPDATE;
  SELECT vagas INTO vagas_atividade FROM atividade WHERE id_atividade=NEW.id_atividade FOR UPDATE;
  IF vagas_atividade > capacidade_sala THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='RN18: vagas acima da capacidade da sala';
  END IF;
END$$
DELIMITER ;

-- Registros preexistentes não são apagados nem corrigidos silenciosamente.
-- Execute 10_verificacao_regras.sql para identificar pendências antigas.
