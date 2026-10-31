"""Boundary checks for eligibility, re-adds, purging and purchase labels."""
from pathlib import Path
import re
import tempfile
import unittest
import duckdb

ROOT=Path(__file__).resolve().parents[1]

class JourneyTests(unittest.TestCase):
    def test_decision_boundaries_and_cart_state(self):
        with tempfile.TemporaryDirectory(prefix='journey-fixture-') as tmp:
            con=duckdb.connect()
            carts=[(-1,-1,'2022-06-23 00:00:00'),(-1,-1,'2022-12-08 00:00:00')]
            buys=[(-1,-1,'2022-06-23 00:00:00'),(-1,-1,'2022-12-08 00:00:00')]
            removals=[(-1,-1,'2022-06-23 00:00:00'),(-1,-1,'2022-12-08 00:00:00')]
            carts += [(i,i,'2022-08-01 00:00:00') for i in [1,2,3,4,5,6,7,10]]
            carts += [(3,3,'2022-08-01 23:00:00'),(7,7,'2022-08-01 23:00:00'),
                      (8,8,'2022-07-01 00:00:00'),(9,9,'2022-12-05 00:00:00'),
                      (10,10,'2022-08-01 00:00:00')]
            buys += [(1,1,'2022-08-02 00:00:00'),(3,3,'2022-08-03 00:00:00'),
                     (4,4,'2022-08-09 00:00:00'),(5,5,'2022-08-09 00:00:01')]
            removals += [(2,2,'2022-08-01 22:00:00'),(3,3,'2022-08-01 22:00:00'),(7,7,'2022-08-01 23:00:00')]
            for name,rows in [('add_to_cart',carts),('product_buy',buys),('remove_from_cart',removals)]:
                con.execute('CREATE OR REPLACE TABLE fixture(client_id BIGINT,sku BIGINT,timestamp VARCHAR)')
                con.executemany('INSERT INTO fixture VALUES (?,?,?)',rows)
                path=str(Path(tmp)/f'{name}.parquet').replace('\\','/').replace("'","''")
                con.execute(f"COPY fixture TO '{path}' (FORMAT PARQUET)")
            sql=(ROOT/'sql/01_build_journeys.sql').read_text(encoding='utf-8').replace('{{RAW}}',tmp.replace('\\','/'))
            for statement in re.split(r';\s*(?:\n|$)',sql):
                if statement.strip(): con.execute(statement)
            labels=dict(con.execute('SELECT client_id,purchased_7d FROM features').fetchall())
            self.assertEqual(labels,{3:1,4:1,5:0,6:0,10:0})
            self.assertEqual(con.execute('SELECT product_cart_events_24h FROM features WHERE client_id=10').fetchone()[0],1)
            self.assertEqual(con.execute('SELECT product_cart_events_24h FROM features WHERE client_id=3').fetchone()[0],2)
            # The decision-time user history must not include the following day's purchase.
            self.assertEqual(con.execute('SELECT user_buy_events FROM features WHERE client_id=3').fetchone()[0],0)
            con.close()

if __name__=='__main__': unittest.main()
