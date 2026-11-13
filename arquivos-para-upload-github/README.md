# Conecta Acadêmico — Gestão de Eventos Acadêmicos

Projeto Final da disciplina **Laboratório de Banco de Dados — 2026/2** (UCB). Etapa 1: projeto e construção do banco. Etapa 2: operação, interface e desempenho.

## Integrantes
- ISAAC BARBOSA DA SILVA
- ÁTILA DE MELO CANTOARA
- VICTOR LEMOS DE ABREU OLIVEIRA
- JOAO PEDRO CARNEIRO IBIAPINO
- JAYME BERNARDINO DA SILVA NETO

**Turma:** Ciência da Computação — **Grupo:** 10 

## Tema e escopo
Banco de dados para gestão de eventos acadêmicos, atividades, sessões, salas, participantes, organizadores, inscrições, histórico de status e certificados.

**SGBD:** MySQL 8.0 ou superior. **Aplicação:** Python 3.10+ / Flask.

## Atualização de segurança e integridade

Para uma base existente, siga [docs/ATUALIZACAO_SEGURANCA.md](docs/ATUALIZACAO_SEGURANCA.md).
O `.env` é privado e é gerado por `python configurar_ambiente.py`; somente `.env.example` é público.
O SQL `12_integridade.sql` atualiza permissões e gatilhos sem apagar o banco.

## Estrutura
```
repositorio/
├── README.md
├── .gitignore                 # .env, backup.cnf e 06_usuarios.local.sql NUNCA vão para o Git
├── .env.example               # modelo das credenciais (sem senhas reais)
├── docs/
│   ├── relatorio-etapa1.pdf  mer-conceitual.*  modelo-logico.*  dicionario-dados.*     # Etapa 1
│   ├── relatorio-etapa2.pdf (e .docx)                                                 # Etapa 2 (relatório final)
│   └── evidencias/            # saídas dos experimentos (texto) e prints/ (capturas do MySQL Workbench)
├── sql/
│   ├── 01_ddl.sql  02_carga.sql  03_consultas.sql                 # Etapa 1 (01 inclui o gatilho da RN06)
│   ├── 04_views.sql  05_triggers.sql                              # visões, auditoria
│   ├── 06_seguranca.sql  06_usuarios.exemplo.sql                  # perfis (GRANT/REVOKE), usuario_app
│   ├── 07_estudo_indices.sql  08_carga_volume.sql                 # EXPLAIN antes/depois + dados sintéticos
│   ├── 09_transacao_concorrencia.sql                              # roteiro das 2 sessões
│   └── 10_verificacao_regras.sql                                  # regras atendidas por consulta (RN06 ciclos, RN12, RN15, RN18, RN22, RN24, RN26)
├── app/                       # aplicação Flask (ver app/README.md)
└── backup/                    # backup.sh, restaurar_teste.sh, plano de backup
```

## Como executar
**Banco** (como administrador do MySQL, nesta ordem): `01_ddl.sql` → `02_carga.sql` → `03_consultas.sql` → `04_views.sql` → `05_triggers.sql` → `06_seguranca.sql` → `06_usuarios.local.sql`
(gerado por `python configurar_ambiente.py`, **fora do Git**) → `11_cadastro_publico.sql` → `12_integridade.sql`. O `01_ddl.sql` apaga o esquema: use-o apenas na instalação inicial em base descartável/vazia. Se executar pela linha de comando, use `mysql --default-character-set=utf8mb4`. Para os estudos de desempenho, use um banco separado: `08_carga_volume.sql` e depois `07_estudo_indices.sql`.

**Aplicação:** siga [`app/README.md`](app/README.md) (venv, `pip install -r requirements-lock.txt`, `.env`, `python criar_usuario.py admin ADMIN`, `python app.py`).
Testes: `python app/teste_fumaca.py` e, em banco descartável, `ALLOW_TEST_DATABASE=1 python -m unittest discover -s tests -v` (PowerShell: `$env:ALLOW_TEST_DATABASE='1'` antes do comando). GitHub Actions executa as suítes em MySQL separado.

**Melhorias de interface:** tela de login revisada, cadastro público em `/cadastro` (cria apenas perfil CONSULTA, via procedure com `EXECUTE` limitado), painel inicial com atalhos, participantes, inscrições e presença. As permissões do MySQL continuam sendo a camada principal; ver `docs/MELHORIAS_INTERFACE.md`.

## Observação sobre os dados
Todos os dados de carga são sintéticos, criados exclusivamente para fins acadêmicos. Nenhum dado pessoal real de terceiros é utilizado.
A carga (`02_carga.sql`) tem data de referência em 30/10/2026: eventos já realizados estão ENCERRADOS, inscrições só existem em eventos já abertos (e com data anterior ao início), eventos CANCELADOS só têm inscrições canceladas, e há participantes sem inscrição e organizadores sem evento para exercitar os `LEFT JOIN`.

## Uso de IA
Foi utilizado o assistente Claude (Anthropic) como apoio: na Etapa 1, à estruturação do domínio, revisão de regras, SQL inicial e documentação; na Etapa 2, à geração inicial de views, gatilhos, perfis de acesso, aplicação Flask, scripts de desempenho, concorrência e backup, e ao rascunho do relatório.
Detalhes de **em que partes** e **como o grupo verificou** o resultado estão na seção 8 do `docs/relatorio-etapa2.pdf`.
