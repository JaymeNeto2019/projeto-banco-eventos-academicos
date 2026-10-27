-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 2
-- Arquivo: 06_usuarios.exemplo.sql   (MODELO - não use estas senhas)
--
-- COMO USAR:
--   1) Copie para 06_usuarios.local.sql (esse nome está no .gitignore).
--   2) Troque cada senha por uma senha forte e anote no seu .env local.
--   3) Execute depois de 06_seguranca.sql, como administrador do MySQL.
-- Nunca faça commit do arquivo .local nem do .env.
-- =============================================================
DROP USER IF EXISTS 'usr_admin_eventos'@'localhost';
DROP USER IF EXISTS 'usr_organizador'@'localhost';
DROP USER IF EXISTS 'usr_consulta'@'localhost';
DROP USER IF EXISTS 'usr_app_auth'@'localhost';

CREATE USER 'usr_admin_eventos'@'localhost' IDENTIFIED BY 'TROQUE_ESTA_SENHA_1';
CREATE USER 'usr_organizador'@'localhost'   IDENTIFIED BY 'TROQUE_ESTA_SENHA_2';
CREATE USER 'usr_consulta'@'localhost'      IDENTIFIED BY 'TROQUE_ESTA_SENHA_3';
CREATE USER 'usr_app_auth'@'localhost'      IDENTIFIED BY 'TROQUE_ESTA_SENHA_4';

GRANT 'r_admin_eventos' TO 'usr_admin_eventos'@'localhost';
GRANT 'r_organizador'   TO 'usr_organizador'@'localhost';
GRANT 'r_consulta'      TO 'usr_consulta'@'localhost';
GRANT 'r_autenticacao'  TO 'usr_app_auth'@'localhost';

SET DEFAULT ROLE 'r_admin_eventos' TO 'usr_admin_eventos'@'localhost';
SET DEFAULT ROLE 'r_organizador'   TO 'usr_organizador'@'localhost';
SET DEFAULT ROLE 'r_consulta'      TO 'usr_consulta'@'localhost';
SET DEFAULT ROLE 'r_autenticacao'  TO 'usr_app_auth'@'localhost';
