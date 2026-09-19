-- =============================================================
-- Projeto Final - Laboratório de Banco de Dados - Etapa 1
-- Tema: Sistema de Gestão de Eventos Acadêmicos
-- SGBD: MySQL 8.0+
-- Arquivo: 01_ddl.sql
-- =============================================================

DROP DATABASE IF EXISTS eventos_academicos;
CREATE DATABASE eventos_academicos
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE eventos_academicos;

-- RN01/RN02: supertipo PESSOA e especialização em PARTICIPANTE/ORGANIZADOR.
CREATE TABLE pessoa (
  id_pessoa BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL,
  telefone VARCHAR(20) NULL,
  data_nascimento DATE NULL,
  criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_pessoa PRIMARY KEY (id_pessoa),
  CONSTRAINT uq_pessoa_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE TABLE instituicao (
  id_instituicao INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(150) NOT NULL,
  sigla VARCHAR(20) NOT NULL,
  tipo VARCHAR(10) NOT NULL,
  cidade VARCHAR(80) NOT NULL,
  uf CHAR(2) NOT NULL,
  site VARCHAR(200) NULL,
  CONSTRAINT pk_instituicao PRIMARY KEY (id_instituicao),
  CONSTRAINT uq_instituicao_sigla UNIQUE (sigla),
  CONSTRAINT ck_instituicao_tipo CHECK (tipo IN ('PUBLICA','PRIVADA','OUTRA'))
) ENGINE=InnoDB;

-- RN03/RN04: subtipo PARTICIPANTE.
CREATE TABLE participante (
  id_pessoa BIGINT UNSIGNED NOT NULL,
  tipo_participante VARCHAR(10) NOT NULL,
  matricula_academica VARCHAR(30) NULL,
  id_instituicao_origem INT UNSIGNED NULL,
  CONSTRAINT pk_participante PRIMARY KEY (id_pessoa),
  CONSTRAINT uq_participante_matricula UNIQUE (matricula_academica),
  CONSTRAINT ck_participante_tipo CHECK (tipo_participante IN ('ALUNO','PROFESSOR','EXTERNO')),
  CONSTRAINT ck_participante_matricula_aluno CHECK (
    tipo_participante <> 'ALUNO' OR matricula_academica IS NOT NULL
  ),
  CONSTRAINT fk_participante_pessoa FOREIGN KEY (id_pessoa)
    REFERENCES pessoa(id_pessoa)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_participante_instituicao FOREIGN KEY (id_instituicao_origem)
    REFERENCES instituicao(id_instituicao)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- RN05: subtipo ORGANIZADOR.
CREATE TABLE organizador (
  id_pessoa BIGINT UNSIGNED NOT NULL,
  cargo VARCHAR(80) NOT NULL,
  setor VARCHAR(100) NOT NULL,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT pk_organizador PRIMARY KEY (id_pessoa),
  CONSTRAINT fk_organizador_pessoa FOREIGN KEY (id_pessoa)
    REFERENCES pessoa(id_pessoa)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- RN06: autorrelacionamento de hierarquia entre categorias.
CREATE TABLE categoria_evento (
  id_categoria INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(100) NOT NULL,
  descricao VARCHAR(300) NULL,
  id_categoria_pai INT UNSIGNED NULL,
  CONSTRAINT pk_categoria_evento PRIMARY KEY (id_categoria),
  CONSTRAINT uq_categoria_evento_nome UNIQUE (nome),

  CONSTRAINT fk_categoria_pai FOREIGN KEY (id_categoria_pai)
    REFERENCES categoria_evento(id_categoria)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- RN17: salas possuem capacidade positiva.
CREATE TABLE sala (
  id_sala INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(80) NOT NULL,
  bloco VARCHAR(50) NOT NULL,
  capacidade INT UNSIGNED NOT NULL,
  acessivel BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT pk_sala PRIMARY KEY (id_sala),
  CONSTRAINT uq_sala_nome_bloco UNIQUE (nome, bloco),
  CONSTRAINT ck_sala_capacidade CHECK (capacidade > 0)
) ENGINE=InnoDB;

-- RN07-RN11: regras estruturais do EVENTO.
CREATE TABLE evento (
  id_evento BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_categoria INT UNSIGNED NOT NULL,
  id_instituicao_promotora INT UNSIGNED NOT NULL,
  titulo VARCHAR(180) NOT NULL,
  descricao VARCHAR(1000) NULL,
  data_inicio DATETIME NOT NULL,
  data_fim DATETIME NOT NULL,
  modalidade VARCHAR(12) NOT NULL,
  limite_participantes INT UNSIGNED NULL,
  gratuito BOOLEAN NOT NULL DEFAULT TRUE,
  valor_inscricao DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  url_evento VARCHAR(250) NULL,
  CONSTRAINT pk_evento PRIMARY KEY (id_evento),
  CONSTRAINT ck_evento_periodo CHECK (data_fim > data_inicio),
  CONSTRAINT ck_evento_modalidade CHECK (modalidade IN ('PRESENCIAL','ONLINE','HIBRIDO')),
  CONSTRAINT ck_evento_limite CHECK (limite_participantes IS NULL OR limite_participantes > 0),
  CONSTRAINT ck_evento_valor CHECK (
    (gratuito = TRUE AND valor_inscricao = 0.00)
    OR (gratuito = FALSE AND valor_inscricao > 0.00)
  ),
  CONSTRAINT fk_evento_categoria FOREIGN KEY (id_categoria)
    REFERENCES categoria_evento(id_categoria)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_evento_instituicao FOREIGN KEY (id_instituicao_promotora)
    REFERENCES instituicao(id_instituicao)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- RN12/RN13: entidade fraca e temporal; a PK depende do EVENTO.
CREATE TABLE historico_status_evento (
  id_evento BIGINT UNSIGNED NOT NULL,
  sequencia INT UNSIGNED NOT NULL,
  status VARCHAR(12) NOT NULL,
  data_hora DATETIME NOT NULL,
  observacao VARCHAR(300) NULL,
  CONSTRAINT pk_historico_status_evento PRIMARY KEY (id_evento, sequencia),
  CONSTRAINT ck_historico_sequencia CHECK (sequencia > 0),
  CONSTRAINT ck_historico_status CHECK (status IN ('PLANEJADO','ABERTO','ENCERRADO','CANCELADO')),
  CONSTRAINT fk_historico_evento FOREIGN KEY (id_evento)
    REFERENCES evento(id_evento)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- RN14: atividades pertencem a um único evento e possuem vagas/carga válidas.
CREATE TABLE atividade (
  id_atividade BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_evento BIGINT UNSIGNED NOT NULL,
  titulo VARCHAR(180) NOT NULL,
  tipo_atividade VARCHAR(20) NOT NULL,
  descricao VARCHAR(800) NULL,
  carga_horaria DECIMAL(4,1) NOT NULL,
  vagas INT UNSIGNED NOT NULL,
  obrigatoria BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT pk_atividade PRIMARY KEY (id_atividade),
  CONSTRAINT ck_atividade_tipo CHECK (tipo_atividade IN ('PALESTRA','MINICURSO','MESA_REDONDA','OFICINA')),
  CONSTRAINT ck_atividade_carga CHECK (carga_horaria > 0),
  CONSTRAINT ck_atividade_vagas CHECK (vagas > 0),
  CONSTRAINT fk_atividade_evento FOREIGN KEY (id_evento)
    REFERENCES evento(id_evento)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- RN16/RN17: entidade fraca SESSAO_ATIVIDADE.
CREATE TABLE sessao_atividade (
  id_atividade BIGINT UNSIGNED NOT NULL,
  numero_sessao INT UNSIGNED NOT NULL,
  id_sala INT UNSIGNED NOT NULL,
  inicio DATETIME NOT NULL,
  fim DATETIME NOT NULL,
  observacao VARCHAR(300) NULL,
  CONSTRAINT pk_sessao_atividade PRIMARY KEY (id_atividade, numero_sessao),
  CONSTRAINT ck_sessao_numero CHECK (numero_sessao > 0),
  CONSTRAINT ck_sessao_periodo CHECK (fim > inicio),
  CONSTRAINT fk_sessao_atividade FOREIGN KEY (id_atividade)
    REFERENCES atividade(id_atividade)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_sessao_sala FOREIGN KEY (id_sala)
    REFERENCES sala(id_sala)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- RN19-RN21: primeira associação N:N com atributos próprios.
CREATE TABLE inscricao_atividade (
  id_participante BIGINT UNSIGNED NOT NULL,
  id_atividade BIGINT UNSIGNED NOT NULL,
  data_inscricao DATETIME NOT NULL,
  status_inscricao VARCHAR(15) NOT NULL,
  percentual_presenca DECIMAL(5,2) NULL,
  nota_avaliacao DECIMAL(3,1) NULL,
  CONSTRAINT pk_inscricao_atividade PRIMARY KEY (id_participante, id_atividade),
  CONSTRAINT ck_inscricao_status CHECK (status_inscricao IN ('CONFIRMADA','LISTA_ESPERA','CANCELADA')),
  CONSTRAINT ck_inscricao_presenca CHECK (
    percentual_presenca IS NULL OR (percentual_presenca BETWEEN 0 AND 100)
  ),
  CONSTRAINT ck_inscricao_avaliacao CHECK (
    nota_avaliacao IS NULL OR (nota_avaliacao BETWEEN 0 AND 10)
  ),
  CONSTRAINT ck_inscricao_sem_presenca_pendente CHECK (
    status_inscricao = 'CONFIRMADA' OR percentual_presenca IS NULL
  ),
  CONSTRAINT fk_inscricao_participante FOREIGN KEY (id_participante)
    REFERENCES participante(id_pessoa)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_inscricao_atividade FOREIGN KEY (id_atividade)
    REFERENCES atividade(id_atividade)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- RN23/RN24: segunda associação N:N com atributos próprios.
CREATE TABLE organizacao_evento (
  id_organizador BIGINT UNSIGNED NOT NULL,
  id_evento BIGINT UNSIGNED NOT NULL,
  papel VARCHAR(80) NOT NULL,
  data_inicio_atuacao DATE NOT NULL,
  responsavel_principal BOOLEAN NOT NULL DEFAULT FALSE,
  CONSTRAINT pk_organizacao_evento PRIMARY KEY (id_organizador, id_evento),
  CONSTRAINT fk_organizacao_organizador FOREIGN KEY (id_organizador)
    REFERENCES organizador(id_pessoa)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_organizacao_evento FOREIGN KEY (id_evento)
    REFERENCES evento(id_evento)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- RN25/RN26: certificados têm chave própria e unicidade participante/evento.
CREATE TABLE certificado (
  id_certificado BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_participante BIGINT UNSIGNED NOT NULL,
  id_evento BIGINT UNSIGNED NOT NULL,
  codigo_validacao VARCHAR(40) NOT NULL,
  emitido_em DATETIME NOT NULL,
  carga_horaria DECIMAL(5,1) NOT NULL,
  url_validacao VARCHAR(250) NULL,
  CONSTRAINT pk_certificado PRIMARY KEY (id_certificado),
  CONSTRAINT uq_certificado_codigo UNIQUE (codigo_validacao),
  CONSTRAINT uq_certificado_participante_evento UNIQUE (id_participante, id_evento),
  CONSTRAINT ck_certificado_carga CHECK (carga_horaria > 0),
  CONSTRAINT fk_certificado_participante FOREIGN KEY (id_participante)
    REFERENCES participante(id_pessoa)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT fk_certificado_evento FOREIGN KEY (id_evento)
    REFERENCES evento(id_evento)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Índices de apoio às consultas da Etapa 1 e aos estudos de desempenho da Etapa 2.
CREATE INDEX idx_evento_periodo ON evento (data_inicio, data_fim);
CREATE INDEX idx_evento_categoria ON evento (id_categoria);
CREATE INDEX idx_historico_evento_data ON historico_status_evento (id_evento, data_hora);
CREATE INDEX idx_atividade_evento ON atividade (id_evento);
CREATE INDEX idx_sessao_inicio ON sessao_atividade (inicio);
CREATE INDEX idx_inscricao_atividade_status ON inscricao_atividade (id_atividade, status_inscricao);
CREATE INDEX idx_inscricao_participante_status ON inscricao_atividade (id_participante, status_inscricao);
CREATE INDEX idx_organizacao_evento_principal ON organizacao_evento (id_evento, responsavel_principal);
