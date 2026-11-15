"""Package the static beta browser with the committed catalog and CSV snapshot."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


def build(output):
    root = Path(__file__).resolve().parent
    output = Path(output).resolve()
    protected = [root / p for p in ('data', 'web', 'imports', 'research')]
    if output == root or any(output == p or p in output.parents or output in p.parents for p in protected):
        raise ValueError('Output cannot replace repository sources')
    output.mkdir(parents=True, exist_ok=True)
    assets = ('index.html', 'style.css', 'app.mjs', 'core.mjs', 'decoder.mjs', 'prefix-data.mjs', 'brand-emblem.svg', 'parts.mjs', 'decoder-presentation.mjs', 'model-references.mjs', 'research-prefix-data.mjs', 'decoder-rules.mjs', 'variant-interpretations.mjs', 'prefix-meanings.mjs', 'guide-interpretations.mjs')
    datasets = ('catalog.json', 'watches.csv', 'parts-links.json', 'official-product-links.json', 'model-references.json')
    fingerprint = hashlib.sha256(Path(__file__).read_bytes())
    for folder, names in [('web', assets), ('data', datasets)]:
        for name in names:
            fingerprint.update(name.encode())
            fingerprint.update((root / folder / name).read_bytes())
            shutil.copyfile(root / folder / name, output / name)
    version = fingerprint.hexdigest()[:16]
    # Version every module edge as well as the entrypoint, so cached dependencies
    # cannot leave a freshly published app running an older decoder.
    for name in assets:
        path = output / name
        if name.endswith('.mjs'):
            text = re.sub(r"(['\"])(\./[^'\"]+\.mjs)\1", lambda m: m[1] + m[2] + '?v=' + version + m[1], path.read_text())
            path.write_text(text)
    index = output / 'index.html'
    index.write_text(index.read_text().replace('src="app.mjs"', 'src="app.mjs?v=' + version + '"').replace('href="style.css"', 'href="style.css?v=' + version + '"'))
    (output / 'build-info.json').write_text(json.dumps({'asset_version': version}) + '\n')
    print(f'Browser packaged at {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='build/site')
    build(parser.parse_args().output)
