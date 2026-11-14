"""Regressões com MySQL real. Somente em instância descartável: ALLOW_TEST_DATABASE=1."""
import concurrent.futures
import os
from pathlib import Path
import sys
import threading
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import mysql.connector
from app import app
from criar_usuario import criar
from db import conectar, consultar, executar

SENHA = 'SenhaIntegracao#2026'


def ler(sql, params=()):
    c = conectar('ADMIN')
    try:
        return consultar(c, sql, params)
    finally:
        c.close()


def gravar(sql, params=()):
    c = conectar('ADMIN')
    try:
        result = executar(c, sql, params)
        c.commit()
        return result[1]
    finally:
        c.close()


def total(sql, params=()):
    return int(next(iter(ler(sql, params)[0].values())))


def post(c, path, data=None):
    with c.session_transaction() as s:
        token = s['_csrf']
    return c.post(path, data={**(data or {}), '_csrf': token}, follow_redirects=True)


@unittest.skipUnless(os.getenv('ALLOW_TEST_DATABASE') == '1', 'Requer banco descartável e ALLOW_TEST_DATABASE=1')
class Integracao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.usuarios = {}
        for perfil in ('ADMIN', 'ORGANIZADOR', 'CONSULTA'):
            nome = 'reg_' + uuid.uuid4().hex[:16]
            criar(nome, perfil, SENHA)
            cls.usuarios[perfil] = nome
        cls.responsavel = total('SELECT MIN(id_pessoa) FROM organizador WHERE ativo=TRUE')

    @classmethod
    def tearDownClass(cls):
        for nome in cls.usuarios.values():
            gravar('UPDATE usuario_app SET ativo=FALSE WHERE login=%s', (nome,))

    def entrar(self, perfil='ADMIN'):
        c = app.test_client()
        c.get('/login')
        post(c, '/login', dict(login=self.usuarios[perfil], senha=SENHA))
        with c.session_transaction() as s:
            self.assertEqual(s.get('perfil'), perfil)
        return c

    def pessoa(self):
        p = gravar('INSERT INTO pessoa(nome,email) VALUES (%s,%s)', ('Participante regressão', uuid.uuid4().hex+'@exemplo.test'))
        gravar("INSERT INTO participante(id_pessoa,tipo_participante) VALUES (%s,'EXTERNO')", (p,))
        return p

    def atividade(self, ev, vagas=5):
        return gravar("INSERT INTO atividade(id_evento,titulo,tipo_atividade,carga_horaria,vagas) VALUES (%s,'Atividade regressão','OFICINA',2,%s)", (ev, vagas))

    def evento(self, status='ABERTO', vagas=5, limite=None):
        ev = gravar("INSERT INTO evento(id_categoria,id_instituicao_promotora,titulo,data_inicio,data_fim,modalidade,limite_participantes) VALUES (1,1,%s,DATE_ADD(NOW(),INTERVAL 60 DAY),DATE_ADD(NOW(),INTERVAL 61 DAY),'PRESENCIAL',%s)", ('Regressão '+uuid.uuid4().hex[:8], limite))
        gravar('INSERT INTO historico_status_evento(id_evento,sequencia,status,data_hora) VALUES (%s,1,%s,NOW())', (ev, status))
        gravar("INSERT INTO organizacao_evento(id_organizador,id_evento,papel,data_inicio_atuacao,responsavel_principal) VALUES (%s,%s,'Responsável',CURRENT_DATE,TRUE)", (self.responsavel, ev))
        return ev, self.atividade(ev, vagas)

    def sessao(self, atividade):
        gravar('INSERT INTO sessao_atividade(id_atividade,numero_sessao,id_sala,inicio,fim) VALUES (%s,1,1,TIMESTAMP(DATE_ADD(CURRENT_DATE,INTERVAL 60 DAY),"09:00"),TIMESTAMP(DATE_ADD(CURRENT_DATE,INTERVAL 60 DAY),"11:00"))', (atividade,))

    def inscrever(self, c, p, a, **kwargs):
        return post(c, '/operacoes/inscrever', dict(id_participante=p, id_atividade=a, **kwargs))

    def test_agenda_e_certificados_todos_perfis(self):
        for perfil in self.usuarios:
            with self.subTest(perfil=perfil):
                c = self.entrar(perfil)
                self.assertEqual(c.get('/agenda').status_code, 200)
                self.assertEqual(c.get('/certificados/validar?codigo=CERT-E01-P001-X0037').status_code, 200)

    def test_perfis_sem_privilegio(self):
        for perfil, urls in [('ORGANIZADOR', ['/usuarios/novo','/auditoria']), ('CONSULTA', ['/participantes','/presencas','/relatorio','/operacoes/abrir-evento'])]:
            c = self.entrar(perfil)
            for url in urls:
                with self.subTest(perfil=perfil, url=url):
                    self.assertEqual(c.get(url).status_code, 403)

    def test_eventos_fechados_ou_planejados_recusam_inscricao(self):
        c = self.entrar()
        p = self.pessoa()
        for status in ['PLANEJADO', 'CANCELADO', 'ENCERRADO']:
            ev, a = self.evento(status)
            self.inscrever(c, p, a)
            self.assertEqual(total('SELECT COUNT(*) FROM inscricao_atividade WHERE id_atividade=%s', (a,)), 0)

    def test_evento_iniciado_recusa_inscricao(self):
        ev, a = self.evento()
        gravar('UPDATE evento SET data_inicio=DATE_SUB(NOW(),INTERVAL 2 DAY),data_fim=DATE_SUB(NOW(),INTERVAL 1 DAY) WHERE id_evento=%s', (ev,))
        self.inscrever(self.entrar(), self.pessoa(), a)
        self.assertEqual(total('SELECT COUNT(*) FROM inscricao_atividade WHERE id_atividade=%s', (a,)), 0)

    def test_rollback_inscricao(self):
        _, a = self.evento()
        self.inscrever(self.entrar(), self.pessoa(), a, simular_falha='on')
        self.assertEqual(total('SELECT COUNT(*) FROM inscricao_atividade WHERE id_atividade=%s', (a,)), 0)

    def simultaneas(self, requests):
        inicio = threading.Barrier(len(requests))
        def enviar(item):
            c, url, dados = item
            inicio.wait(timeout=15)
            return post(c, url, dados).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(requests)) as pool:
            resultados = list(pool.map(enviar, requests))
        self.assertTrue(all(status == 200 for status in resultados), resultados)

    def test_ultima_vaga_concorrente(self):
        _, a = self.evento(vagas=1)
        self.simultaneas([(self.entrar(), '/operacoes/inscrever', dict(id_participante=self.pessoa(),id_atividade=a,pausa=1)) for _ in range(2)])
        self.assertEqual(total("SELECT COUNT(*) FROM inscricao_atividade WHERE id_atividade=%s AND status_inscricao='CONFIRMADA'", (a,)), 1)
        self.assertEqual(total("SELECT COUNT(*) FROM inscricao_atividade WHERE id_atividade=%s AND status_inscricao='LISTA_ESPERA'", (a,)), 1)

    def test_rn22_concorrente_entre_eventos(self):
        _, a = self.evento()
        _, b = self.evento()
        self.sessao(a)
        self.sessao(b)
        p = self.pessoa()
        self.simultaneas([(self.entrar(), '/operacoes/inscrever', dict(id_participante=p,id_atividade=x,pausa=1)) for x in (a,b)])
        self.assertEqual(total("SELECT COUNT(*) FROM inscricao_atividade WHERE id_participante=%s AND status_inscricao='CONFIRMADA'", (p,)), 1)

    def test_limite_evento_concorrente(self):
        ev, a = self.evento(limite=1)
        b = self.atividade(ev)
        self.simultaneas([(self.entrar(), '/operacoes/inscrever', dict(id_participante=self.pessoa(),id_atividade=x)) for x in (a,b)])
        self.assertEqual(total("SELECT COUNT(DISTINCT ia.id_participante) FROM inscricao_atividade ia JOIN atividade a USING(id_atividade) WHERE a.id_evento=%s AND ia.status_inscricao='CONFIRMADA'", (ev,)), 1)

    def test_limite_evento_conta_pessoas_distintas(self):
        ev, a = self.evento(limite=1)
        b = self.atividade(ev)
        c, p = self.entrar(), self.pessoa()
        self.inscrever(c, p, a)
        self.inscrever(c, p, b)
        self.assertEqual(total("SELECT COUNT(*) FROM inscricao_atividade WHERE id_participante=%s AND status_inscricao='CONFIRMADA'", (p,)), 2)

    def test_minimo_de_certificacao_invalido(self):
        ev, _ = self.evento()
        c = self.entrar()
        for minimo in ['-1','0','74.99','101','NaN','Infinity','-Infinity','abc']:
            with self.subTest(minimo=minimo):
                r = post(c, '/operacoes/encerrar-evento', dict(id_evento=ev,minimo=minimo))
                self.assertEqual(r.status_code, 200)
                self.assertEqual(total('SELECT COUNT(*) FROM historico_status_evento WHERE id_evento=%s', (ev,)), 1)
                self.assertEqual(total('SELECT COUNT(*) FROM certificado WHERE id_evento=%s', (ev,)), 0)

    def test_baixa_presenca_sem_certificado(self):
        ev, a = self.evento()
        c, p = self.entrar(), self.pessoa()
        self.inscrever(c, p, a)
        post(c, '/presencas', dict(id_participante=p,id_atividade=a,percentual=50))
        post(c, '/operacoes/encerrar-evento', dict(id_evento=ev,minimo=75))
        self.assertEqual(total('SELECT COUNT(*) FROM certificado WHERE id_evento=%s', (ev,)), 0)

    def test_presenca_bloqueada_apos_certificado(self):
        ev, a = self.evento()
        c, p = self.entrar(), self.pessoa()
        self.inscrever(c, p, a)
        post(c, '/presencas', dict(id_participante=p,id_atividade=a,percentual=90))
        post(c, '/operacoes/encerrar-evento', dict(id_evento=ev,minimo=75))
        self.assertEqual(total('SELECT COUNT(*) FROM certificado WHERE id_evento=%s', (ev,)), 1)
        post(c, '/presencas', dict(id_participante=p,id_atividade=a,percentual=0))
        self.assertEqual(total('SELECT percentual_presenca FROM inscricao_atividade WHERE id_participante=%s AND id_atividade=%s', (p,a)), 90)

    def test_encerramento_e_presenca_concorrentes(self):
        ev, a = self.evento()
        c, p = self.entrar(), self.pessoa()
        self.inscrever(c, p, a)
        post(c, '/presencas', dict(id_participante=p,id_atividade=a,percentual=90))
        self.simultaneas([(self.entrar(),'/presencas',dict(id_participante=p,id_atividade=a,percentual=0)),
                         (self.entrar(),'/operacoes/encerrar-evento',dict(id_evento=ev,minimo=75))])
        self.assertEqual(total('SELECT COUNT(*) FROM certificado ce JOIN atividade a ON a.id_evento=ce.id_evento JOIN inscricao_atividade ia ON ia.id_atividade=a.id_atividade AND ia.id_participante=ce.id_participante WHERE ce.id_evento=%s AND ia.percentual_presenca<75', (ev,)), 0)

    def test_revogacao_de_sessao(self):
        nome = 'reg_' + uuid.uuid4().hex[:16]
        criar(nome, 'ORGANIZADOR', SENHA)
        c = app.test_client()
        c.get('/login')
        post(c, '/login', dict(login=nome,senha=SENHA))
        gravar("UPDATE usuario_app SET ativo=FALSE,perfil='CONSULTA' WHERE login=%s", (nome,))
        self.assertEqual(c.get('/participantes').status_code, 302)
        with c.session_transaction() as s:
            self.assertNotIn('id_usuario', s)

    def test_csrf_unicode_e_ausente(self):
        c = self.entrar()
        self.assertEqual(c.post('/presencas', data={}).status_code, 400)
        self.assertEqual(c.post('/presencas', data={'_csrf':'á'}).status_code, 400)

    def test_criacao_evento_exige_responsavel(self):
        c = self.entrar()
        titulo = 'Evento UI ' + uuid.uuid4().hex[:8]
        datas = ler('SELECT DATE_ADD(NOW(),INTERVAL 60 DAY) AS inicio,DATE_ADD(NOW(),INTERVAL 61 DAY) AS fim')[0]
        data = dict(id_categoria=1,id_instituicao_promotora=1,titulo=titulo,data_inicio=str(datas['inicio']),data_fim=str(datas['fim']),modalidade='ONLINE',gratuito='on',valor_inscricao=0)
        post(c, '/crud/evento/novo', data)
        self.assertEqual(total('SELECT COUNT(*) FROM evento WHERE titulo=%s', (titulo,)), 0)
        post(c, '/crud/evento/novo', {**data,'id_responsavel':self.responsavel})
        ev = total('SELECT id_evento FROM evento WHERE titulo=%s', (titulo,))
        self.assertEqual(total('SELECT COUNT(*) FROM organizacao_evento WHERE id_evento=%s AND responsavel_principal=TRUE', (ev,)), 1)
        self.assertEqual(c.get(f'/crud/evento/{ev}/editar').status_code, 200)

    def test_abertura_exige_atividade_e_responsavel(self):
        c = self.entrar()
        ev, a = self.evento(status='PLANEJADO')
        gravar('DELETE FROM atividade WHERE id_atividade=%s', (a,))
        post(c, '/operacoes/abrir-evento', dict(id_evento=ev))
        self.assertEqual(total('SELECT COUNT(*) FROM historico_status_evento WHERE id_evento=%s', (ev,)), 1)
        self.atividade(ev)
        gravar('UPDATE organizacao_evento SET responsavel_principal=FALSE WHERE id_evento=%s', (ev,))
        post(c, '/operacoes/abrir-evento', dict(id_evento=ev))
        self.assertEqual(total('SELECT COUNT(*) FROM historico_status_evento WHERE id_evento=%s', (ev,)), 1)
        gravar('UPDATE organizacao_evento SET responsavel_principal=TRUE WHERE id_evento=%s', (ev,))
        post(c, '/operacoes/abrir-evento', dict(id_evento=ev))
        self.assertEqual(ler('SELECT status_atual FROM vw_evento_status_atual WHERE id_evento=%s', (ev,))[0]['status_atual'], 'ABERTO')

    def test_rn18_edicao_pela_interface(self):
        ev, a = self.evento()
        self.sessao(a)
        post(self.entrar(),f'/crud/atividade/{a}/editar',dict(id_evento=ev,titulo='Acima capacidade',tipo_atividade='OFICINA',carga_horaria=2,vagas=1000))
        self.assertEqual(total('SELECT vagas FROM atividade WHERE id_atividade=%s', (a,)), 5)

    def test_rn18_sql_direto(self):
        _, a = self.evento()
        self.sessao(a)
        with self.assertRaises(mysql.connector.Error) as exc:
            gravar('UPDATE atividade SET vagas=1000 WHERE id_atividade=%s', (a,))
        self.assertEqual(exc.exception.errno, 1644)
        with self.assertRaises(mysql.connector.Error):
            gravar('UPDATE sala SET capacidade=1 WHERE id_sala=1')

    def test_rn18_sessao_invalida(self):
        _, a = self.evento(vagas=1000)
        with self.assertRaises(mysql.connector.Error) as exc:
            self.sessao(a)
        self.assertEqual(exc.exception.errno, 1644)

    def test_exclusao_nao_remove_ultima_atividade_aberta(self):
        _, a = self.evento()
        post(self.entrar(), f'/crud/atividade/{a}/excluir')
        self.assertEqual(total('SELECT COUNT(*) FROM atividade WHERE id_atividade=%s', (a,)), 1)

    def test_exclusao_nao_remove_atividade_encerrada(self):
        _, a = self.evento(status='ENCERRADO')
        post(self.entrar(), f'/crud/atividade/{a}/excluir')
        self.assertEqual(total('SELECT COUNT(*) FROM atividade WHERE id_atividade=%s', (a,)), 1)

    def test_cadastro_publico_sem_elevacao(self):
        c = app.test_client()
        c.get('/cadastro')
        nome = 'reg_' + uuid.uuid4().hex[:16]
        post(c, '/cadastro', dict(login=nome,senha=SENHA,confirmar=SENHA,perfil='ADMIN'))
        self.assertEqual(ler('SELECT perfil FROM usuario_app WHERE login=%s', (nome,))[0]['perfil'], 'CONSULTA')
        self.assertEqual(c.get('/auditoria').status_code, 403)


if __name__ == '__main__':
    unittest.main(verbosity=2)
