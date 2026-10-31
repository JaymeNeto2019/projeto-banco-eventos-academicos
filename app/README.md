# Aplicação (Etapa 2)

Flask + MySQL. Foi escrita para exibir o que a disciplina avalia: consultas parametrizadas, transações explícitas,
erros de restrição com mensagem compreensível, acesso por perfil (uma conta MySQL por perfil) e senhas com hash+sal.

## Como subir (máquina limpa)
1. **Banco** (como administrador do MySQL, nesta ordem): `sql/01_ddl.sql`, `02_carga.sql`, `04_views.sql`, `05_triggers.sql`,
   `06_seguranca.sql`, o seu `06_usuarios.local.sql` (cópia de `06_usuarios.exemplo.sql` com senhas reais) **e `sql/11_cadastro_publico.sql`**, necessário para criar contas na tela `/cadastro`. Execute os SQL a partir da raiz do repositório. O banco configurado em `.env` deve ser `eventos_academicos`.
2. **Credenciais**: `cp .env.example .env` e preencha com as senhas criadas no passo anterior (o `.env` não vai para o Git).
3. **Dependências** (Python 3.10+):
   ```bash
   cd app
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Primeiro usuário** (a senha é pedida sem eco e gravada com bcrypt): `python criar_usuario.py admin ADMIN`
5. **Executar**: `python app.py` e abrir http://localhost:5000
6. **Teste automático** (evidência para o relatório): `python teste_fumaca.py` — imprime PASSOU/FALHOU por verificação.
   Ele cria dados fictícios próprios e usuários `t_admin`, `t_org`, `t_cons`; apague-os depois (ou use um banco de testes).

## Onde cada item do checklist aparece
| Item | Onde |
|---|---|
| 4 CRUDs | `/crud/instituicao`, `/crud/sala`, `/crud/categoria_evento`, `/crud/evento`, `/crud/atividade` (config em `entidades.py`) |
| 2 consultas parametrizadas | `/consulta/ocupacao` (JOIN + LEFT JOIN + GROUP BY + HAVING) e `/consulta/participacao` |
| Relatório alimentado por view | `/relatorio` → `vw_relatorio_eventos` |
| Operação em 2+ tabelas numa transação | `/operacoes/encerrar-evento` (`historico_status_evento` + `certificado`) |
| Controle de vagas e concorrência | `/operacoes/inscrever` (`SELECT ... FOR UPDATE`; campo "segurar o bloqueio" para o experimento com 2 sessões) |
| ROLLBACK demonstrável | caixa "Simular falha no meio da transação" nas duas operações |
| Mensagens de erro amigáveis | `db.py` (`REGRAS` e `mensagem_erro`) |
| Credenciais fora do código | `.env` (no `.gitignore`) lido por `db.py` |
| Perfis com menor privilégio | `db.py` escolhe a conta MySQL pelo perfil do login; o BANCO nega o resto (tente `/auditoria` como organizador) |
| Senha com hash e sal | `app.py: hash_senha` (bcrypt) e `login()`; tabela `usuario_app` |
| Autor na auditoria | `db.conectar` executa `SET @usuario_app = <login>` (lido pelos gatilhos) |
| Proteção contra SQL injection | só `%s` parametrizado; para o relatório, digite `' OR '1'='1` no campo "Sigla da instituição" de `/consulta/participacao` e registre o resultado (nenhuma linha, nenhum erro) |


