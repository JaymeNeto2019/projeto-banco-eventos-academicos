# Aplicar a atualização em uma base existente

As correções de código não mudam automaticamente as contas de outra instância MySQL. Faça uma cópia de segurança antes da atualização. Não execute `01_ddl.sql` para atualizar: ele apaga o banco.

## Credenciais locais

O `.env` da raiz e um ZIP em `.vscode` estavam rastreados pelo Git. Ambos foram retirados da versão atual. As cópias antigas podem permanecer no histórico ou em clones. As quatro senhas MySQL e a chave Flask que tenham sido utilizadas devem ser substituídas no ambiente correspondente. A limpeza de histórico deve ser coordenada com os colaboradores; esta atualização não usa force-push.

1. Pare a aplicação e guarde a configuração atual em local privado até concluir a mudança.
2. Na raiz, execute `python configurar_ambiente.py --rotacionar`. Para outra porta local, acrescente `--porta PORTA`. Esse comando gera `.env` e `sql/06_usuarios.local.sql` com novas senhas, sem exibi-las. Ele não conecta ao banco.
3. Abra o MySQL Workbench na instância correta com uma conta administradora. Execute `sql/12_integridade.sql` e o arquivo **local** `sql/06_usuarios.local.sql`. O primeiro corrige permissões e instala os gatilhos de capacidade; o segundo usa CREATE/ALTER USER, preservando tabelas, dados e usuários da aplicação.
4. Confira `DB_HOST` e `DB_PORT` no `.env`, instale `app/requirements-lock.txt` e reinicie a aplicação. A nova chave invalida os cookies antigos. Não coloque `.env`, o SQL local ou pacotes privados no Git.
5. Verifique login, agenda, certificados e um cadastro de evento. Execute `sql/10_verificacao_regras.sql` para listar inconsistências antigas. Elas não são apagadas silenciosamente pela migração; precisam ser examinadas antes de corrigir ou revogar certificados antigos.

Se a instância ainda não possui `usuario_app`, views, roles ou a procedure de cadastro, primeiro conclua os passos de instalação desses objetos (`04`, `05`, `06` e `11`) com o administrador. Instalação nova em base vazia segue o README principal.

`SESSION_COOKIE_SECURE=0` permite desenvolvimento local por HTTP. Use `1` no ambiente servido por HTTPS. A aplicação recusa uma chave Flask ausente ou de exemplo e sempre lê o `.env` da raiz, independentemente do diretório do comando.

## Mudanças de comportamento

- Agenda e validação de certificados funcionam para os três perfis.
- Cada requisição protegida confere atividade e perfil da conta no banco; mudança de permissão exige novo login.
- Eventos novos exigem responsável principal e passam por abertura explícita antes de aceitar inscrições.
- Inscrições bloqueiam evento, participante e atividade; o teto do evento conta participantes distintos. Requisições paralelas não confirmam horários sobrepostos para a mesma pessoa.
- Presença mínima deve ficar entre 75 e 100%; números não finitos são recusados. Presença de evento encerrado ou de participante já certificado fica bloqueada na aplicação.
- RN18 é validada no CRUD e por gatilhos em alterações de vagas, capacidade e sessões.
- Carga de volume cria responsáveis e datas de inscrição anteriores ao início. As evidências antigas em PDF e capturas são históricas e não foram reescritas para aparentar resultados novos.
- Dependências possuem versões fixas e há testes de regressão com MySQL no GitHub Actions.

Os scripts de restauração comparam contagens de tabelas, views, gatilhos e rotinas. Isso complementa o teste de importação, mas não substitui comparar o conteúdo e executar os fluxos restaurados.
