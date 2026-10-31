"""Rotas adicionais de participantes, inscrições e presença.
São registradas em app.py pelo script aplicar_melhorias.py.
Usam a conexão por perfil e as tabelas ORIGINAIS do projeto.
"""
from decimal import Decimal, InvalidOperation
import mysql.connector
from flask import abort, flash, redirect, render_template, request, url_for


def registrar_rotas(app, cn, consultar, executar, mensagem_erro, perfis_permitidos):
    @app.get('/participantes')
    @perfis_permitidos('ADMIN', 'ORGANIZADOR')
    def participantes_lista():
        rows = consultar(cn(), """SELECT pa.id_pessoa, pe.nome, pe.email, pa.tipo_participante
            FROM participante pa JOIN pessoa pe ON pe.id_pessoa = pa.id_pessoa
            ORDER BY pe.nome LIMIT 300""")
        return render_template('participantes.html', rows=rows)

    @app.route('/participantes/novo', methods=['GET', 'POST'])
    @perfis_permitidos('ADMIN', 'ORGANIZADOR')
    def participante_novo():
        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip()
            matricula = request.form.get('matricula_academica', '').strip()
            tipo = request.form.get('tipo_participante', '').strip()
            tipo = request.form.get('tipo_participante', '').strip()

            if tipo == 'ALUNO' and not matricula:
                flash('Informe a matrícula do aluno.', 'erro')
                return render_template('participante_novo.html')

            if len(matricula) > 30:
                flash('A matrícula deve ter no máximo 30 caracteres.', 'erro')
                return render_template('participante_novo.html')
            if len(nome) < 3 or '@' not in email or tipo not in ('ALUNO', 'PROFESSOR', 'EXTERNO'):
                flash('Preencha nome, e-mail e tipo de participante válidos.', 'erro')
                return render_template('participante_novo.html')
            c = cn()
            try:
                c.start_transaction()
                _, pessoa_id = executar(c, 'INSERT INTO pessoa (nome, email) VALUES (%s, %s)', (nome, email))
                executar(c, 'INSERT INTO participante (id_pessoa, tipo_participante, matricula_academica) VALUES (%s, %s, %s)', (pessoa_id, tipo, matricula or None))
                c.commit()
                flash(f'Participante cadastrado! ID {pessoa_id}.', 'ok')
                return redirect(url_for('participantes_lista'))
            except mysql.connector.Error as exc:
                c.rollback()
                flash(mensagem_erro(exc), 'erro')
        return render_template('participante_novo.html')

    @app.get('/inscricoes')
    @perfis_permitidos('ADMIN', 'ORGANIZADOR')
    def inscricoes_lista():
        rows = consultar(cn(), """SELECT ia.id_participante, pe.nome AS participante,
                ia.id_atividade, a.titulo AS atividade, e.titulo AS evento,
                ia.status_inscricao, ia.percentual_presenca, ia.data_inscricao
            FROM inscricao_atividade ia
            JOIN pessoa pe ON pe.id_pessoa = ia.id_participante
            JOIN atividade a ON a.id_atividade = ia.id_atividade
            JOIN evento e ON e.id_evento = a.id_evento
            ORDER BY ia.data_inscricao DESC LIMIT 300""")
        return render_template('inscricoes.html', rows=rows)

    @app.route('/presencas', methods=['GET', 'POST'])
    @perfis_permitidos('ADMIN', 'ORGANIZADOR')
    def presencas():
        if request.method == 'POST':
            try:
                pessoa = int(request.form.get('id_participante', ''))
                atividade = int(request.form.get('id_atividade', ''))
                percentual = Decimal(request.form.get('percentual', ''))
                if not percentual.is_finite() or percentual < 0 or percentual > 100:
                    raise ValueError('Fora do intervalo')
            except (ValueError, InvalidOperation):
                flash('Informe participante, atividade e percentual entre 0 e 100.', 'erro')
                return redirect(url_for('presencas'))
            c = cn()
            try:
                qtd, _ = executar(c, """UPDATE inscricao_atividade SET percentual_presenca = %s
                    WHERE id_participante = %s AND id_atividade = %s AND status_inscricao = 'CONFIRMADA'""",
                    (percentual, pessoa, atividade))
                c.commit()
                flash('Presença registrada.' if qtd else 'Nenhuma inscrição CONFIRMADA encontrada para estes IDs.',
                      'ok' if qtd else 'erro')
            except mysql.connector.Error as exc:
                c.rollback()
                flash(mensagem_erro(exc), 'erro')
            return redirect(url_for('presencas'))
        rows = consultar(cn(), """SELECT ia.id_participante, pe.nome AS participante,
                ia.id_atividade, a.titulo AS atividade, ia.percentual_presenca
            FROM inscricao_atividade ia
            JOIN pessoa pe ON pe.id_pessoa = ia.id_participante
            JOIN atividade a ON a.id_atividade = ia.id_atividade
            WHERE ia.status_inscricao = 'CONFIRMADA'
            ORDER BY a.titulo, pe.nome LIMIT 300""")
        return render_template('presencas.html', rows=rows)
