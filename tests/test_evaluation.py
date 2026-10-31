from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.pipeline import metrics

class EvaluationTests(unittest.TestCase):
    def test_constant_scores_do_not_claim_ranking_lift(self):
        # Outcomes are deliberately ordered to expose a tie-ordering artifact.
        y=np.array([1]*20+[0]*80)
        result=metrics(y,np.full(100,.2))
        self.assertAlmostEqual(result['average_precision'],.2)
        self.assertAlmostEqual(result['top20_purchase_capture'],.2)
        self.assertAlmostEqual(result['roc_auc'],.5)

    def test_perfect_ranking_and_probabilities(self):
        y=np.array([0,1,0,1,0,0,0,0,0,0])
        result=metrics(y,y.astype(float))
        self.assertEqual(result['average_precision'],1.)
        self.assertEqual(result['brier_score'],0.)
        self.assertEqual(result['top20_purchase_capture'],1.)

if __name__=='__main__': unittest.main()
