# Esqueleto do relatório final (Etapa 2) + roteiro da demonstração

> O PDF final precisa **incorporar a Etapa 1 revisada** (A1–A5, com as correções da devolutiva) e acrescentar as seções abaixo.
> Cada seção diz **o que colar como evidência** e onde ela é gerada. Apague estas instruções ao escrever.

## 0. Etapa 1 revisada
- Liste, em uma tabela, cada observação da devolutiva do professor → o que foi alterado → onde (arquivo/página).
- Se algo não foi corrigido, explique por quê. Quem reentrega sem revisão perde pontos.

## 1. Aplicação (B1)
- Prints: login, um CRUD completo (criar/editar/excluir), as 2 consultas com filtros, o relatório, uma mensagem de erro amigável.
- Tabela: tela → tabelas/visões usadas → tipo de SQL (JOIN, GROUP BY, HAVING). Ver tabela em `app/README.md`.

## 2. Camada de acesso a dados (B2)
- Trecho de `db.py`/`app.py` mostrando `%s` (consulta parametrizada). Declare que não há concatenação de strings em valores.
- **Teste de SQL injection:** entrada `' OR '1'='1` em "Sigla da instituição" (`/consulta/participacao?...`) → resultado: nenhuma linha, sem erro. Print + texto da entrada.
- Credenciais: `.env` fora do Git (print do `.gitignore` e do `git status` sem o `.env`).

## 3. Transações e concorrência (B3)
- **Sucesso:** print de `/operacoes/encerrar-evento` + `SELECT` em `historico_status_evento` e `certificado` mostrando o resultado. Escreva a sequência SQL: `START TRANSACTION → SELECT ... FOR UPDATE → INSERT historico → INSERT certificado → COMMIT`.
- **Falha provocada:** marque "Simular falha" → mensagem de ROLLBACK + `SELECT COUNT(*)` das duas tabelas antes e depois (iguais).
- **Experimento com 2 sessões:** siga `sql/09_transacao_concorrencia.sql` (partes 3 a 5). Anote: comando de cada sessão, o que B observou (espera, erro 1205 ou 1213), saída de `SELECT @@transaction_isolation` e `SHOW ENGINE INNODB STATUS` (deadlock).
  Alternativa pela aplicação: abra duas abas em `/operacoes/inscrever`, use "segurar o bloqueio" = 20 na primeira e envie a segunda em seguida.
- **Justificativa do isolamento:** REPEATABLE READ (padrão do InnoDB) + `FOR UPDATE` onde há regra de capacidade; diga por que não precisa de SERIALIZABLE (custo/bloqueios) e o risco de READ COMMITTED (leitura não repetível entre `COUNT` e `INSERT`).

## 4. Otimização de consultas (B4)
- Gere volume com `sql/08_carga_volume.sql` e informe as contagens (`SELECT COUNT(*)`).
- Para cada um dos 3 estudos de `sql/07_estudo_indices.sql`: consulta, `EXPLAIN ANALYZE` antes (com leitura em texto: tipo de acesso, linhas lidas, tempo), índice criado (colunas e **por que nessa ordem**), `EXPLAIN ANALYZE` depois, comparação do tempo (mediana de 3 execuções).
- **Discussão honesta:** ganhos pequenos ou nulos (o estudo 3 é candidato) também valem; explique por quê (o índice da FK já cobre `id_sala`; poucas linhas por sala; custo de escrita e espaço).
- Lembrete: os números mudam de máquina para máquina — use os SEUS.

## 5. Segurança e controle de acesso (B5)
- Tabela dos perfis: papel → conta → o que pode/não pode (de `06_seguranca.sql`). Prints de **login real** com cada conta: um comando permitido e um negado (erro 1142).
- A visão de restrição: `vw_agenda_publica` / `vw_validacao_certificado` (o que escondem: colunas pessoais, eventos cancelados, nome do titular mascarado).
- Senhas: print de `SELECT login, LEFT(senha_hash, 15) FROM usuario_app` (mostra `$2b$12$...`), explicando bcrypt + sal embutido.
- **Dados pessoais (LGPD):**

| Dado | Tabela | Cuidado adotado |
|---|---|---|
| Nome, e-mail, telefone, data de nascimento | `pessoa` | carga 100% fictícia; só admin/organizador leem; visões públicas não expõem |
| Login e senha | `usuario_app` | só hash bcrypt com sal; perfil de autenticação enxerga só colunas necessárias |
| Autor das alterações | `auditoria` | só leitura para admin; escrita apenas por gatilhos |
| Titular do certificado | `certificado` | validação pública mostra nome mascarado |

## 6. Gatilhos e auditoria (B6)
- Justificativa do que é auditado (comentário no topo de `05_triggers.sql`).
- Evidência: um `UPDATE` de status de inscrição e um de data do evento, e o `SELECT` em `auditoria` (autor, data, valor anterior/posterior). Pela aplicação, o autor sai como o login (não o usuário do banco).

## 7. Projeto físico e armazenamento (B7)
- Revisão dos tipos de dados: o que mudaria e por quê (ex.: `BIGINT` em ids que nunca passarão de milhões; `DECIMAL(4,1)` da carga horária; `VARCHAR` oversized; `VARCHAR` x `ENUM` nos status).
- **Estimativa de crescimento em 2 anos:** pegue `SELECT table_name, table_rows, data_length+index_length FROM information_schema.tables WHERE table_schema='eventos_academicos'` e projete (ex.: nº de eventos/ano × atividades × inscrições). Mostre a conta.
- Backup: ver `backup/README_backup.md` (frequência, retenção, teste de restauração) + saída de `restaurar_teste.sh` (`RESTAURAÇÃO VERIFICADA`).
- Particionamento/arquivamento: candidata natural = `inscricao_atividade` e `auditoria` (por ano/`data_hora`); proponha a regra ("arquivar eventos ENCERRADOS há mais de 2 anos") ou justifique que não compensa no volume atual.

## 8. Teste automático
- Cole a saída de `python teste_fumaca.py` (todas as linhas PASSOU) como evidência complementar.

## 9. Declaração de uso de inteligência artificial
> Modelo — **preencha só com o que for verdade**. O professor confere na arguição.
- Ferramenta(s) usada(s): ______.
- Partes em que foi usada: (ex.: geração inicial de views/gatilhos/perfis; esqueleto da aplicação Flask; scripts de backup; revisão do DDL).
- Como o grupo verificou: (ex.: executou todos os scripts em base limpa; leu e entendeu cada gatilho; testou cada perfil com login real; rodou o teste automático; alterou X e Y).
- O que o grupo escreveu/decidiu por conta própria: ______.

---
# Roteiro da demonstração (15 min) — ensaiem com cronômetro
Prepare antes: banco povoado, aplicação rodando, **2 terminais MySQL abertos**, navegador logado como admin e outro perfil (janela anônima).

| Tempo | Quem | O que fazer |
|---|---|---|
| 0:00–2:00 | Contexto | Domínio, entidades principais, **o que mudou no modelo desde a Etapa 1** (usuario_app, auditoria, ajustes da devolutiva). |
| 2:00–6:00 | CRUD e consultas | Cadastrar uma sala/atividade; rodar `/consulta/ocupacao` com filtro; abrir `/relatorio` e dizer que vem da view. |
| 6:00–9:00 | Transação | `/operacoes/encerrar-evento` com sucesso (mostrar as 2 tabelas) → repetir com "Simular falha" (mostrar contagens iguais). |
| 9:00–11:00 | Restrições | Tentar cadastrar sala com capacidade 0 e e-mail duplicado → mensagem tratada; mostrar que não aparece exceção do driver. |
| 11:00–14:00 | Desempenho e acesso | `EXPLAIN ANALYZE` antes/depois de um índice no terminal; entrar como **organizador** e como **consulta** e abrir `/auditoria` (negado) e `/agenda`. |
| 14:00–15:00 | Arguição | Qualquer integrante pode ser sorteado: **todos precisam saber explicar todas as partes**. |

Perguntas prováveis: por que FOR UPDATE? o que acontece se dois usuários se inscreverem na última vaga? por que o índice tem essas colunas nessa ordem? o que o perfil de consulta enxerga e por quê? onde fica o sal da senha? o que o gatilho grava no lugar do autor se a aplicação não definir `@usuario_app`?
