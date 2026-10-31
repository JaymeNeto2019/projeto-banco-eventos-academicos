# Complemento da aplicação — Login, cadastro, menu e operações

Projeto: **Gestão de Eventos Acadêmicos**, UCB 2026/2.

## Objetivo
Completar a navegação e os cadastros do sistema sem substituir a modelagem de dados nem os mecanismos da Etapa 2.

## Fluxo do usuário

1. Acessar `/login` ou criar conta em `/cadastro`.
2. Cadastro público usa a procedure `cadastrar_usuario_publico` com `SQL SECURITY DEFINER`; o perfil gravado é sempre `CONSULTA`.
3. O sistema usa `bcrypt` para hash de senhas e sessão Flask com token CSRF nas alterações.
4. Após entrar, o usuário acessa `/` (painel) com links conforme seu perfil.
5. Administradores podem criar outros usuários em `/usuarios/novo`.

## Funcionalidades e rotas

| Recurso | Rota | Perfis |
|---|---|---|
| Login | `/login` | sem sessão |
| Cadastro público | `/cadastro` | sem sessão (cria CONSULTA) |
| Painel | `/` | todos |
| Instituições, salas, categorias, eventos, atividades | `/crud/<entidade>` | ADMIN e ORGANIZADOR (alguns em leitura) |
| Participantes | `/participantes`, `/participantes/novo` | ADMIN e ORGANIZADOR |
| Inscrições | `/inscricoes`, `/operacoes/inscrever` | ADMIN e ORGANIZADOR |
| Registrar presença | `/presencas` | ADMIN e ORGANIZADOR |
| Encerrar evento/emitir certificados | `/operacoes/encerrar-evento` | ADMIN e ORGANIZADOR |
| Consultas e relatório | `/consulta/*`, `/relatorio` | ADMIN e ORGANIZADOR |
| Auditoria e criar usuários internos | `/auditoria`, `/usuarios/novo` | ADMIN |
| Agenda pública e validação de certificados | `/agenda`, `/certificados/validar` | todos os perfis autenticados |

## Aderência aos requisitos do banco

- Consultas com parâmetros `%s` e identificadores de CRUD provenientes de configuração fixa.
- `INSERT` em `pessoa` + `participante` dentro da **mesma transação**.
- Operações de vagas, concorrência, `COMMIT` e `ROLLBACK` continuam no código original.
- Autenticação separada das credenciais das contas MySQL de perfil.
- O cadastro público não ganha permissão de `INSERT` direto em `usuario_app`: a role AUTH pode chamar uma procedure que insere exclusivamente CONSULTA.
- Os privilégios para administradores/organizadores/consulta continuam definidos pelos GRANTs do MySQL, além da restrição de rota.

## Evidências para a apresentação

- Mostrar login incorreto e correto, cadastro de nova conta, acesso ao painel e logout.
- Tentar acessar a auditoria com um organizador/consulta: retorno 403.
- Criar participante, atividade, realizar inscrição, registrar presença e encerrar evento.
- Mostrar relatórios alimentados por views e log de auditoria.
- Executar `python teste_fumaca.py` depois de configurar o banco e revisar quaisquer falhas.

**Nota:** O código do kit foi validado estaticamente. Execução funcional com MySQL depende de esquema, carga e credenciais da máquina de demonstração; não se deve declarar testes de integração aprovados sem executá-los.
