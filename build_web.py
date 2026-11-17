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
    import unified_index
    unified_index.write(root, check=True)
    protected = [root / p for p in ('data', 'web', 'imports', 'research')]
    if output == root or any(output == p or p in output.parents or output in p.parents for p in protected):
        raise ValueError('Output cannot replace repository sources')
    output.mkdir(parents=True, exist_ok=True)
    assets = ('official-support.mjs', 'model-identity-data.mjs', 'dw-heritage-interpretations.mjs', 'dw-heritage-data.mjs', 'regional-models.mjs', 'family-classification.mjs', 'ocean-wave-interpretations.mjs', 'ocean-wave-data.mjs', 'mud-frog-interpretations.mjs', 'mud-frog-data.mjs', 'series-interpretations.mjs', 'series-pdfs-data.mjs', 'video-families.mjs', 'lineage-interpretations.mjs', 'special-variants-data.mjs', 'metal-squares-data.mjs', 'module-comparison-data.mjs', 'research-pdfs-data.mjs', 'catalog-1983.mjs', 'catalog-1983-data.mjs', 'index.html', 'style.css', 'app.mjs', 'core.mjs', 'decoder.mjs', 'prefix-data.mjs', 'brand-emblem.svg', 'parts.mjs', 'decoder-presentation.mjs', 'model-references.mjs', 'research-prefix-data.mjs', 'decoder-rules.mjs', 'variant-interpretations.mjs', 'prefix-meanings.mjs', 'guide-interpretations.mjs', 'owner-prefix-readings.mjs', 'anniversary.mjs', 'anniversary-data.mjs', 'historical-review.mjs', 'combined-reference.mjs', 'protrek-reference.mjs', 'catalog-2011-reference.mjs', 'catalog-batch-reference.mjs', 'watchnavi-reference.mjs', 'watchnavi-search.mjs', 'master-research.mjs', 'english.mjs', 'specification-display.mjs', 'unified-search.mjs', 'awg-m520ua.mjs', 'creator-videos.mjs')
    datasets = ('catalog.json', 'watches.csv', 'parts-links.json', 'official-product-links.json', 'model-references.json', 'search-index.json', 'reconciliation-report.json', 'unified-models.csv')
    fingerprint = hashlib.sha256(Path(__file__).read_bytes())
    for folder, names in [('web', assets), ('data', datasets)]:
        for name in names:
            fingerprint.update(name.encode())
            fingerprint.update((root / folder / name).read_bytes())
            shutil.copyfile(root / folder / name, output / name)
    master_source = root / 'research/casio-master-research-2026-11-16.json'
    fingerprint.update(master_source.read_bytes())
    shutil.copyfile(master_source, output / 'master-research.json')
    reviews_path = root / 'reviews.json'
    if reviews_path.exists():
        references = sorted({review['evidence_reference'] for review in json.loads(reviews_path.read_text()) if review.get('evidence_reference')})
        for reference in references:
            relative = Path(reference)
            if relative.is_absolute() or '..' in relative.parts or not reference.startswith('research/') or relative.suffix != '.json':
                raise ValueError('Invalid review evidence path')
            source = root / relative
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            fingerprint.update(reference.encode())
            fingerprint.update(source.read_bytes())
            shutil.copyfile(source, destination)
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
    (output / 'build-info.json').write_text(json.dumps({'asset_version': version, 'search_index_sha256': hashlib.sha256((root / 'data/search-index.json').read_bytes()).hexdigest(), 'reconciliation_sha256': hashlib.sha256((root / 'data/reconciliation-report.json').read_bytes()).hexdigest(), 'individual_watch_identifiers': json.loads((root / 'data/search-index.json').read_text())['counts']['watch']}) + '\n')
    print(f'Browser packaged at {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='build/site')
    build(parser.parse_args().output)
