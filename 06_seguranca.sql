-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 2
-- Arquivo: 06_seguranca.sql  (B5 - Segurança e controle de acesso)
-- Pré-requisito: 01_ddl.sql, 04_views.sql e 05_triggers.sql (tabela auditoria)
-- Executar com um usuário administrador do MySQL (ex.: root).
--
-- Este arquivo cria: tabela de usuários da aplicação, 4 PAPÉIS (roles)
-- com o princípio do menor privilégio e as permissões de cada um.
-- As CONTAS (com senhas) ficam em 06_usuarios.exemplo.sql, copiado para
-- um arquivo local fora do Git, para não versionar credenciais.
-- =============================================================
USE eventos_academicos;

-- -------------------------------------------------------------
-- Usuários DA APLICAÇÃO (login da tela). A senha NUNCA é gravada em texto
-- claro: a aplicação calcula o hash com sal (bcrypt/argon2, o sal já vem
-- embutido no texto do hash) e grava apenas senha_hash.
-- A restrição ck_usuario_app_hash recusa valores que não pareçam um hash
-- ($2b$..., $argon2id$...), barrando senha em texto claro por engano.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuario_app (
  id_usuario   INT UNSIGNED    NOT NULL AUTO_INCREMENT,
  id_pessoa    BIGINT UNSIGNED NULL,
  login        VARCHAR(60)     NOT NULL,
  senha_hash   VARCHAR(255)    NOT NULL,
  perfil       VARCHAR(15)     NOT NULL,
  ativo        BOOLEAN         NOT NULL DEFAULT TRUE,
  criado_em    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ultimo_login DATETIME        NULL,
  CONSTRAINT pk_usuario_app PRIMARY KEY (id_usuario),
  CONSTRAINT uq_usuario_app_login UNIQUE (login),
  CONSTRAINT uq_usuario_app_pessoa UNIQUE (id_pessoa),
  CONSTRAINT ck_usuario_app_perfil CHECK (perfil IN ('ADMIN','ORGANIZADOR','CONSULTA')),
  CONSTRAINT ck_usuario_app_hash CHECK (senha_hash LIKE '$%' AND CHAR_LENGTH(senha_hash) >= 60),
  CONSTRAINT fk_usuario_app_pessoa FOREIGN KEY (id_pessoa)
    REFERENCES pessoa(id_pessoa)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- Papéis do banco (MySQL 8)
-- -------------------------------------------------------------
CREATE ROLE IF NOT EXISTS 'r_admin_eventos', 'r_organizador', 'r_consulta', 'r_autenticacao';

-- ---- r_admin_eventos: gerencia todos os dados do domínio -------------
-- Sem DDL, sem GRANT OPTION. A auditoria é somente leitura: só os gatilhos
-- gravam nela (executam com os direitos de quem os criou).
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.pessoa                  TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.instituicao             TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.participante            TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.organizador             TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.categoria_evento        TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.sala                    TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.evento                  TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.historico_status_evento TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.atividade               TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.sessao_atividade        TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.inscricao_atividade     TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.organizacao_evento      TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.certificado             TO 'r_admin_eventos';
GRANT SELECT, INSERT, UPDATE         ON eventos_academicos.usuario_app             TO 'r_admin_eventos'; -- desativa em vez de apagar
GRANT SELECT                         ON eventos_academicos.auditoria               TO 'r_admin_eventos';
GRANT SELECT ON eventos_academicos.vw_evento_status_atual TO 'r_admin_eventos';
GRANT SELECT ON eventos_academicos.vw_relatorio_eventos   TO 'r_admin_eventos';

-- ---- r_organizador: opera os eventos do dia a dia ---------------------
-- Lê o domínio, cadastra/atualiza o que a operação exige e NÃO apaga dados
-- (exceto sessões, que podem ser remarcadas). Não enxerga usuario_app nem auditoria.
GRANT SELECT ON eventos_academicos.pessoa                  TO 'r_organizador';
GRANT SELECT ON eventos_academicos.instituicao             TO 'r_organizador';
GRANT SELECT ON eventos_academicos.organizador             TO 'r_organizador';
GRANT SELECT ON eventos_academicos.categoria_evento        TO 'r_organizador';
GRANT SELECT ON eventos_academicos.sala                    TO 'r_organizador';
GRANT SELECT ON eventos_academicos.organizacao_evento      TO 'r_organizador';
GRANT SELECT, INSERT, UPDATE ON eventos_academicos.participante            TO 'r_organizador';
GRANT SELECT, INSERT, UPDATE ON eventos_academicos.evento                  TO 'r_organizador';
GRANT SELECT, INSERT, UPDATE ON eventos_academicos.historico_status_evento TO 'r_organizador';
GRANT SELECT, INSERT, UPDATE ON eventos_academicos.atividade               TO 'r_organizador';
GRANT SELECT, INSERT, UPDATE ON eventos_academicos.inscricao_atividade     TO 'r_organizador';
GRANT SELECT, INSERT, UPDATE, DELETE ON eventos_academicos.sessao_atividade TO 'r_organizador';
GRANT INSERT, UPDATE ON eventos_academicos.pessoa TO 'r_organizador';
GRANT SELECT, INSERT, UPDATE ON eventos_academicos.certificado TO 'r_organizador';
-- Certificado emitido é imutável para o organizador (cancelamento é decisão do admin):
REVOKE UPDATE ON eventos_academicos.certificado FROM 'r_organizador';
GRANT SELECT ON eventos_academicos.vw_evento_status_atual TO 'r_organizador';
GRANT SELECT ON eventos_academicos.vw_relatorio_eventos   TO 'r_organizador';

-- ---- r_consulta: público externo; só enxerga as visões de restrição ----
GRANT SELECT ON eventos_academicos.vw_agenda_publica          TO 'r_consulta';
GRANT SELECT ON eventos_academicos.vw_validacao_certificado   TO 'r_consulta';

-- ---- r_autenticacao: usado pela aplicação SÓ na tela de login ----------
-- Privilégios por coluna: lê o necessário para conferir a senha e
-- atualiza apenas a data do último login.
GRANT SELECT (id_usuario, login, senha_hash, perfil, ativo) ON eventos_academicos.usuario_app TO 'r_autenticacao';
GRANT UPDATE (ultimo_login)                                 ON eventos_academicos.usuario_app TO 'r_autenticacao';
