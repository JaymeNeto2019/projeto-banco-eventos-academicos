# Passo a passo - como colocar o projeto no GitHub

## 1. Antes de começar

Os nomes dos cinco integrantes, a turma **Ciência da Computação** e o **Grupo 10** já estão preenchidos no `README.md` e na capa do relatório. Antes de enviar, apenas confira se a grafia de todos os nomes está exatamente igual ao cadastro acadêmico.

## 2. Crie uma conta no GitHub (se ainda não tiver)

1. Acesse https://github.com/.
2. Clique em **Sign up** e conclua o cadastro.

## 3. Crie o repositório

1. No GitHub, clique no botão **+** no canto superior direito.
2. Clique em **New repository**.
3. Nome sugerido: `projeto-banco-eventos-academicos`.
4. Pode deixar como **Public**, a menos que o professor tenha pedido repositório privado.
5. NÃO marque a opção de criar README, porque esta pasta já possui um `README.md`.
6. Clique em **Create repository**.

## 4. Instale o Git no Windows

1. Acesse https://git-scm.com/download/win.
2. Instale mantendo as opções padrão.
3. Depois, abra a pasta do projeto no Explorador de Arquivos.
4. Clique com o botão direito dentro dela e escolha **Open Git Bash here** (ou abra o Terminal nessa pasta).

## 5. Configure seu nome e e-mail no Git (primeira vez apenas)

```bash
git config --global user.name "SEU NOME"
git config --global user.email "SEU EMAIL DO GITHUB"
```

## 6. Inicie o repositório local

Dentro da pasta do projeto:

```bash
git init
git add .
git commit -m "Etapa 1: modelagem e implementação inicial do banco"
```

## 7. Ligue sua pasta ao repositório do GitHub

Na página do repositório recém-criado, copie a URL HTTPS. Exemplo:

```text
https://github.com/seu-usuario/projeto-banco-eventos-academicos.git
```

Depois execute:

```bash
git branch -M main
git remote add origin https://github.com/seu-usuario/projeto-banco-eventos-academicos.git
git push -u origin main
```

Se o GitHub pedir autenticação, siga a janela de login do navegador/Git Credential Manager.

## 8. Para os outros integrantes contribuírem

O ideal é que cada pessoa faça pelo menos alguns commits identificados pelo próprio nome, porque o professor poderá consultar o histórico de participação.

Cada integrante pode clonar o repositório:

```bash
git clone https://github.com/seu-usuario/projeto-banco-eventos-academicos.git
```

Depois de alterar arquivos:

```bash
git add .
git commit -m "Descrição clara do que foi alterado"
git pull --rebase origin main
git push origin main
```

## 9. Teste final antes de entregar

No MySQL Workbench:

1. Execute `01_ddl.sql` do começo ao fim.
2. Execute `02_carga.sql`.
3. Execute as 15 consultas de `03_consultas.sql`.
4. Confira se o banco foi recriado sem erro.
5. Confira se o link do GitHub abre em uma janela anônima/incógnita.
6. Envie no AVA o link do repositório e o PDF do relatório.

## 10. Não faça isso

- Não envie senha de banco, token ou arquivo `.env` ao GitHub.
- Não altere arquivos depois do prazo se o professor considerar apenas a versão existente no horário da entrega.
- Não deixe só uma pessoa com todos os commits; a participação individual pode ser verificada.
