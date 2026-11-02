#!/usr/bin/env python3
"""Add an offline, self-contained importance/attention scatter to policymapper.

Run from a checkout of https://github.com/dylangclark/policymapper:
  python add_attention_scatter.py --repo . --data "Export outcome to expenditures_strong.csv"

Updates network_template.html (persistent across rebuilds) and index.html, if
present.  It does not change the source spreadsheet, research funding, or
network data.  Safe to rerun when the scores CSV changes.
"""
import argparse
import csv
import json
import math
import re
from pathlib import Path

START = '<!-- OUTCOME_ATTENTION_SCATTER_START -->'
END = '<!-- OUTCOME_ATTENTION_SCATTER_END -->'
TEMPLATE = Path(__file__).with_name('outcome_scatter_fragment.html.in')


def load_rows(path):
    with path.open('r', newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'Theme','Outcome','Importance score','Attention score',
                    'Number of contracts','Number grants (BC)'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError('Missing columns: '+', '.join(sorted(required-set(reader.fieldnames or []))))
        result, seen = [], set()
        for number, source in enumerate(reader, 2):
            label = ' '.join(source['Outcome'].split())
            theme = ' '.join(source['Theme'].split())
            if not label or not theme:
                raise ValueError(f'CSV row {number}: missing outcome or theme')
            if label in seen:
                raise ValueError(f'CSV row {number}: repeated outcome {label!r}')
            seen.add(label)
            def f(key):
                value = float(source[key].strip())
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f'CSV row {number}: {key} must be nonnegative and finite')
                return value
            def i(key):
                value = f(key)
                if not value.is_integer():
                    raise ValueError(f'CSV row {number}: {key} must be a whole-number count')
                return int(value)
            result.append({'theme':theme,'outcome':label,
                           'importance':f('Importance score'),'attention':f('Attention score'),
                           'contracts':i('Number of contracts'),'grants':i('Number grants (BC)')})
    if not result:
        raise ValueError('The input CSV contains no outcomes')
    return result


def fragment(rows):
    raw = TEMPLATE.read_text(encoding='utf-8')
    payload=json.dumps(rows,ensure_ascii=False,separators=(',',':'))
    # Keep arbitrary CSV text from breaking the inert JSON script element.
    payload=payload.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    return raw.replace('__ATTENTION_SCATTER_JSON__',payload).strip('\n')


def embed(existing, block, filename):
    if START in existing or END in existing:
        pat=re.compile(re.escape(START)+r'.*?'+re.escape(END),re.DOTALL)
        if len(pat.findall(existing))!=1:
            raise ValueError(f'{filename}: expected one previously inserted scatter section')
        return pat.sub(lambda _:block,existing,count=1)
    if 'id="research"' not in existing or 'id="fundingMap"' not in existing:
        raise ValueError(f'{filename}: not the expected policymapper page with funding treemap')
    # Insert after the research funding panel but before the research tab closes.
    pat=re.compile(r'(?P<panel_close></div>)\s*(?P<research_close></section>\s*</main>)')
    found=list(pat.finditer(existing))
    if len(found)!=1:
        raise ValueError(f'{filename}: cannot uniquely locate end of research tab')
    m=found[0]
    return existing[:m.start()]+m.group('panel_close')+'\n'+block+'\n'+m.group('research_close')+existing[m.end():]


def preview(block, path):
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Importance and attention scatter — preview</title><style>:root{--ink:#18332f;--muted:#627570;--line:#d9e3dc;--bg:#f3f6f2}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}button,input,select{font:inherit;border:1px solid #bfcec4;border-radius:7px;background:white;color:var(--ink);padding:8px 12px}button{cursor:pointer}main{max-width:1450px;margin:20px auto;padding:0 20px}.panel{background:white;border:1px solid var(--line);border-radius:12px;padding:22px;margin-bottom:18px}.eyebrow{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}h2{font-size:20px;margin:0 0 3px}.subtle{color:var(--muted);font-size:13px}</style></head><body><main><p class="subtle">Standalone preview of the component that will appear immediately beneath the treemap in the Research funding tab.</p>'''
    path.write_text(page+block+'</main></body></html>',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo',type=Path,default=Path('.'),help='Directory containing policymapper index.html and network_template.html')
    ap.add_argument('--data',type=Path,default=Path('Export outcome to expenditures_strong.csv'))
    ap.add_argument('--preview',type=Path,default=None,help='Also write a standalone HTML preview')
    ap.add_argument('--preview-only',action='store_true',help='Only create preview; do not change repo files')
    args=ap.parse_args()
    rows=load_rows(args.data)
    block=fragment(rows)
    if args.preview:
        args.preview.parent.mkdir(parents=True,exist_ok=True)
        preview(block,args.preview)
        print(f'Created standalone preview: {args.preview}')
    if args.preview_only:
        return
    files=[args.repo/'network_template.html',args.repo/'index.html']
    present=[p for p in files if p.is_file()]
    if not present:
        ap.error('Could not find network_template.html or index.html under --repo')
    updated={p:embed(p.read_text(encoding='utf-8'),block,str(p)) for p in present}
    for p,content in updated.items():
        p.write_text(content,encoding='utf-8')
        print(f'Updated {p} with {len(rows)} scored outcomes')
    if not (args.repo/'network_template.html').exists():
        print('Note: the template is absent; regenerate index.html only after adding the component to the template.')

if __name__=='__main__':
    main()
