# Sistema de Gestão de Eventos Acadêmicos

Projeto da disciplina **Laboratório de Banco de Dados - 2026/2**.

## Integrantes

- ISAAC BARBOSA DA SILVA
- ÁTILA DE MELO CANTOARA
- VICTOR LEMOS DE ABREU OLIVEIRA
- JOAO PEDRO CARNEIRO IBIAPINO
- JAYME BERNARDINO DA SILVA NETO

**Turma:** Ciência da Computação  
**Grupo:** 10

## Tema e escopo

Banco de dados para gestão de eventos acadêmicos, atividades, sessões, salas, participantes, organizadores, inscrições, histórico de status e certificados.

## SGBD

MySQL 8.0 ou superior.

## Estrutura

```text
repositorio/
├── README.md
├── PASSO_A_PASSO_GITHUB.md
├── docs/
│   ├── relatorio-etapa1.pdf
│   ├── relatorio-etapa1.docx
│   ├── mer-conceitual.pdf
│   ├── mer-conceitual.png
│   ├── mer-conceitual.drawio
│   ├── mer-conceitual.dot
│   ├── modelo-logico.pdf
│   ├── modelo-logico.png
│   ├── modelo-logico.dot
│   ├── dicionario-dados.pdf
│   └── dicionario-dados.docx
└── sql/
    ├── 01_ddl.sql
    ├── 02_carga.sql
    └── 03_consultas.sql
```

## Como executar

1. Abra MySQL Workbench (ou outro cliente compatível com MySQL 8.0+).
2. Execute `sql/01_ddl.sql` inteiro.
3. Execute `sql/02_carga.sql` inteiro.
4. Execute `sql/03_consultas.sql` e confira as 15 consultas.
5. Antes da entrega, apague o banco e repita os passos 2 a 4 do zero.

## Observação sobre os dados

Todos os dados inseridos pelo script de carga são sintéticos e foram criados exclusivamente para fins acadêmicos.

## Uso de IA

Foi utilizado um assistente de IA como apoio à estruturação do domínio, revisão de regras, geração inicial de SQL e documentação. O material deve ser revisado e testado pela equipe antes da entrega.
