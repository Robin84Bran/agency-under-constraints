import copy
import unittest
from rg_collect import Stop
from rg_freeze import push_record

COMMIT = '059a0258b86359d2564fd1e09bf4a4867b23353b'
ACTIVITY = {'activity_type':'push', 'after':COMMIT, 'before':'4'*40,
            'ref':'refs/heads/main', 'timestamp':'2026-11-11T09:13:51Z', 'id':49834798845}
EVENT = {'type':'PushEvent', 'repo':{'name':'Robin84Bran/research'},
         'payload':{'head':COMMIT, 'ref':ACTIVITY['ref']},
         'created_at':ACTIVITY['timestamp'], 'id':'server-event-id'}


class PushRecordTests(unittest.TestCase):
    def test_both_server_shapes(self):
        for event in (ACTIVITY, EVENT):
            self.assertEqual(push_record(event, COMMIT), (ACTIVITY['ref'], ACTIVITY['timestamp']))
        event = copy.deepcopy(EVENT)
        event['payload']['after'] = event['payload'].pop('head')
        self.assertEqual(push_record(event, COMMIT)[0], ACTIVITY['ref'])

    def test_activity_rejects_wrong_or_missing_required_fields(self):
        cases = [{'activity_type':'force_push'}, {'after':'b'*40}, {'ref':None}, {'ref':''},
                 {'ref':'main'}, {'ref':'refs/heads/'}, {'timestamp':None}, {'timestamp':'invalid'},
                 {'timestamp':'2026-01-01T00:00:00'}, {'timestamp':'2999-01-01T00:00:00Z'}, {'id':None}]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(Stop):
                push_record({**ACTIVITY, **change}, COMMIT)
        for key in ('activity_type', 'after', 'ref', 'timestamp'):
            record = dict(ACTIVITY); del record[key]
            with self.subTest(missing=key), self.assertRaises(Stop):
                push_record(record, COMMIT)

    def test_commit_and_event_repository(self):
        for commit in ('x'*40, 'a'*39, None):
            with self.subTest(commit=commit), self.assertRaises(Stop):
                push_record(ACTIVITY, commit)
        event = copy.deepcopy(EVENT); event['repo']['name'] = 'another/research'
        with self.assertRaises(Stop):
            push_record(event, COMMIT)
        event = copy.deepcopy(EVENT); event['payload']['head'] = 'b'*40
        with self.assertRaises(Stop):
            push_record(event, COMMIT)


