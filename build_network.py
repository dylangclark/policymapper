#!/usr/bin/env python3
"""Convert the adaptation workbook to a self-contained, offline HTML explorer.

Usage: python build_network.py "bc_adaptation_network_input 1.0.xlsx" -o adaptation_network.html
       Add --screening "bc_adaptation_outcome_screen.xlsx" to sort and colour outcomes.
       Add --policies "bc_policy_failures_and_enablers.xlsx" for policy-name bubbles.
Requires Python 3.9+ and openpyxl. No browser libraries or network access required.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HTML_TEMPLATE = Path(__file__).with_name("network_template.html").read_text(encoding="utf-8")

# Explicit wording variants present in workbook 1.0; no fuzzy matching.
OUTCOME_ALIASES = {
    'Food disruptions place a smaller burden on household budgets':
        'Climate-related disruptions place a smaller burden on household food budgets',
    'Hazards create fewer unplanned municipal expenditures':
        'Flooding, coastal hazards, and landslides create fewer unplanned municipal expenditures',
    'Disaster costs place a smaller burden on public finances':
        'Climate-related disaster costs place a smaller burden on public finances',
}

def clean(value):
    return ' '.join(str(value or '').split())


def sheet_records(sheet):
    rows = iter(sheet.values)
    headers = [clean(v).lower() for v in next(rows)]
    for number, row in enumerate(rows, 2):
        if any(v is not None and clean(v) for v in row):
            yield number, dict(zip(headers, row))


def codes(value, prefix, context):
    """Accept comma/semicolon/pipe/newline separated IDs; reject malformed tokens."""
    if not clean(value):
        return []
    result = set()
    for token in re.split(r'[,;|\s]+', str(value).strip()):
        if not token:
            continue
        match = re.fullmatch(prefix + r'(\d+)', token, re.I)
        if not match:
            raise ValueError(f'{context}: invalid code {token!r}; expected {prefix}01, {prefix}02, …')
        result.add(f'{prefix}{int(match[1]):02d}')
    return sorted(result)


def read_workbook(path):
    try:
        import openpyxl
    except ImportError as exc:
        raise ValueError('Install the dependency first: python -m pip install openpyxl') from exc
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for required in ('Outcomes', 'Policy problems', 'Enablers'):
            if required not in book.sheetnames:
                raise ValueError(f'Missing worksheet: {required}')
        nodes, edges, warnings = {}, set(), []
        for sheet, prefix, label, description, kind in [
            ('Policy problems', 'F', 'failure', 'statement', 'failure'),
            ('Enablers', 'E', 'enabler', 'enabling condition', 'enabler'),
        ]:
            for row, record in sheet_records(book[sheet]):
                if not clean(record.get('number')):
                    raise ValueError(f'{sheet} row {row}: missing Number')
                ids = codes(record['number'], prefix, f'{sheet} row {row}')
                if len(ids) != 1 or not clean(record.get(label)):
                    raise ValueError(f'{sheet} row {row}: requires one ID and a label')
                node_id = ids[0]
                if node_id in nodes:
                    raise ValueError(f'{sheet} row {row}: duplicate dictionary ID {node_id}')
                nodes[node_id] = dict(id=node_id, label=clean(record[label]),
                    description=clean(record.get(description)), category=clean(record.get('category')), kind=kind)
        themes = {}
        for row, record in sheet_records(book['Outcomes']):
            outcome, theme = clean(record.get('outcome')), clean(record.get('theme'))
            if not outcome or not theme:
                raise ValueError(f'Outcomes row {row}: missing Theme or Outcome')
            if outcome in themes and themes[outcome] != theme:
                raise ValueError(f'Outcome assigned conflicting themes: {outcome}')
            themes[outcome] = theme
        candidates = []
        for sheet in book:
            headers = {clean(v).lower() for v in next(sheet.values)}
            if {'outcome', 'failure', 'enabler'} <= headers:
                candidates.append(sheet)
        if len(candidates) != 1:
            raise ValueError('Expected exactly one connection sheet with Outcome, Failure, Enabler headers')
        outcomes = {}
        for row, record in sheet_records(candidates[0]):
            label = clean(record.get('outcome'))
            if not label:
                raise ValueError(f'Connection row {row}: missing Outcome')
            if label not in themes and label in OUTCOME_ALIASES:
                original = label
                label = OUTCOME_ALIASES[label]
                warnings.append(f'Row {row}: matched shortened label "{original}" to "{label}".')
            if label not in themes:
                raise ValueError(f'Connection row {row}: outcome missing from Outcomes lookup: {label}')
            if label not in outcomes:
                node_id = f'O{len(outcomes)+1:03d}'
                outcomes[label] = node_id
                nodes[node_id] = dict(id=node_id, label=label, description=label,
                    category=themes[label], theme=themes[label], kind='outcome')
            for column, prefix in [('failure', 'F'), ('enabler', 'E')]:
                for code in codes(record.get(column), prefix, f'Connection row {row}, {column}'):
                    if code not in nodes:
                        raise ValueError(f'Connection row {row}: undefined code {code}')
                    edges.add((outcomes[label], code))
        for label, theme in themes.items():
            if label not in outcomes:
                warnings.append(f'No connections supplied for outcome: {label}')
                node_id = f'O{len(outcomes)+1:03d}'
                outcomes[label] = node_id
                nodes[node_id] = dict(id=node_id, label=label, description=label,
                    category=theme, theme=theme, kind='outcome')
        if not outcomes:
            raise ValueError('No outcomes found')
        return dict(source=path.name, nodes=list(nodes.values()),
            edges=[dict(source=a, target=b) for a, b in sorted(edges)], warnings=warnings)
    finally:
        book.close()


SCREENING_FIELDS = ('economic', 'governance', 'salience', 'urgency')
SCREENING_ALIASES = {
    'Communities experience less damaging flooding during heavy rainfall':
        'Communities experience less damaging surface-water flooding during heavy rainfall',
}


def screening_header(value):
    text = clean(value).lower()
    if text in ('outcome', 'outcome statement'):
        return 'outcome'
    if text.startswith(('annual direct economic', 'economic')):
        return 'economic'
    if text.startswith(('government salience', 'governance salience', 'salience')):
        return 'salience'
    if text.startswith('governance'):
        return 'governance'
    if text == 'urgency':
        return 'urgency'
    if text.startswith('notes'):
        return 'notes'
    return text


def screening_score(value, context):
    """Only explicit 1/2/3 classes are scored; never coerce unknowns to low."""
    text = clean(value)
    if not text or text.casefold() in ('unknown', 'u', 'unscored'):
        return None
    if text.casefold() in ('n/a', 'na', 'not applicable'):
        return 'N/A'
    if not isinstance(value, bool) and text in ('1', '2', '3', '1.0', '2.0', '3.0'):
        return int(float(text))
    raise ValueError(f'{context}: invalid screening score {value!r}; use 1, 2, 3, Unknown, N/A or blank')


def add_screening(data, path):
    """Join by canonical outcome statement, never by mutable Excel row number."""
    import openpyxl
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        candidates = []
        required = {'outcome', *SCREENING_FIELDS}
        for sheet in book:
            # Support the title/intro rows in the screening workbook.
            for row_number, row in enumerate(sheet.iter_rows(values_only=True), 1):
                if row_number > 30:
                    break
                headers = [screening_header(v) for v in row]
                if required <= set(headers):
                    if any(headers.count(h) != 1 for h in required):
                        raise ValueError(f'{sheet.title} row {row_number}: duplicate screening headers')
                    candidates.append((sheet, row_number, headers))
        if len(candidates) != 1:
            raise ValueError('Expected exactly one screening table with Outcome statement, Economic, Governance, Government salience and Urgency columns')
        sheet, header_row, headers = candidates[0]
        by_label = {n['label']: n for n in data['nodes'] if n['kind'] == 'outcome'}
        seen = set()
        for row_number, row in enumerate(sheet.iter_rows(min_row=header_row + 1, values_only=True), header_row + 1):
            record = dict(zip(headers, row))
            label = clean(record.get('outcome'))
            if not label:
                if any(clean(record.get(k)) for k in SCREENING_FIELDS):
                    raise ValueError(f'{sheet.title} row {row_number}: scores without an outcome statement')
                continue
            label = OUTCOME_ALIASES.get(label, label)
            if label in SCREENING_ALIASES:
                original = label
                label = SCREENING_ALIASES[label]
                data['warnings'].append(f'Screening row {row_number}: explicitly matched "{original}" to network outcome "{label}". Network wording and connections are retained; the screening wording is broader.')
            if label not in by_label:
                raise ValueError(f'{sheet.title} row {row_number}: outcome not found in network: {label}')
            if label in seen:
                raise ValueError(f'{sheet.title} row {row_number}: duplicate outcome statement: {label}')
            seen.add(label)
            node = by_label[label]
            node['scores'] = {field: screening_score(record.get(field), f'{sheet.title} row {row_number}, {field}')
                              for field in SCREENING_FIELDS}
            node['screening_notes'] = str(record.get('notes') or '').strip().replace('\\n', '\n')
        missing = set(by_label) - seen
        for label in sorted(missing):
            data['warnings'].append(f'No screening row for outcome; shown as Unknown: {label}')
        if not seen:
            raise ValueError('Screening table has no matching outcomes')
        data['screening_source'] = path.name
        data['screening_matched'] = len(seen)
    finally:
        book.close()


POLICY_ROLES = {
    'addresses': ('failures addressed (codes)', 'F', 'how failures are addressed / scope'),
    'potentially_worsens': ('failures potentially worsened (codes)', 'F', 'potential worsening / evidence needed'),
    'supports': ('enablers supported (codes)', 'E', 'enabling mechanism and scope'),
    'potentially_constrains': ('conditions potentially constrained (codes)', 'E', 'potential constraint / evidence needed'),
}


def find_table(book, sheet_name, required):
    if sheet_name not in book.sheetnames:
        raise ValueError(f'Policy workbook missing worksheet: {sheet_name}')
    sheet = book[sheet_name]
    for number, row in enumerate(sheet.iter_rows(values_only=True), 1):
        if number > 30:
            break
        headers = [clean(v).lower() for v in row]
        if set(required) <= set(headers):
            if any(headers.count(h) != 1 for h in required):
                raise ValueError(f'{sheet_name} row {number}: duplicate required headers')
            return sheet, number, headers
    raise ValueError(f'{sheet_name}: missing required headers: {", ".join(required)}')


def policy_entry(value, context):
    try:
        if isinstance(value, bool) or float(value) != int(float(value)) or float(value) < 1:
            raise ValueError()
        return f'P{int(float(value)):03d}'
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f'{context}: expected a positive integer policy entry, got {value!r}') from exc


def add_policies(data, path):
    """Intersect explicit policy→outcome and policy→code links with existing edges.

    This places candidate associations, not independently validated three-way
    causal links. Never create a new outcome/code edge to accommodate a policy.
    """
    import openpyxl
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        required = ['entry', 'policy', 'reviewed source'] + [v[0] for v in POLICY_ROLES.values()]
        sheet, header_row, headers = find_table(book, 'Policies', required)
        node_ids = {n['id'] for n in data['nodes']}
        policies = {}
        for number, row in enumerate(sheet.iter_rows(min_row=header_row + 1, values_only=True), header_row + 1):
            record = dict(zip(headers, row))
            if not any(clean(v) for v in row):
                continue
            pid = policy_entry(record.get('entry'), f'Policies row {number}')
            if pid in policies:
                raise ValueError(f'Policies row {number}: duplicate policy entry {pid}')
            title = clean(record.get('policy'))
            if not title:
                raise ValueError(f'Policies row {number}: missing policy title')
            p = dict(id=pid, title=title, source=str(record.get('reviewed source') or '').strip(),
                     summary=str(record.get('policy summary') or '').strip(), codes={}, code_notes={})
            for role, (column, prefix, explanation) in POLICY_ROLES.items():
                raw = record.get(column)
                cs = [] if clean(raw).casefold() in ('', 'none', 'none identified', 'n/a') else codes(raw, prefix, f'{pid}, {column}')
                if set(cs) - node_ids:
                    raise ValueError(f'{pid}: undefined policy codes: {sorted(set(cs) - node_ids)}')
                p['codes'][role] = cs
                p['code_notes'][role] = str(record.get(explanation) or '').strip()
            policies[pid] = p
        if not policies:
            raise ValueError('Policy workbook contains no policies')
        required = ['policy entry', 'policy', 'outcome id', 'outcome statement', 'relationship', 'mechanism and limits']
        sheet, header_row, headers = find_table(book, 'Policy-outcome links', required)
        outcomes = {n['id']: n for n in data['nodes'] if n['kind'] == 'outcome'}
        edges = {(e['source'], e['target']): e for e in data['edges']}
        links, seen, unmatched = [], set(), []
        for number, row in enumerate(sheet.iter_rows(min_row=header_row + 1, values_only=True), header_row + 1):
            if not any(clean(v) for v in row):
                continue
            record = dict(zip(headers, row))
            pid = policy_entry(record.get('policy entry'), f'Policy-outcome links row {number}')
            if pid not in policies:
                raise ValueError(f'Policy-outcome links row {number}: undefined policy {pid}')
            if clean(record.get('policy')) != policies[pid]['title']:
                raise ValueError(f'Policy-outcome links row {number}: title does not match {pid}')
            oid = clean(record.get('outcome id')).upper()
            label = clean(record.get('outcome statement'))
            label = OUTCOME_ALIASES.get(label, label)
            if oid not in outcomes or label != outcomes[oid]['label']:
                raise ValueError(f'Policy-outcome links row {number}: outcome ID/statement mismatch: {oid}: {label}')
            if (pid, oid) in seen:
                raise ValueError(f'Policy-outcome links row {number}: duplicate pair {pid}/{oid}')
            seen.add((pid, oid))
            lid = pid + ':' + oid
            links.append(dict(id=lid, policy=pid, outcome=oid,
                              relationship=clean(record.get('relationship')),
                              rationale=str(record.get('mechanism and limits') or '').strip()))
            attached = {}
            for role, cs in policies[pid]['codes'].items():
                for code in cs:
                    edge = edges.get((oid, code))
                    if edge is not None:
                        attached.setdefault(code, []).append(role)
            for code, roles in sorted(attached.items()):
                edges[(oid, code)].setdefault('policies', []).append(dict(policy=pid, link=lid, roles=roles))
            if not attached:
                unmatched.append(lid)
        for edge in data['edges']:
            edge.get('policies', []).sort(key=lambda a: a['policy'])
        data['policies'] = list(policies.values())
        data['policy_outcomes'] = links
        data['policy_source'] = path.name
        data['policy_stats'] = dict(outcome_links=len(links),
            associations=sum(len(e.get('policies', [])) for e in data['edges']),
            labelled_edges=sum(bool(e.get('policies')) for e in data['edges']),
            unplaced_outcome_links=unmatched)
        if unmatched:
            data['warnings'].append(f'{len(unmatched)} policy–outcome pairs have no overlapping code on an existing network edge; no new edge was created for them.')
    finally:
        book.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('workbook', type=Path)
    parser.add_argument('--screening', type=Path, help='Outcome screening workbook with four 1–3 rating columns')
    parser.add_argument('--policies', type=Path, help='Consolidated policy workbook containing Policies and Policy-outcome links tables')
    parser.add_argument('-o', '--output', type=Path, default=Path('adaptation_network.html'))
    args = parser.parse_args()
    try:
        data = read_workbook(args.workbook)
        if args.screening:
            add_screening(data, args.screening)
        if args.policies:
            add_policies(data, args.policies)
        template = HTML_TEMPLATE
        # Prevent workbook text from terminating the inert JSON script element.
        payload = json.dumps(data, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(template.replace('__WORKBOOK_JSON__', payload), encoding='utf-8')
        print(f'Created {args.output.resolve()} ({len(data["nodes"])} nodes, {len(data["edges"])} connections)')
        for warning in data['warnings']:
            print('Warning:', warning, file=sys.stderr)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
