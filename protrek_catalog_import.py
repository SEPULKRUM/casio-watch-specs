"""Parse the supplied text-only Pro Trek compilation with family and page scope."""
import argparse
import json
import re
import subprocess
from pathlib import Path

def parse_text(text):
    models, comparisons, families, conflicts = [], [], [], []
    family = None
    mode = None
    columns = None
    current = None
    detail = None
    for page_number, page in enumerate(text.split('\f'), 1):
        for line in page.splitlines():
            stripped = line.strip()
            if match := re.match(r'(.+?) \| (\d+) models$', stripped):
                family = match[1]
                mode = None
                current = None
                continue
            if match := re.match(r'(.+?) \(((?:PRX|PRW|PRG|WSD|PRJ|SPF)-[A-Z0-9]+)\)$', stripped):
                detail = {'title': match[1], 'family': match[2], 'extraction_pdf_page': page_number, 'details': []}
                families.append(detail)
                mode = None
                continue
            if detail and page_number in {2, 3, 4} and stripped and not stripped.startswith('CASIO PRO TREK'):
                detail['details'].append(stripped)
            if 'Model ' in line and all(label in line for label in ['Module', 'Water / reference size', 'Key functions / model note', 'Source page(s)']):
                mode = 'models'
                labels = ['Model', 'Module', 'Water / reference size', 'Key functions / model note', 'Source page(s)']
                columns = [line.index(label) for label in labels]
                current = None
                continue
            if all(label in line for label in ['Family', 'Water resistance', 'Size (family reference)', 'Power / synchronization']):
                mode = 'comparison'
                labels = ['Family', 'Water resistance', 'Size (family reference)', 'Power / synchronization']
                columns = [line.index(label) for label in labels]
                current = None
                continue
            if all(label in line for label in ['Specification', 'Archived Casio page', 'Supplied graphic / verification note']):
                mode = 'conflicts'
                labels = ['Specification', 'Archived Casio page', 'Supplied graphic / verification note']
                columns = [line.index(label) for label in labels]
                current = None
                continue
            if not mode or not columns or not stripped:
                continue
            if stripped.startswith('CASIO PRO TREK'):
                current = None
                continue
            cells = [line[a:b].strip() for a, b in zip(columns, columns[1:] + [None])]
            if not cells[0] and current:
                for index, value in enumerate(cells):
                    if value:
                        current['cells'][index] += ' ' + value
                continue
            if mode in {'models', 'comparison'} and not re.fullmatch(r'(?:PRX|PRW|PRG|WSD|PRJ|SPF)-[A-Z0-9-]+', cells[0]):
                continue
            if mode == 'conflicts' and not re.search(r'\S {2,}\S', line):
                mode = None
                continue
            if cells[0]:
                current = {'extraction_pdf_page': page_number, 'family_title': family, 'columns': labels[:], 'cells': cells}
                {'models': models, 'comparison': comparisons, 'conflicts': conflicts}[mode].append(current)
    return {'models': models, 'family_comparisons': comparisons, 'detailed_families': families, 'spf_source_comparison': conflicts}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    text = subprocess.check_output(['pdftotext', '-layout', args.pdf, '-'], text=True)
    parsed = parse_text(text)
    Path(args.output).write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({name: len(rows) for name, rows in parsed.items()}))
