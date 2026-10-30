# Sistema de Gestão de Eventos Acadêmicos

Projeto Final da disciplina **Laboratório de Banco de Dados — 2026/2** (UCB). Etapa 1: projeto e construção do banco. Etapa 2: operação, interface e desempenho.

## Integrantes
- ISAAC BARBOSA DA SILVA
- ÁTILA DE MELO CANTOARA
- VICTOR LEMOS DE ABREU OLIVEIRA
- JOAO PEDRO CARNEIRO IBIAPINO
- JAYME BERNARDINO DA SILVA NETO

**Turma:** Ciência da Computação — **Grupo:** 10 — **Interlocutor:** [PREENCHER]

## Tema e escopo
Banco de dados para gestão de eventos acadêmicos, atividades, sessões, salas, participantes, organizadores, inscrições, histórico de status e certificados.

**SGBD:** MySQL 8.0 ou superior. **Aplicação:** Python 3.10+ / Flask.

## Estrutura
```
repositorio/
├── README.md
├── PASSO_A_PASSO_GITHUB.md
├── .gitignore                 # .env, backup.cnf e 06_usuarios.local.sql NUNCA vão para o Git
├── .env.example               # modelo das credenciais (sem senhas reais)
├── docs/
│   ├── relatorio-etapa1.pdf  mer-conceitual.*  modelo-logico.*  dicionario-dados.*     # Etapa 1
│   ├── relatorio-etapa2.pdf                                                           # Etapa 2 (relatório final)
│   └── evidencias/            # saídas brutas dos experimentos (perfis, gatilhos, transações, concorrência, EXPLAIN, backup)
├── sql/
│   ├── 01_ddl.sql  02_carga.sql  03_consultas.sql                 # Etapa 1
│   ├── 04_views.sql  05_triggers.sql                              # visões, auditoria
│   ├── 06_seguranca.sql  06_usuarios.exemplo.sql                  # perfis (GRANT/REVOKE), usuario_app
│   ├── 07_estudo_indices.sql  08_carga_volume.sql                 # EXPLAIN antes/depois + dados sintéticos
│   └── 09_transacao_concorrencia.sql                              # roteiro das 2 sessões
├── app/                       # aplicação Flask (ver app/README.md)
└── backup/                    # backup.sh, restaurar_teste.sh, plano de backup
```

## Como executar
**Banco** (como administrador do MySQL, nesta ordem): `01_ddl.sql` → `02_carga.sql` → `03_consultas.sql` → `04_views.sql` → `05_triggers.sql` → `06_seguranca.sql` → `06_usuarios.local.sql`
(cópia de `06_usuarios.exemplo.sql` com senhas reais, **fora do Git**). Para os estudos de desempenho: `08_carga_volume.sql` e depois `07_estudo_indices.sql`.

**Aplicação:** siga o passo a passo de [`app/README.md`](app/README.md) (venv, `pip install -r requirements.txt`, `.env`, `python criar_usuario.py admin ADMIN`, `python app.py`).
Teste automático: `python teste_fumaca.py`.

## Observação sobre os dados
Todos os dados de carga são sintéticos, criados exclusivamente para fins acadêmicos. Nenhum dado pessoal real de terceiros é utilizado.

## Uso de IA
Foi utilizado o assistente Claude (Anthropic) como apoio: na Etapa 1, à estruturação do domínio, revisão de regras, SQL inicial e documentação; na Etapa 2, à geração inicial de views, gatilhos, perfis de acesso, aplicação Flask, scripts de desempenho, concorrência e backup, e ao rascunho do relatório.
Detalhes de **em que partes** e **como o grupo verificou** o resultado estão na seção 8 do `docs/relatorio-etapa2.pdf`. [PREENCHER: confirmar e complementar com o que o grupo efetivamente verificou e alterou.]
