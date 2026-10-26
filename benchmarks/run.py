"""Paired, uncached warm lookup benchmark. Run: python -m benchmarks.run."""
import argparse
import cProfile
import csv
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
import platform
import pstats
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
from fixops.config import ROOT, Settings
from fixops.knowledge import load_runbooks
from fixops.retrieval import Retriever


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_tasks():
    manifest = json.loads((ROOT / 'benchmarks/freeze.json').read_text())
    for name, expected in manifest['sha256'].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Frozen input changed: {name}; create a separately versioned study.')
    return json.loads((ROOT / 'benchmarks/tasks.json').read_text())


def baseline_class():
    spec = importlib.util.spec_from_file_location('fixops._frozen_baseline', ROOT / 'benchmarks/baseline_retrieval.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.Retriever


def statistics(rows):
    supported = [r for r in rows if r['expected_supported']]
    unsupported = [r for r in rows if not r['expected_supported']]
    times = [r['elapsed_ms'] for r in rows]
    return {
        'measurements': len(rows),
        'mean_ms': float(np.mean(times)), 'median_ms': float(np.median(times)),
        'p95_ms': float(np.percentile(times, 95)),
        'recall_at_1': float(np.mean([r['recall_at_1'] for r in supported])),
        'recall_at_3': float(np.mean([r['recall_at_3'] for r in supported])),
        'supported_acceptance_rate': float(np.mean([r['accepted'] for r in supported])),
        'unsupported_rejection_rate': float(np.mean([not r['accepted'] for r in unsupported])),
    }


def profile(engine, tasks, output, count):
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(count):
        for task in tasks:
            engine.search(task['query'])
    profiler.disable()
    profiler.dump_stats(str(output.with_suffix('.prof')))
    stream = io.StringIO()
    pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats('cumulative').print_stats(35)
    output.with_suffix('.txt').write_text(stream.getvalue())


def run(args):
    if args.repeats < 2 or args.warmups < 1:
        raise ValueError('Use at least two repeats and one full warm-up pass.')
    tasks = frozen_tasks()
    settings = Settings()
    docs = load_runbooks()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    versions = {}
    for package in ['numpy', 'scipy', 'scikit-learn', 'sentence-transformers', 'torch', 'transformers', 'streamlit']:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    cpu = platform.processor()
    if Path('/proc/cpuinfo').exists():
        cpu = next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), cpu)
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
              'platform': platform.platform(), 'cpu': cpu, 'logical_cpus': os.cpu_count(),
              'memory': Path('/proc/meminfo').read_text().splitlines()[0] if Path('/proc/meminfo').exists() else 'unavailable',
              'cpu_quota': Path('/sys/fs/cgroup/cpu.max').read_text().strip() if Path('/sys/fs/cgroup/cpu.max').exists() else None,
              'memory_limit_bytes': Path('/sys/fs/cgroup/memory.max').read_text().strip() if Path('/sys/fs/cgroup/memory.max').exists() else None,
              'versions': versions, 'seed': args.seed, 'repeats': args.repeats, 'warmup_passes': args.warmups,
              'corpus_size': len(docs), 'supported_query_count': sum(t['supported'] for t in tasks),
              'unsupported_query_count': sum(not t['supported'] for t in tasks),
              'freeze': json.loads((ROOT / 'benchmarks/freeze.json').read_text()),
              'candidate_sha256': digest(ROOT / 'fixops/retrieval.py'),
              'method': 'External perf_counter around search (validation, redaction, query encoding, ranking, scope). No result cache. Shared immutable fitted encoder/matrix; same process, seeded shuffled queries and randomized pair order. Warm-up excluded. Profiles separate from timing. No UI, LLM, network or human time. Percentiles: numpy linear interpolation. Recall macro-averaged over supported queries; repeats are not additional independent tasks.',
              'results': {}, 'unavailable': {}, 'quality_differences': []}
    rows = []
    for backend in (['tfidf','semantic'] if args.backend == 'both' else [args.backend]):
        threshold = settings.semantic_threshold if backend == 'semantic' else settings.tfidf_threshold
        try:
            start = perf_counter()
            before = baseline_class()(docs, backend, settings.model, threshold)
            startup_ms = (perf_counter()-start)*1000
            after = Retriever.__new__(Retriever)
            after.__dict__.update(before.__dict__)
            engines = {'baseline': before, 'optimized': after}
            model_info = {'configured_name': settings.model, 'device': str(getattr(before.encoder,'device','cpu'))}
            if backend == 'semantic':
                model_info['threads'] = __import__('torch').get_num_threads()
                module = before.encoder[0].auto_model
                model_info['resolved_revision'] = getattr(module.config,'_commit_hash',None)
                from huggingface_hub import try_to_load_from_cache
                config = try_to_load_from_cache(settings.model, 'config.json') if not Path(settings.model).is_dir() else str(Path(settings.model)/'config.json')
                if isinstance(config,str):
                    snapshot = Path(config).parent
                    model_info['snapshot_directory'] = snapshot.name
                    model_info['artifact_sha256'] = {p.name:digest(p) for p in snapshot.iterdir() if p.is_file() and p.suffix in ('.json','.safetensors','.txt')}
                    if snapshot.parent.name=='snapshots':
                        model_info['resolved_revision'] = snapshot.name
            report['results'][backend] = {'startup_ms_excluded': startup_ms, 'threshold': threshold, 'model': model_info}
            for _ in range(args.warmups):
                for task in tasks:
                    for engine in engines.values():
                        engine.search(task['query'])
            rng = random.Random(args.seed)
            for repeat in range(args.repeats):
                shuffled = tasks.copy()
                rng.shuffle(shuffled)
                for task in shuffled:
                    variants = list(engines)
                    rng.shuffle(variants)
                    pair = {}
                    for position, variant in enumerate(variants):
                        start = perf_counter()
                        result = engines[variant].search(task['query'])
                        elapsed = (perf_counter()-start)*1000
                        ids = [h.doc['id'] for h in result.hits]
                        expected = set(task['expected_sources'])
                        row = {'backend':backend,'variant':variant,'repeat':repeat,'pair_position':position,
                               'task_id':task['id'],'expected_supported':task['supported'],
                               'accepted':bool(result.supported),'retrieved_ids':json.dumps(ids),
                               'scores':json.dumps([h.score for h in result.hits]),
                               'elapsed_ms':elapsed,'internal_ms':result.latency_ms,
                               'recall_at_1':len(expected.intersection(ids[:1]))/len(expected) if expected else '',
                               'recall_at_3':len(expected.intersection(ids))/len(expected) if expected else ''}
                        rows.append(row)
                        pair[variant] = (ids,bool(result.supported))
                    if pair['baseline'] != pair['optimized']:
                        report['quality_differences'].append({'backend':backend,'repeat':repeat,'task':task['id'],'results':pair})
            for variant, engine in engines.items():
                selected = [r for r in rows if r['backend']==backend and r['variant']==variant]
                report['results'][backend][variant] = statistics(selected)
                profile(engine, tasks, out / f'{backend}-{variant}-profile', 10)
        except Exception as exc:
            report['unavailable'][backend] = {'type':type(exc).__name__,'message':str(exc)}
    if rows:
        with (out / 'raw.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (out / 'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k in ('results','unavailable','quality_differences')},indent=2))
    return 2 if report['unavailable'] else (3 if report['quality_differences'] else 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=['tfidf','semantic','both'],default='both')
    parser.add_argument('--output',default=str(ROOT / 'reports/benchmark'))
    parser.add_argument('--repeats',type=int,default=30)
    parser.add_argument('--warmups',type=int,default=3)
    parser.add_argument('--seed',type=int,default=20261026)
    args = parser.parse_args()
    raise SystemExit(run(args))

if __name__ == '__main__':
    main()
