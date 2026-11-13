# Aplicação (Etapa 2)

Flask + MySQL. Foi escrita para exibir o que a disciplina avalia: consultas parametrizadas, transações explícitas,
erros de restrição com mensagem compreensível, acesso por perfil (uma conta MySQL por perfil) e senhas com hash+sal.

## Como subir (máquina limpa)
1. **Banco** (como administrador do MySQL, nesta ordem): `sql/01_ddl.sql`, `02_carga.sql`, `04_views.sql`, `05_triggers.sql`,
   `06_seguranca.sql`, `06_usuarios.local.sql`, `11_cadastro_publico.sql` e `12_integridade.sql`. Execute os SQL a partir da raiz. O banco deve ser `eventos_academicos`. `01_ddl.sql` apaga o esquema; para atualizar uma base existente, siga `docs/ATUALIZACAO_SEGURANCA.md`.
2. **Credenciais**: antes de executar `06_usuarios.local.sql`, rode `python configurar_ambiente.py` na raiz. Ele gera `.env` e esse SQL com senhas aleatórias correspondentes. Os dois são privados e ficam fora do Git. Não reutilize as credenciais antigas publicadas. Uma configuração já existente só é substituída com `--rotacionar`.
3. **Dependências** (Python 3.10+):
   ```bash
   cd app
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements-lock.txt
   ```
4. **Primeiro usuário** (a senha é pedida sem eco e gravada com bcrypt): `python criar_usuario.py admin ADMIN`
5. **Executar**: `python app.py` e abrir http://localhost:5000
6. **Teste automático** (evidência para o relatório): `python teste_fumaca.py` — imprime PASSOU/FALHOU por verificação.
   Ele cria dados fictícios próprios e usuários `t_admin`, `t_org`, `t_cons`; apague-os depois (ou use um banco de testes).

## Fluxo de operação

Crie o evento escolhendo um organizador responsável, cadastre suas atividades e use **Abrir inscrições**.
Só eventos ABERTOS e com início futuro aceitam inscrições. O limite total conta pessoas distintas confirmadas;
ao atingir o limite de pessoas ou de vagas da atividade, novas inscrições entram em lista de espera.
Inscrições confirmadas não podem se sobrepor no horário, inclusive quando feitas simultaneamente em eventos diferentes.
Registre a presença antes de encerrar. A emissão exige média mínima de 75% e presença informada em todas as atividades confirmadas.
Após emitir certificado ou encerrar o evento, a tela comum não permite alterar presença.
As conexões da aplicação usam READ COMMITTED com bloqueios explícitos; os experimentos SQL manuais podem continuar comparando os dois isolamentos.

## Testes de regressão

Em instância descartável configurada pelo `.env`, execute na raiz:
```powershell
$env:ALLOW_TEST_DATABASE='1'
python -m unittest discover -s tests -v
```
As suítes criam dados e usuários fictícios. Não as execute no banco de operação.

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


