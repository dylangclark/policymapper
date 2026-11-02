"""Read the supplied research inventory without reclassifying its outcome matches."""
import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


# Display aliases only. The original institution is retained on each record.
INSTITUTIONS = {
    "Queen's University (Kingston, Ontario)": "Queen's University",
    "University of Waterloo (Ontario)": "University of Waterloo",
    "The University of Western Ontario": "Western University",
    "Western University (The University of Western Ontario)": "Western University",
    "Carleton University (Ottawa)": "Carleton University",
}
INSTITUTION_LOOKUP = json.loads(Path(__file__).with_name('research_institutions.json').read_text(encoding='utf-8'))
REQUIRED = {
    'Project title', 'PI / named lead', 'University / lead institution at award',
    'IS BC', 'Funder', 'Project ID', 'Primary outcome theme', 'Primary outcome statement',
    'Grant dollar value (CAD)', 'Grant dollar value basis', 'Additional linked outcomes',
}


def funding_basis(text):
    text = text.lower()
    if not text:
        return 'missing'
    if 'fiscal-year' in text:
        return 'payment'
    if 'not confirmed' in text:
        return 'uncertain'
    if 'annual northern' in text:
        return 'annual'
    if 'supplement only' in text or 'early career supplement' in text:
        return 'supplement'
    return 'award'


def add_research(data, path):
    records, seen = [], set()
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if not REQUIRED <= set(reader.fieldnames or []):
            raise ValueError('Research CSV is missing columns: ' + ', '.join(sorted(REQUIRED - set(reader.fieldnames or []))))
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('Research CSV has duplicate headers')
        for row, raw in enumerate(reader, 2):
            if None in raw or any(v is None for v in raw.values()):
                raise ValueError(f'Research CSV row {row}: inconsistent column count')
            r = {k: v.strip() for k, v in raw.items()}
            if not any(r.values()):
                continue
            for key in ('Project title', 'Primary outcome theme', 'Primary outcome statement'):
                if not r[key]:
                    raise ValueError(f'Research CSV row {row}: missing {key}')
            if r['IS BC'] not in ('0', '1'):
                raise ValueError(f'Research CSV row {row}: IS BC must be 0 or 1')
            # A grant ID is unique within a funder, never globally across funders.
            identity = (r['Funder'], r['Project ID']) if r['Project ID'] else (
                r['Funder'], r['Project title'], r['PI / named lead'], r.get('Award / competition year', ''))
            if identity in seen:
                raise ValueError(f'Research CSV row {row}: duplicate project identity {identity}')
            seen.add(identity)
            value = r['Grant dollar value (CAD)']
            cents = None
            if value and value.upper() not in ('NA', 'N/A', 'UNKNOWN'):
                try:
                    amount = Decimal(value.replace(',', '').removeprefix('$'))
                except InvalidOperation as exc:
                    raise ValueError(f'Research CSV row {row}: invalid dollar value {value!r}') from exc
                if not amount.is_finite() or amount < 0 or amount * 100 > 2**53-1 or amount * 100 != (amount * 100).to_integral_value():
                    raise ValueError(f'Research CSV row {row}: dollars must be finite, nonnegative, and at most two decimal places')
                cents = int(amount * 100)
            institution = r['University / lead institution at award']
            if institution and institution not in INSTITUTION_LOOKUP:
                raise ValueError(f'Research CSV row {row}: institution geography/type needs a lookup entry: {institution}')
            lookup = INSTITUTION_LOOKUP.get(institution, {})
            region = 'unknown' if not institution else 'international' if lookup['country']=='international' else 'bc' if r['IS BC'] == '1' else 'canada'
            # Exact source flag determines BC; no inference from a project's geography.
            is_university = lookup.get('university', False)
            records.append(dict(
                id=f'R{len(records)+1:03d}', source_row=row, title=r['Project title'],
                pi=r['PI / named lead'] or 'Not supplied',
                institution=INSTITUTIONS.get(institution, institution) or 'Institution not supplied',
                original_institution=institution, region=region, university=is_university,
                theme=r['Primary outcome theme'], objective=r['Primary outcome statement'],
                cents=cents, basis=funding_basis(r['Grant dollar value basis']) if cents is not None else 'missing',
                raw=r,
            ))
    if not records:
        raise ValueError('Research CSV contains no projects')
    data['research'] = dict(source=path.name, records=records, allocation='primary',
        notes=[
            'Objective means the primary outcome statement in the supplied CSV. Each record is allocated once; additional outcome links do not duplicate its dollars.',
            'Mappings and research relevance are provisional assessments from the source file, not verified project effects or evidence of research gaps.',
            'Amounts retain their published basis. Awards, fiscal-year payments, supplements and uncertain periods are separated; they are not annualized or multiplied by award term.',
            'BC uses the source IS BC flag at the lead institution at award. Missing and foreign institutions are excluded from Canadian views; institution country and type come from the explicit generator lookup, not a project-location inference.',
            'University-only views exclude hospital, government, non-profit and other non-university leads. Institutional aliases are display-only; original labels appear in details.',
            'The inventory is a screened selection with mixed award years, not a census of Canadian adaptation research funding. Missing values are not zero.',
        ])
