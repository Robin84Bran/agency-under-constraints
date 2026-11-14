"""Synthetic-only integration checks; never evaluate the archived study here."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wop_analysis
from tests.test_policy import item

ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def test_offline_loader_and_ambiguous_start(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=Path(directory)
            saved=root/'collection'/'calls'/'qwen7b';saved.mkdir(parents=True)
            name=hashlib.sha256(b'a|trace').hexdigest()
            record=dict(model='qwen7b',id='a',view='trace',status='OK',verdict=True,
                        usage=dict(input_tokens=8,output_tokens=2),seconds=.1,usd=0)
            (saved/(name+'.json')).write_text(json.dumps(record))
            (saved/(name+'.start.json')).write_text(json.dumps(record))
            other=hashlib.sha256(b'b|trace').hexdigest()
            record['id']='b'
            (saved/(other+'.start.json')).write_text(json.dumps(record))
            loaded=wop_analysis._read_calls(root)
            self.assertEqual(len(loaded),2)
            self.assertEqual(loaded[('qwen7b','b','trace')]['status'],'UNCERTAIN')
            self.assertEqual(loaded[('qwen7b','a','trace')]['call']['input_tokens'],8)

    def test_gzip_rebuild_byte_exact(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=Path(directory)
            for name in ['a.gz','b.gz']:
                with wop_analysis._gzip_text(root/name) as handle: handle.write('fixture\n')
            self.assertEqual((root/'a.gz').read_bytes(),(root/'b.gz').read_bytes())

    def test_append_only_synthetic_renderer(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root=Path(directory)
            (root/'imported').mkdir()
            population=[item('HA/a'),item('HA/b',breach=False,trace=False),dict(item('Rebel/a'),source='Rebel'),dict(item('Rebel/b',breach=False,trace=False),source='Rebel')]
            (root/'imported'/'dataset.json').write_text(json.dumps(dict(items=population,cohorts={})))
            (root/'freeze.json').write_text('{}')
            records={(model,x['id'],view):dict(status='OK',verdict=x['breach'],call=dict(input_tokens=8,output_tokens=2,seconds=.1,usd=0))
                     for x in population for model in wop_analysis.MODELS for view in ('final','trace')}
            primary=dict(superiority='superiority criterion not met',recall_difference=0,recall_difference_ci95=[0,0],
                         yield_difference=0,yield_difference_ci95=[0,0],limitation='synthetic fixture')
            collection=dict(incomplete=False,replay_exactness={},cost_limits='synthetic')
            output=root/'results'
            with patch.object(wop_analysis,'_verify_provenance',return_value={}), \
                 patch.object(wop_analysis,'_read_calls',return_value=records), \
                 patch.object(wop_analysis,'collection_summary',return_value=collection), \
                 patch.object(wop_analysis,'primary_statistics',return_value=primary), \
                 patch.object(wop_analysis,'ORDER_SEEDS',(46000,)), \
                 patch.object(wop_analysis,'GRID',((1,2),)):
                result=wop_analysis.analyze(root,output)
                self.assertGreater(result['tables'],0)
                with self.assertRaises(FileExistsError): wop_analysis.analyze(root,output)
            for name in ['primary.json','tables.json','tables.csv','RESULTS.md','predictions.json','manifest.json']:
                self.assertTrue((output/name).is_file())
            with gzip.open(output/'orders_routes.jsonl.gz','rt') as handle:
                header=json.loads(next(handle));first=json.loads(next(handle))
            self.assertIn('route_fields',header)
            self.assertEqual(len(first['routes'][0]),len(header['route_fields']))
            predictions=json.loads((output/'predictions.json').read_text())
            self.assertTrue(any(x['id']=='LP1/qwen7b' for x in predictions))
            self.assertTrue(any(x['id']=='LP5/llama8b' and x['status']=='UNKNOWN' for x in predictions))
