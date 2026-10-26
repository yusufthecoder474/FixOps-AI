"""Genuine volunteer study only; no simulated completion observations.

python -m benchmarks.human plan --participants P01 P02 P03 P04
python -m benchmarks.human record --participant P01
python -m benchmarks.human summarize --assessed reports/human/assessed.csv
"""
import argparse
import csv
import json
import math
import random
import statistics
from pathlib import Path
from time import perf_counter
from benchmarks.run import frozen_tasks

FIELDS = ['participant','task_id','mode','order','locate_seconds','elapsed_seconds',
          'chosen_runbook','submitted_steps','timed_out','success','errors','assessor']


def schedule(participants, tasks):
    if not participants or len(set(participants)) != len(participants):
        raise ValueError('Use unique anonymized participant IDs.')
    tasks = [t for t in tasks if t['supported']]
    shuffled = tasks.copy()
    random.Random(20261026).shuffle(shuffled)
    rows = []
    for index, participant in enumerate(participants):
        ordered = list(enumerate(shuffled))
        if (index // 2) % 2:
            ordered.reverse()
        for order, (task_index, task) in enumerate(ordered, 1):
            rows.append({'participant':participant,'task_id':task['id'],
                         'mode':'manual' if (task_index + index) % 2 == 0 else 'assisted',
                         'order':order})
    return rows


def summarize(rows):
    if not rows:
        return {'status':'unexecuted','participants':0,'observations':0}
    for row in rows:
        if row['success'] not in ('0','1') or not row['assessor'].strip():
            raise ValueError('Every observation needs genuine assessor identity and success=0/1.')
        if row['mode'] not in ('manual','assisted') or row['timed_out'] not in ('0','1'):
            raise ValueError('Invalid condition or timeout value.')
        locate, elapsed = float(row['locate_seconds']), float(row['elapsed_seconds'])
        if not (math.isfinite(elapsed) and 0 <= locate <= elapsed) or int(row['errors']) < 0:
            raise ValueError('Invalid timing or error count.')
        if elapsed >= 300 and row['timed_out']!='1':
            raise ValueError('Elapsed >=300 seconds must be marked as timeout.')
        if row['timed_out']=='1' and row['success']=='1':
            raise ValueError('A timeout cannot count as successful completion.')
    keys = [(r['participant'],r['task_id']) for r in rows]
    if len(keys)!=len(set(keys)):
        raise ValueError('Duplicate participant/task observations.')
    modes = {}
    for mode in ('manual','assisted'):
        selected = [r for r in rows if r['mode']==mode]
        successful = [r for r in selected if r['success']=='1']
        modes[mode] = {'tasks':len(selected),
            'success_rate':sum(int(r['success']) for r in selected)/len(selected) if selected else None,
            'errors':sum(int(r['errors']) for r in selected),
            'timeouts':sum(int(r['timed_out']) for r in selected),
            'successful_median_seconds':statistics.median(float(r['elapsed_seconds']) for r in successful) if successful else None,
            'successful_median_locate_seconds':statistics.median(float(r['locate_seconds']) for r in successful) if successful else None}
    paired = []
    for participant in sorted({r['participant'] for r in rows}):
        medians = {}
        for mode in modes:
            values = [float(r['elapsed_seconds']) for r in rows if r['participant']==participant and r['mode']==mode and r['success']=='1']
            if values:
                medians[mode] = statistics.median(values)
        if len(medians)==2:
            paired.append({'participant':participant,**medians,'difference_seconds':medians['manual']-medians['assisted']})
    return {'status':'assessed','participants':len({r['participant'] for r in rows}),
            'observations':len(rows),'modes':modes,'participant_paired_successful_medians':paired,
            'note':'Report failure/timeout rates alongside successful-only times. Tasks within participants are dependent; no causal or population claim from descriptive medians.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    plan = sub.add_parser('plan')
    plan.add_argument('--participants',nargs='+',required=True)
    record = sub.add_parser('record')
    record.add_argument('--participant',required=True)
    summary = sub.add_parser('summarize')
    summary.add_argument('--assessed',required=True)
    parser.add_argument('--output',default='reports/human')
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    tasks = frozen_tasks()
    if args.command=='plan':
        rows = schedule(args.participants,tasks)
        (out/'assignments.json').write_text(json.dumps(rows,indent=2)+'\n')
        print('Assignments created. No participant observations collected.')
    elif args.command=='record':
        consent = input('Confirm volunteer consent and completed practice task (type YES): ')
        if consent != 'YES':
            raise SystemExit('No data collected.')
        assignments = json.loads((out/'assignments.json').read_text())
        selected = [r for r in assignments if r['participant']==args.participant]
        if not selected:
            raise ValueError('Participant not in plan.')
        raw = out/'raw.csv'
        existing = list(csv.DictReader(raw.open())) if raw.exists() else []
        done = {(r['participant'],r['task_id']) for r in existing}
        for row in selected:
            if (row['participant'],row['task_id']) in done:
                continue
            task = next(t for t in tasks if t['id']==row['task_id'])
            print(f"Condition: {row['mode']}. Hide all answer keys; follow HUMAN_STUDY.md.")
            input('Press Enter to reveal the task and start the timer. ')
            start = perf_counter()
            print(task['query'])
            input('Press Enter as soon as you locate your chosen runbook (or at 300s timeout). ')
            locate = perf_counter()-start
            chosen = input('Enter chosen runbook ID: ')
            steps = input('Describe all three investigation steps (one line): ')
            elapsed = perf_counter()-start
            # Keep actual elapsed time, including timeout overruns, for audit.
            result = {**row,'locate_seconds':locate,'elapsed_seconds':elapsed,
                      'chosen_runbook':chosen,'submitted_steps':steps,
                      'timed_out':int(elapsed>=300),'success':'','errors':'','assessor':''}
            new = not raw.exists()
            with raw.open('a',newline='') as f:
                writer = csv.DictWriter(f,fieldnames=FIELDS)
                if new: writer.writeheader()
                writer.writerow(result)
            print('Recorded. Assessor scoring is required; no automatic success claim.')
    else:
        with Path(args.assessed).open(newline='') as f:
            result = summarize(list(csv.DictReader(f)))
        (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
