"""Policy-edge association validation: python -m unittest discover -s . -p 'test_*.py'."""
import copy
import tempfile
import unittest
from pathlib import Path
from openpyxl import Workbook
import build_network as app

ROOT=Path(__file__).resolve().parent

class PolicyBubbleTests(unittest.TestCase):
    def network(self):
        return app.read_workbook(ROOT/'bc_adaptation_network_input 1.0.xlsx')

    def fixture(self, path, outcome, change=None):
        book=Workbook();s=book.active;s.title='Policies'
        s.append(['Title block'])
        s.append(['Entry','Policy','Reviewed source','Failures addressed (codes)','Failures potentially worsened (codes)','Enablers supported (codes)','Conditions potentially constrained (codes)'])
        s.append([1,'Example policy','https://example.org/policy','F01','F01','E02','None identified'])
        t=book.create_sheet('Policy-outcome links')
        t.append(['Policy entry','Policy','Outcome ID','Outcome statement','Relationship','Mechanism and limits'])
        t.append([1,'Example policy',outcome['id'],outcome['label'],'Direct mechanism','Fixture mechanism'])
        if change:change(book)
        book.save(path)

    def test_real_policy_data_preserve_edges_and_correct_policy_identity(self):
        data=self.network();before=copy.deepcopy(data['edges'])
        app.add_policies(data,ROOT/'bc_policy_failures_and_enablers.xlsx')
        self.assertEqual([{k:e[k] for k in ('source','target')} for e in data['edges']],before)
        self.assertEqual(len(data['policies']),99)
        dike=next(e for e in data['edges'] if (e['source'],e['target'])==('O022','F27'))
        self.assertIn({'policy':'P009','link':'P009:O022','roles':['addresses']},dike['policies'])
        enabler=next(e for e in data['edges'] if (e['source'],e['target'])==('O022','E09'))
        self.assertTrue(any(a['policy']=='P009' and 'supports' in a['roles'] for a in enabler['policies']))
        p={p['id']:p for p in data['policies']}
        self.assertEqual(p['P054']['title'],p['P065']['title'])
        self.assertNotEqual(p['P054']['source'],p['P065']['source'])
        self.assertIn('P043:O028',data['policy_stats']['unplaced_outcome_links'])

    def test_two_roles_share_one_bubble_and_do_not_invent_edges(self):
        data=self.network();outcome=next(n for n in data['nodes'] if n['id']=='O001')
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'policies.xlsx';self.fixture(path,outcome);app.add_policies(data,path)
        edge=next(e for e in data['edges'] if (e['source'],e['target'])==('O001','F01'))
        self.assertEqual(len(edge['policies']),1)
        self.assertEqual(edge['policies'][0]['roles'],['addresses','potentially_worsens'])
        self.assertFalse(any(e['target']=='E02' and e['source']=='O001' for e in data['edges']))
        # An E02 policy match cannot create an O001–E02 edge to carry a bubble.
        self.assertEqual(len(data['edges']),903)

    def test_bad_policy_outcome_pairs_fail_before_output(self):
        n=next(n for n in self.network()['nodes'] if n['id']=='O001')
        cases=[('unknown policy',lambda w:setattr(w['Policy-outcome links']['A2'],'value',999),'undefined policy'),
               ('wrong statement',lambda w:setattr(w['Policy-outcome links']['D2'],'value','Not this outcome'),'outcome ID/statement mismatch'),
               ('wrong title',lambda w:setattr(w['Policy-outcome links']['B2'],'value','Wrong policy'),'title does not match'),
               ('duplicate pair',lambda w:w['Policy-outcome links'].append([1,'Example policy',n['id'],n['label'],'Direct mechanism','Duplicate']),'duplicate pair'),
               ('invalid code',lambda w:setattr(w['Policies']['D3'],'value','F99'),'undefined policy codes')]
        with tempfile.TemporaryDirectory() as d:
            for name,change,error in cases:
                with self.subTest(name=name):
                    path=Path(d)/'policy.xlsx';self.fixture(path,n,change)
                    with self.assertRaisesRegex(ValueError,error):app.add_policies(self.network(),path)

if __name__=='__main__':unittest.main()
