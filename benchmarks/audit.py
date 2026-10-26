"""Recompute saved benchmark metrics without loading a model or timing queries."""
import argparse
import csv
import json
import numpy as np
from pathlib import Path
from benchmarks.run import statistics


def audit(directory):
    directory=Path(directory)
    report=json.loads((directory/'summary.json').read_text())
    with (directory/'raw.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    keys=set()
    for row in rows:
        key=tuple(row[k] for k in ['backend','variant','repeat','task_id'])
        if key in keys:
            raise ValueError(f'Duplicate observation: {key}')
        keys.add(key)
        for key in ['expected_supported','accepted']:
            if row[key] not in ('True','False'):
                raise ValueError('Invalid Boolean value')
            row[key]=row[key]=='True'
        for key in ['elapsed_ms','internal_ms','recall_at_1','recall_at_3']:
            if row[key]!='':
                row[key]=float(row[key])
                if not np.isfinite(row[key]) or row[key]<0:
                    raise ValueError('Invalid numeric observation')
    expected_count=(report['supported_query_count']+report['unsupported_query_count'])*report['repeats']
    score_difference=0.0
    for backend,data in report['results'].items():
        for variant in ['baseline','optimized']:
            selected=[r for r in rows if r['backend']==backend and r['variant']==variant]
            if len(selected)!=expected_count or statistics(selected)!=data[variant]:
                raise ValueError(f'Raw data / summary mismatch: {backend}/{variant}')
        before={(r['repeat'],r['task_id']):r for r in rows if r['backend']==backend and r['variant']=='baseline'}
        after={(r['repeat'],r['task_id']):r for r in rows if r['backend']==backend and r['variant']=='optimized'}
        if before.keys()!=after.keys():
            raise ValueError('Incomplete pairs')
        for key,old in before.items():
            new=after[key]
            if old['retrieved_ids']!=new['retrieved_ids'] or old['accepted']!=new['accepted']:
                raise ValueError(f'Ranking/acceptance changed: {backend}/{key}')
            score_difference=max(score_difference,float(np.max(np.abs(np.array(json.loads(old['scores']))-np.array(json.loads(new['scores']))))))
    if report['unavailable'] or report['quality_differences']:
        raise ValueError('Report contains unavailable engines or quality changes')
    return {'status':'passed','rows':len(rows),'all_summary_metrics_recomputed':True,
            'ranking_and_acceptance_changes':0,'max_absolute_score_difference':score_difference}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',nargs='?',default='reports/final')
    args=parser.parse_args()
    print(json.dumps(audit(args.directory),indent=2))

if __name__=='__main__':
    main()
