import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from coreference_resolution_claim_audit.audit import audit, evidence, main, matches, COREFERENCE, NOCOREFERENCE, GENERIC_NAMES

class AuditTests(unittest.TestCase):
    def test_phrase_oracle(self):
        self.assertEqual(list(COREFERENCE), ['coreference resolution', 'coreference', 'coreferences', 'coref', 'coreference model', 'coreference models', 'coreference system', 'coreference pipeline', 'coreference feature', 'coreference capability', 'coreference support', 'supports coreference resolution', 'provides coreference resolution', 'performs coreference resolution', 'coreference resolution feature', 'coreference resolution capability', 'coreference resolution system', 'coreference resolution pipeline', 'coreference resolution step', 'coreference resolution process', 'automatic coreference resolution', 'auto coreference resolution', 'coreference resolution tool', 'coreference resolution engine', 'coreference resolution api', 'coreference tool', 'coreference engine', 'coreference api', 'resolves coreferences', 'resolve coreferences', 'resolving coreferences', 'coreference chains', 'coref chains', 'coreference chain', 'coref chain', 'coref resolution', 'coreference resolver', 'coref resolver', 'coreference clustering', 'mention coreference', 'pronoun resolution', 'resolves pronouns', 'anaphora resolution', 'coreference detection', 'detects coreferences', 'coreference linking', 'coreference prediction', 'coreference annotation', 'coreference resolution support', 'supports coreference'])
        self.assertEqual(list(NOCOREFERENCE), ['does not resolve coreferences', 'do not resolve coreferences', "doesn't resolve coreferences", "don't resolve coreferences", 'no coreference resolution', 'without coreference resolution', 'never resolves coreferences', 'does not perform coreference resolution', 'never performs coreference resolution', 'coreference resolution not supported', 'coreference resolution unsupported', 'no coreference support', 'lacks coreference resolution', 'missing coreference resolution', 'coreference resolution disabled', 'no coreference', 'without coreference resolution support', 'does not provide coreference resolution', 'does not support coreference resolution', 'no automatic coreference resolution', 'coreference resolution not available', 'no coreference resolution support', 'does not resolve coreference', 'without a coreference resolver'])

    def test_generic_oracle(self):
        self.assertEqual(list(GENERIC_NAMES), ['resolve_coreference', 'resolve_coreferences', 'coreference_resolve', 'get_coref_chains', 'get_coreference_chains', 'find_coreferences', 'find_coreference', 'detect_coreference', 'detect_coreferences', 'coref_resolve', 'coref_predict', 'predict_coref', 'extract_coreferences', 'extract_coreference', 'resolve_pronouns', 'link_coreferences', 'cluster_coreferences', 'get_coref_clusters', 'coreference_resolution', 'coref_resolution', 'resolve_coref', 'resolve_mentions', 'link_mentions', 'cluster_mentions'])

    def fixture(self, readme='', code='', extra=None, flags=()):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'README.md').write_text(readme)
            (root/'app.py').write_text(code)
            for name, text in (extra or {}).items():
                p = root/name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = main(['audit', str(root)] + list(flags))
            return status, out.getvalue()

    def test_pairs(self):
        cases = [
            'from allennlp.predictors import Predictor as P; p=P.from_path("COREF-model"); p.predict("x")',
            'import allennlp; allennlp.predictors.Predictor.from_path("coref").predict("x")',
            'import fastcoref as fc; m=fc.LingMessCoref(); m.predict("x")',
            'from fastcoref import LingMessCoref; LingMessCoref().predict("x")',
            'from fastcoref import FCoref as F; m=F(); m.predict("x")',
            'import fastcoref; fastcoref.FCoref().predict("x")',
            'nlp.add_pipe("coreferee"); doc._.coref_chains',
            'import neuralcoref as nc; nc.add_to_pipe(nlp); doc._.coref_clusters',
            'from neuralcoref import add_to_pipe as add; add(nlp); doc._.coref_clusters',
        ]
        for code in cases:
            with self.subTest(code=code): self.assertTrue(evidence(code))

    def test_generics(self):
        for name in GENERIC_NAMES:
            for code in ('x.'+name+'()', 'from unknown import '+name+' as run; run()'):
                with self.subTest(code=code): self.assertTrue(evidence(code))

    def test_rejections(self):
        cases = [
            'import fastcoref; import neuralcoref; from allennlp.predictors import Predictor',
            'from allennlp.predictors import Predictor; p=Predictor.from_path("generic"); p.predict("x")',
            'doc.ents', 'pipeline("ner", model="ner")', 'm=NER(); m.predict("x")',
            'token.head; token.dep_', 'p=Parser(); p.parse("x")',
            'constituency.parse("x")', 'pos.tag("x")', 'tokenizer.tokenize("x")',
            'stemmer.stem("x")', 'lemmatizer.lemmatize("x")', 'sentiment.predict("x")',
            'summarizer.summarize("x")', 'translator.translate("x")',
            'from fastcoref import LingMessCoref; m=LingMessCoref()',
            'from fastcoref import FCoref; m=FCoref()',
            'from allennlp.predictors import Predictor; p=Predictor.from_path("coref")',
            'nlp.add_pipe("coreferee")', 'import neuralcoref; neuralcoref.add_to_pipe(nlp)',
            '"coreference coref" # coref', '"""coreference"""',
            'from unknown import resolve_coreference; resolve_coreference',
            'import subprocess; subprocess.run(["coref", "text"])',
            'from fastcoref import FCoref; m=FCoref(); other.predict("x")',
            'resolve_coreference()', 'this is invalid python!',
        ]
        for code in cases:
            with self.subTest(code=code): self.assertFalse(evidence(code))

    def test_shadowing(self):
        cases = [
            'from x import resolve_coreference\ndef resolve_coreference(): pass\nresolve_coreference()',
            'from fastcoref import LingMessCoref\nclass LingMessCoref: pass\nm=LingMessCoref(); m.predict()',
            'from fastcoref import FCoref\nclass FCoref: pass\nFCoref().predict()',
            'from allennlp.predictors import Predictor\nclass Predictor: pass\nPredictor.from_path("coref").predict()',
            'from neuralcoref import add_to_pipe\ndef add_to_pipe(x): pass\nadd_to_pipe(nlp); doc._.coref_clusters',
            'def add_pipe(x): pass\nnlp.add_pipe("coreferee"); doc._.coref_chains',
        ]
        for code in cases:
            with self.subTest(code=code): self.assertFalse(evidence(code))

    def test_split_modules(self):
        status, out = self.fixture('coreference', 'from fastcoref import FCoref; m=FCoref()', {'other.py': 'm.predict()'})
        self.assertEqual(status, 2)

    def test_matching(self):
        self.assertEqual(matches('coreference resolution', COREFERENCE)[0], ['coreference resolution'])
        self.assertEqual(self.fixture('does not resolve coreferences')[0], 0)
        self.assertEqual(self.fixture('COREFERENCE')[0], 2)
        self.assertEqual(self.fixture('```text\ncoreference\n```')[0], 0)
        self.assertEqual(self.fixture('`coreference`')[0], 2)
        self.assertEqual(matches('pronoun-resolution', COREFERENCE)[0], [])

    def test_cli_good(self):
        self.assertEqual(self.fixture('coreference', 'x.resolve_mentions()'), (0, 'PASS\n'))

    def test_cli_bad(self):
        status, out = self.fixture('coreference')
        self.assertEqual(status, 2)
        self.assertIn('HIGH documented-coreference-resolution-claim-false', out)

    def test_cli_test_only(self):
        extra = {'tests/sample.md': 'coreference'}
        status, out = self.fixture(extra=extra)
        self.assertEqual(status, 0)
        self.assertIn('MEDIUM', out)
        self.assertEqual(self.fixture(extra=extra, flags=['--fail-on', 'medium'])[0], 2)

    def test_cli_denial(self):
        status, out = self.fixture('no coreference resolution', 'x.resolve_mentions()')
        self.assertEqual(status, 2)
        self.assertIn('HIGH documented-no-coreference-resolution-claim-false', out)

    def test_cli_no_claim(self):
        self.assertEqual(self.fixture('A useful tool.'), (0, 'PASS\n'))

    def test_cli_json(self):
        status, out = self.fixture('coreference', flags=['--json'])
        f = json.loads(out)[0]
        self.assertEqual(status, 2)
        self.assertEqual(f['verdict'], 'FAIL')
        self.assertTrue(f['message'])

    def test_cli_ignore(self):
        self.assertEqual(self.fixture(extra={'docs/claim.md': 'coreference'}, flags=['--ignore', 'docs/'])[0], 0)

    def test_cli_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            main(['--version'])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), '0.1.0')

    def test_readme(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(self.fixture((root/'README.md').read_text()), (0, 'PASS\n'))

    def test_io_and_usage(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['audit', '/nonexistent-r142-directory']), 1)
            with self.assertRaises(SystemExit) as cm: main(['audit', '--unknown'])
        self.assertEqual(cm.exception.code, 1)

    def test_virtualenv_excluded(self):
        status, out = self.fixture('coreference', extra={
            'custom-env/pyvenv.cfg': 'home = /usr/bin',
            'custom-env/lib/model.py': 'x.resolve_mentions()',
        })
        self.assertEqual(status, 2)

    def test_verbose(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(self.fixture(flags=['--verbose'])[0], 0)
        self.assertIn('scope:', err.getvalue())

if __name__ == '__main__':
    unittest.main()
