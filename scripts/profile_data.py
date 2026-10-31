"""Audit raw event files with DuckDB, without reading entire files into pandas."""
from pathlib import Path
import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    raw = args.raw_dir or root / 'data/raw'
    out = args.output_dir or root / 'reports'
    paths = sorted(p for p in raw.rglob('*') if p.is_file() and
                   (p.suffix.lower() in {'.csv', '.parquet'} or p.name.lower().endswith('.csv.gz')))
    if not paths:
        print(f'No CSV, CSV.GZ, or Parquet files found in {raw}. Download and extract the raw dataset first.')
        return 2
    import duckdb
    con = duckdb.connect()
    con.execute("SET threads=2")
    con.execute("SET memory_limit='2GB'")
    results = []
    failures = 0
    for path in paths:
        print(f'Auditing {path.name} ...', flush=True)
        item = {'file': str(path.relative_to(raw)), 'bytes': path.stat().st_size}
        try:
            source = str(path.resolve()).replace("'", "''")
            reader = f"read_parquet('{source}')" if path.suffix.lower() == '.parquet' else f"read_csv_auto('{source}', sample_size=20000)"
            con.execute(f'CREATE OR REPLACE TEMP VIEW source_file AS SELECT * FROM {reader}')
            columns = con.execute('DESCRIBE source_file').fetchall()
            item['columns'] = [{'name': r[0], 'type': r[1]} for r in columns]
            names = {r[0] for r in columns}
            expressions = ['count(*) AS rows']
            for name in ['client_id', 'user_id', 'sku', 'product_id', 'timestamp', 'event_time']:
                if name in names:
                    expressions.append(f'count(*) FILTER (WHERE "{name}" IS NULL) AS "{name}_nulls"')
            for name in ['client_id', 'user_id', 'sku', 'product_id']:
                if name in names:
                    expressions.append(f'count(DISTINCT "{name}") AS "{name}_distinct"')
            for name in ['timestamp', 'event_time']:
                if name in names:
                    expressions.extend([
                        f'min(try_cast("{name}" AS TIMESTAMP)) AS first_timestamp',
                        f'max(try_cast("{name}" AS TIMESTAMP)) AS last_timestamp',
                        f'count(*) FILTER (WHERE "{name}" IS NOT NULL AND try_cast("{name}" AS TIMESTAMP) IS NULL) AS invalid_timestamps',
                    ])
                    break
            cursor = con.execute('SELECT ' + ', '.join(expressions) + ' FROM source_file')
            item['metrics'] = dict(zip([c[0] for c in cursor.description], cursor.fetchone()))
            if 'event_type' in names:
                item['event_counts'] = con.execute('SELECT event_type, count(*) FROM source_file GROUP BY 1 ORDER BY 2 DESC').fetchall()
            item['status'] = 'ok'
        except Exception as exc:
            item['status'] = 'error'
            item['error'] = str(exc)
            failures += 1
        results.append(item)
    out.mkdir(parents=True, exist_ok=True)
    (out/'data_profile.json').write_text(json.dumps(results, indent=2, default=str), encoding='utf-8')
    lines = ['# Raw data audit', '', 'Full-file counts. Counts across event files are not globally deduplicated. Passing this audit does not establish usable journey count or absence of prior promotions.', '']
    for item in results:
        lines.extend([f"## {item['file']}", '', f"Status: {item['status']}", ''])
        if item['status'] == 'error':
            lines.extend([item['error'], ''])
        else:
            lines.extend([f'- {k}: {v}' for k,v in item['metrics'].items()])
            lines.extend(['', 'Columns: ' + ', '.join(c['name'] + ' (' + c['type'] + ')' for c in item['columns']), ''])
            if 'event_counts' in item:
                lines.extend([f'- {kind}: {count}' for kind,count in item['event_counts']])
                lines.append('')
    (out/'data_profile.md').write_text('\n'.join(lines), encoding='utf-8')
    con.close()
    print(f'Audit saved in {out}. Files with errors: {failures}')
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
