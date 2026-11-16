import copy
from pathlib import Path
import unittest
import catalog
import specs

class SourceReviewTests(unittest.TestCase):
    def test_partial_review_never_approves_other_fields_in_same_candidate(self):
        legacy=specs.load('watches.json');record=specs.load('imports/module-3495.json')[0]
        field=next(iter(record['specs']))
        decision={'candidate_sha256':specs.digest(record),'reviewed_by':'test','note':'Only one field checked','fields':[field]}
        result=specs.build(legacy,[record],[decision])['modules'][record['id']]['specs']
        self.assertEqual({k for k,f in result.items() if f['status']=='verified'},{field})
        self.assertTrue(all(f['status']=='pending_review' for k,f in result.items() if k!=field))

    def test_invalid_or_unmatched_field_scope_is_rejected(self):
        record=specs.load('imports/module-3495.json')[0]
        for fields in [[],['not_a_record_field'],['alarm_count','alarm_count'],'alarm_count']:
            with self.assertRaises(ValueError):
                specs.build(specs.load('watches.json'),[record],[{'candidate_sha256':specs.digest(record),'reviewed_by':'test','note':'test','fields':fields}])

    def test_automated_reviews_are_bound_to_current_proof_and_exact_fields(self):
        root=Path('.');reviews=specs.load('reviews.json');records=[r for p in sorted((root/'imports').glob('*.json')) for r in specs.load(p)]
        catalog.validate_source_reviews(root,records,reviews)
        changed=copy.deepcopy(reviews);changed[0]['evidence_sha256']='0'*64
        with self.assertRaises(ValueError):catalog.validate_source_reviews(root,records,changed)
        changed=copy.deepcopy(reviews);changed[0]['fields'].append('release_date')
        with self.assertRaises(ValueError):catalog.validate_source_reviews(root,records,changed)

    def test_first_pass_has_33_checked_fields_but_not_checked_modules_or_days(self):
        data=specs.load('data/catalog.json');checked=[]
        for bucket in ['models','modules']:
            for key,row in data[bucket].items():
                checked.extend((bucket,key,field) for field,fact in row['specs'].items() if fact['status']=='verified')
        self.assertEqual(len(checked),33)
        self.assertEqual({key for _,key,_ in checked},{'GW-M5610-1','GW-M5610U-1','GW-5000-1','GW-5000U-1'})
        self.assertFalse(any(bucket=='modules' or field in ['module_id','release_date','color'] for bucket,_,field in checked))

    def test_magazine_discoveries_are_not_specification_or_prefix_expansion_claims(self):
        leads=specs.load('research/publication-discoveries-2026-11-16.json');library=specs.load('data/model-references.json');data=specs.load('data/catalog.json')
        self.assertEqual(len(leads['models']),4)
        for row in leads['models']:
            self.assertNotIn(row['id'],data['models'])
            reference=library['models'][row['id']]
            self.assertEqual(reference['status'],'machine_candidate')
            self.assertEqual(reference['observations'][0]['role'],'publication_discovery')
        self.assertNotIn('GST-W1000D-2AJF',[row['id'] for row in leads['models']])
        self.assertIn('GST-W1000AD-2AJF',[row['id'] for row in leads['models']])

    def test_later_nonoverlapping_review_keeps_prior_field_decision_unchanged(self):
        record=specs.load('imports/module-3495.json')[0];fields=list(record['specs'])
        first={'candidate_sha256':specs.digest(record),'reviewed_by':'first','note':'First pass','fields':[fields[0]]}
        second={'candidate_sha256':specs.digest(record),'reviewed_by':'second','note':'Later pass','fields':[fields[1]]}
        earlier=specs.build(specs.load('watches.json'),[record],[first])
        later=specs.build(specs.load('watches.json'),[record],[first,second])
        catalog.preserve_verified(earlier,later)
        self.assertEqual(later['modules'][record['id']]['specs'][fields[0]]['review'],first)
        self.assertEqual(later['modules'][record['id']]['specs'][fields[1]]['review'],second)

    def test_overlapping_reviews_are_rejected(self):
        record=specs.load('imports/module-3495.json')[0];field=next(iter(record['specs']))
        decision={'candidate_sha256':specs.digest(record),'reviewed_by':'test','note':'test','fields':[field]}
        with self.assertRaises(ValueError):specs.build(specs.load('watches.json'),[record],[decision,dict(decision,note='replacement')])
