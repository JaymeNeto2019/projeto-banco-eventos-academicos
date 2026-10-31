# Correções verificadas — Gestão de Eventos Acadêmicos

## Instalação segura
1. No **GitHub Desktop**, abra o repositório e selecione **Branch > New branch** para trabalhar fora da `main`.
2. Copie a pasta `correcoes_repositorio` para a **raiz do projeto** (ao lado de `app`, `sql` e `docs`).
3. Abra um terminal na raiz e rode `python correcoes_repositorio/aplicar_correcoes.py`.
4. Confira as alterações no GitHub Desktop antes de fazer commit. Backups locais são criados em `.backup_correcoes/` — **não faça commit deles**.
5. Em um **banco de teste** já configurado com os scripts de base, execute novamente `sql/11_cadastro_publico.sql` como administrador MySQL. **Não reexecute `01_ddl.sql` em um banco com dados importantes: ele contém DROP DATABASE!**
6. Execute o Flask e valide manualmente: cadastro público, login, novo participante (ALUNO com matrícula; PROFESSOR e EXTERNO), menus por perfil, inscrições, presença e certificados.
7. Rode `cd app && python teste_fumaca.py` apenas em um **banco descartável de testes**: esse script escreve dados e ainda não cobre todas as telas novas.

## O que este pacote corrige
- `NameError: tipo is not defined` no POST de participantes.
- Inconsistência `eventos_academicos_final`/`eventos_academicos` na procedure de cadastro.
- Numeração repetida no menu lateral.
- Passo faltante para o cadastro público no `app/README.md`.

## O que NÃO foi verificado
- Login e operações com um MySQL real, nem PDF/DOCX finais, nem adequação completa às exigências da disciplina. Não há comprovação de testes de integração aprovados.
- O script `teste_fumaca.py` pode exigir ajustes para refletir a nova interface.

## Segurança
Não faça commit de `.env`, credenciais, nem de backups. Verifique o diff no GitHub Desktop antes de publicar.
