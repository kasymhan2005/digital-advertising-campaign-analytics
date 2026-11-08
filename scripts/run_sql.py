"""Execute the example SQL analyses in an in-memory SQLite database."""
from pathlib import Path
import sqlite3
import pandas as pd

root = Path(__file__).resolve().parents[1]
source = root/'data/raw/conversion.csv'
if not source.exists():
    raise SystemExit('Put the source at data/raw/conversion.csv first.')
with sqlite3.connect(':memory:') as conn:
    pd.read_csv(source).to_sql('ads',conn,index=False,if_exists='replace')
    sql = (root/'sql/queries.sql').read_text(encoding='utf-8')
    # Splitting is safe for this static file (all SELECT statements, no ; in comments).
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    output = ['# SQL query outputs', 'Executed against the original coursework CSV.']
    for i,statement in enumerate(statements,1):
        data=pd.read_sql_query(statement,conn)
        output.extend([f'## Query {i}',data.to_markdown(index=False), ''])
    (root/'reports/sql_results.md').write_text('\n\n'.join(output),encoding='utf-8')
    print('Wrote reports/sql_results.md')
