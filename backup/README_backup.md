# Plano de backup (B7)

| Item | Decisão sugerida (ajuste ao que o grupo realmente configurar) |
|---|---|
| O que copiar | Banco `eventos_academicos` completo: dados, visões, gatilhos e rotinas (`mysqldump --single-transaction --routines --triggers --events`). As contas MySQL e seus GRANTs não vão no dump de um banco: recriar com `sql/06_seguranca.sql` + `sql/06_usuarios.local.sql`. O `.env` e o `backup.cnf` ficam fora do Git e devem ser guardados num cofre/gerenciador de senhas. |
| Frequência | Completo diário às 02:00 (baixo movimento). Para 2 anos de crescimento, avaliar backup incremental via binlog se a janela de perda aceitável for menor que 24 h. |
| Retenção | 14 dias de diários; 1 por semana por 8 semanas; 1 por mês por 12 meses (o script `backup.sh` aplica a janela diária; as demais por cópia manual/rotação). |
| Onde guardar | Pelo menos 2 locais: disco do servidor **e** outra máquina/nuvem (regra 3-2-1: 3 cópias, 2 mídias, 1 fora do local). |
| Como testar a restauração | `bash restaurar_teste.sh` restaura o último dump num banco temporário, compara a contagem de linhas de cada tabela e confere gatilhos. Executar após cada mudança de esquema e ao menos 1 vez por mês; registrar data e resultado. |
| Agendamento (Linux) | `0 2 * * * /caminho/backup/backup.sh >> /caminho/backup/backup.log 2>&1` |
| Agendamento (Windows) | Agendador de Tarefas chamando `bash backup.sh` (Git Bash/WSL) ou um `.bat` com o `mysqldump` equivalente. |

## Passo a passo
1. `cp backup.cnf.exemplo backup.cnf` e preencha (o arquivo real nunca vai para o Git).
2. `chmod 600 backup.cnf`
3. `bash backup.sh`  → gera `dumps/eventos_academicos_AAAAMMDD_HHMMSS.sql.gz`
4. `bash restaurar_teste.sh` → deve terminar com `RESTAURAÇÃO VERIFICADA`. Guarde a saída para o relatório.

## Restauração real (desastre)
```bash
mysql -u root -p -e "DROP DATABASE IF EXISTS eventos_academicos; CREATE DATABASE eventos_academicos CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
gunzip -c dumps/ARQUIVO.sql.gz | mysql -u root -p eventos_academicos
# depois: executar 06_seguranca.sql e 06_usuarios.local.sql para recriar papéis e contas
```
