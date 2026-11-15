"""Package the static beta browser with the committed catalog and CSV snapshot."""
import argparse
import shutil
from pathlib import Path


def build(output):
    root = Path(__file__).resolve().parent
    output = Path(output).resolve()
    protected = [root / p for p in ('data', 'web', 'imports', 'research')]
    if output == root or any(output == p or p in output.parents or output in p.parents for p in protected):
        raise ValueError('Output cannot replace repository sources')
    output.mkdir(parents=True, exist_ok=True)
    for name in ('index.html', 'style.css', 'app.mjs', 'core.mjs', 'decoder.mjs', 'prefix-data.mjs', 'brand-emblem.svg', 'parts.mjs', 'decoder-presentation.mjs', 'model-references.mjs', 'research-prefix-data.mjs', 'decoder-rules.mjs'):
        shutil.copyfile(root / 'web' / name, output / name)
    for name in ('catalog.json', 'watches.csv', 'parts-links.json', 'official-product-links.json', 'model-references.json'):
        shutil.copyfile(root / 'data' / name, output / name)
    print(f'Browser packaged at {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='build/site')
    build(parser.parse_args().output)
