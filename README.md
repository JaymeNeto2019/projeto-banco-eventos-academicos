# Gestão de Eventos Acadêmicos — Projeto Final de Laboratório de Banco de Dados (UCB 2026/2)

> Preencha: integrantes, interlocutor e papéis (Etapa 1). Esta é a estrutura **da Etapa 2**.

```
repositorio/
├── README.md
├── .gitignore               # .env, backup.cnf e 06_usuarios.local.sql NUNCA vão para o Git
├── .env.example             # modelo das credenciais (sem senhas reais)
├── docs/                    # Etapa 1 + relatorio-etapa2 (PDF) + esqueleto e roteiro de demonstração
├── sql/
│   ├── 01_ddl.sql  02_carga.sql  03_consultas.sql        # Etapa 1
│   ├── 04_views.sql  05_triggers.sql                      # Etapa 2: relatório, restrição, auditoria
│   ├── 06_seguranca.sql  06_usuarios.exemplo.sql          # Etapa 2: perfis (GRANT/REVOKE) e usuário da aplicação
│   ├── 07_estudo_indices.sql  08_carga_volume.sql         # Etapa 2: EXPLAIN antes/depois e dados sintéticos
│   └── 09_transacao_concorrencia.sql                      # Etapa 2: roteiro das 2 sessões
├── app/                     # aplicação Flask (ver app/README.md)
└── backup/                  # backup.sh, restaurar_teste.sh, README_backup.md (plano de backup)
```

**Ordem de execução do banco:** 01 → 02 → (03) → 04 → 05 → 06_seguranca → 06_usuarios.local → *(opcional, para o B4)* 08 → 07.
**Banco:** MySQL 8.0+. **Aplicação:** ver `app/README.md`.

## Uso de inteligência artificial
(Preencha com honestidade: quais partes usaram IA, e como o grupo verificou — ver `docs/relatorio-etapa2-esqueleto.md`, seção 9.)
