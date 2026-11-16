"""Parse supplied 2011 watch-family and clock indexes without inventing retail SKUs."""
import argparse
import json
import re
import subprocess
from pathlib import Path

def parse_text(text):
    watches, clocks = [], []
    group = None
    mode = None
    columns = None
    for pdf_page, page in enumerate(text.split('\f'), 1):
        for line in page.splitlines():
            if match := re.match(r'\s*(.+?) \| (\d+) indexed models\s*$', line):
                group = match[1]
                mode = None
            if all(label in line for label in ['Model', 'Case (mm)', 'Mass (g)', 'Module', 'Catalog p.']):
                mode = 'watch'
                labels = ['Model', 'Case (mm)', 'Mass (g)', 'Module', 'Catalog p.']
                columns = [line.index(label) for label in labels]
                continue
            if line.count('Clock model') == 2 and line.count('Catalog p.') == 2:
                mode = 'clock'
                first = line.index('Clock model')
                second = line.index('Clock model', first + 1)
                columns = [first, line.index('Catalog p.'), second, line.index('Catalog p.', second)]
                continue
            if not mode or not columns or not line.strip() or line.lstrip().startswith('Casio 2011 catalog'):
                continue
            cells = [line[a:b].strip() for a, b in zip(columns, columns[1:] + [None])]
            if mode == 'watch':
                model, size, mass, module, product_pages = cells
                if not re.fullmatch(r'[A-Z][A-Z0-9-]*(?: \([A-Z0-9/]+\))?', model):
                    continue
                match = re.fullmatch(r'(\d+(?:\.\d+)?) x (\d+(?:\.\d+)?) x (\d+(?:\.\d+)?)', size)
                if not match:
                    raise ValueError('Unparsed dimensions: ' + model)
                modules = [] if module == '—' else re.split(r'\s*/\s*', module)
                if any(not re.fullmatch(r'\d{2,4}', value) for value in modules):
                    raise ValueError('Unparsed module: ' + model)
                pages = [] if product_pages == '—' else expand_pages(product_pages)
                watches.append({'printed_label': model, 'id': model.split(' (')[0], 'printed_group': group,
                                'indexed_dimensions_mm': dict(zip(['length', 'width', 'thickness'], map(float, match.groups()))),
                                'indexed_weight_g': float(mass), 'printed_module_text': module, 'modules': modules,
                                'printed_product_pages': pages, 'original_pdf_product_pages': [p + 2 for p in pages],
                                'extraction_pdf_page': pdf_page})
            else:
                for model, product_pages in [(cells[0], cells[1]), (cells[2], cells[3])]:
                    if not model:
                        continue
                    if not re.fullmatch(r'[A-Z]+-[A-Z0-9]+', model):
                        continue
                    pages = expand_pages(product_pages)
                    clocks.append({'id': model, 'printed_product_pages': pages, 'original_pdf_product_pages': [p + 2 for p in pages], 'extraction_pdf_page': pdf_page})
    return {'watch_rows': watches, 'clock_rows': clocks}

def expand_pages(value):
    result = []
    for part in value.split('/'):
        if '-' in part:
            start, end = map(int, part.split('-'))
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    text = subprocess.check_output(['pdftotext', '-layout', args.pdf, '-'], text=True)
    data = parse_text(text)
    Path(args.output).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({key: len(rows) for key, rows in data.items()}))
