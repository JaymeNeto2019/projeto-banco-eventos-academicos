"""Configuração privada não deve ser publicada nem substituída por engano."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('configurar_ambiente', ROOT/'configurar_ambiente.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)


class Configuracao(unittest.TestCase):
    def test_geracao_correspondente_e_rotacao(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
            env, sql = config.gerar(tmp, porta=33317)
            before = env.read_text(encoding='utf-8')
            values = dict(line.split('=',1) for line in before.splitlines() if '=' in line)
            self.assertEqual(len(values['FLASK_SECRET_KEY']), 64)
            for perfil, usuario, _ in config.CONTAS:
                senha = values['DB_PASS_'+perfil]
                self.assertGreaterEqual(len(senha), 48)
                self.assertIn(f"ALTER USER '{usuario}'@'localhost' IDENTIFIED BY '{senha}'", sql.read_text(encoding='utf-8'))
            with self.assertRaises(FileExistsError):
                config.gerar(tmp)
            self.assertEqual(env.read_text(encoding='utf-8'), before)
            config.gerar(tmp, rotacionar=True)
            self.assertNotEqual(env.read_text(encoding='utf-8'), before)

    def test_git_nao_rastreia_arquivos_privados(self):
        files = subprocess.check_output(['git','ls-files','-z'], cwd=ROOT).decode().split('\0')
        self.assertNotIn('.env', files)
        self.assertFalse(any(n.endswith('.local.sql') for n in files))
        self.assertFalse(any(n.startswith('.vscode/') and n.endswith('.zip') for n in files))

    def test_rejeita_host_externo_ou_porta_invalida(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as tmp:
            for kwargs in [dict(host='db.example.org'), dict(porta=0), dict(porta=65536)]:
                with self.assertRaises(ValueError):
                    config.gerar(tmp, **kwargs)


if __name__ == '__main__':
    unittest.main()
