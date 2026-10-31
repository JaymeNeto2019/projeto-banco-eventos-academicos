-- Etapa adicional: cadastro público sem fornecer INSERT direto à conta de autenticação.
-- Executar UMA VEZ como administrador do MySQL (após 06_seguranca.sql).
-- Reexecutável. A conta AUTH recebe somente EXECUTE nesta procedure.
USE eventos_academicos_final;

DROP PROCEDURE IF EXISTS cadastrar_usuario_publico;
DELIMITER $$
CREATE PROCEDURE cadastrar_usuario_publico(
    IN p_login VARCHAR(60),
    IN p_senha_hash VARCHAR(255)
)
SQL SECURITY DEFINER
BEGIN
    -- A aplicação pode solicitar somente conta CONSULTA; o banco também impõe.
    IF p_login IS NULL OR CHAR_LENGTH(TRIM(p_login)) < 3 OR
       p_senha_hash IS NULL OR p_senha_hash NOT LIKE '$2b$%' OR
       CHAR_LENGTH(p_senha_hash) < 60 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Dados de cadastro invalidos';
    END IF;

    INSERT INTO usuario_app (login, senha_hash, perfil, ativo)
    VALUES (TRIM(p_login), p_senha_hash, 'CONSULTA', TRUE);
END$$
DELIMITER ;

GRANT EXECUTE ON PROCEDURE eventos_academicos_final.cadastrar_usuario_publico
TO 'r_autenticacao';
