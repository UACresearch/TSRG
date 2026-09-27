#!/usr/bin/env python3
"""Stream one Kaggle dataset snapshot into an existing private GitHub Release.

No full ZIP on disk: 900 MiB pieces are uploaded, verified, and removed one by one.
Do not treat this new server-produced ZIP as byte-identical to an older local ZIP.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

import requests

CHUNK = 900 * 1024 * 1024
READ = 4 * 1024 * 1024
TAG = 'archive-20260927'
REPO = 'caolitong0717/TSRG'
DATASETS = {
    'geometry': 'caolitong/tourism-puffin-geometry-training',
    'radio': 'caolitong/tourism-puffin-m1-v3-radio-cache-742',
}
API = 'https://api.github.com'
KAGGLE = 'https://www.kaggle.com/api/v1/datasets'


def gh_headers():
    token = os.environ['GH_TOKEN']
    return {'Authorization': 'Bearer ' + token,
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'}


def kaggle_headers():
    return {'Authorization': 'Bearer ' + os.environ['KAGGLE_API_TOKEN'],
            'Accept-Encoding': 'identity'}


def get_json(url, headers):
    result = requests.get(url, headers=headers, timeout=(30, 120))
    result.raise_for_status()
    return result.json()


def get_version(dataset, headers, explicit):
    if explicit:
        version = int(explicit)
        if version < 1:
            raise ValueError('version must be positive')
        return version, {'version_source': 'workflow input'}
    metadata = get_json(KAGGLE + '/view/' + dataset, headers)
    version = metadata.get('currentVersionNumber') or metadata.get('versionNumber')
    if not version and isinstance(metadata.get('currentVersion'), dict):
        version = metadata['currentVersion'].get('versionNumber')
    if version is None:
        raise RuntimeError('Could not determine Kaggle dataset version. Set version input manually. Dataset keys: ' + ','.join(metadata.keys()))
    version = int(version)
    if version < 1:
        raise RuntimeError('Invalid Kaggle version')
    return version, {'version_source': 'Kaggle dataset metadata'}


def asset_map(release):
    all_assets = {}
    n = 1
    while True:
        page = get_json(f'{API}/repos/{REPO}/releases/{release["id"]}/assets?per_page=100&page={n}', gh_headers())
        for asset in page:
            all_assets[asset['name']] = asset
        if len(page) < 100:
            return all_assets
        n += 1


def verify_asset(release, path, digest):
    asset = asset_map(release).get(path.name)
    if asset is None:
        return False
    if asset.get('state') != 'uploaded' or asset.get('size') != path.stat().st_size:
        raise RuntimeError(f'Release asset already exists but is incomplete or has different size: {path.name}')
    remote_digest = asset.get('digest')
    if not remote_digest:
        raise RuntimeError(f'Release asset {path.name} exists without an API SHA256 digest; will not silently overwrite it.')
    if remote_digest.lower() != 'sha256:' + digest.lower():
        raise RuntimeError(f'Release asset already exists with a DIFFERENT SHA256: {path.name}')
    print(f'Existing asset verified: {path.name}', flush=True)
    return True


def upload(release, path, digest):
    if verify_asset(release, path, digest):
        return
    # Do not use --clobber: it deletes existing valid assets before re-uploading.
    for attempt in range(1, 4):
        print(f'Uploading {path.name}, attempt {attempt}/3...', flush=True)
        done = subprocess.run(['gh', 'release', 'upload', TAG, str(path), '-R', REPO], check=False)
        if done.returncode == 0:
            for _ in range(8):
                time.sleep(2)
                try:
                    if verify_asset(release, path, digest):
                        return
                except RuntimeError as e:
                    if 'without an API SHA256 digest' not in str(e):
                        raise
            raise RuntimeError('Upload succeeded but GitHub digest was unavailable; stop for manual inspection.')
        time.sleep(attempt * 5)
        if verify_asset(release, path, digest):
            return
    raise RuntimeError('Upload failed after retries: ' + path.name)


def stream_archive(dataset, version, stage, release, version_detail):
    url = f'{KAGGLE}/download/{dataset}'
    headers = kaggle_headers()
    archive_name = f'TSRG_Kaggle_{stage}_v{version}_download.zip'
    manifest_name = f'TSRG_Kaggle_{stage}_v{version}_MANIFEST.json'
    parts = []
    full = hashlib.sha256()
    total = 0
    first = bytearray()
    expected_size = None
    with requests.get(url, params={'datasetVersionNumber': version}, headers=headers,
                      stream=True, allow_redirects=True, timeout=(60, 300)) as response:
        response.raise_for_status()
        if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
            raise RuntimeError('HTTP response encoded unexpectedly; cannot guarantee original ZIP payload.')
        if response.headers.get('Content-Length'):
            expected_size = int(response.headers['Content-Length'])
        print(f'Kaggle returned HTTP {response.status_code}; streaming version {version}.', flush=True)
        with tempfile.TemporaryDirectory(prefix='tsrg_cloud_archive_') as tmp:
            part_file = None
            part_path = None
            part_hash = None
            current = 0
            index = 0

            def finalize():
                nonlocal part_file, part_path, part_hash, current
                if part_file is None:
                    return
                part_file.close()
                digest = part_hash.hexdigest()
                info = {'name': part_path.name, 'bytes': current, 'sha256': digest, 'sequence': index}
                upload(release, part_path, digest)
                parts.append(info)
                print('Uploaded and checked:', part_path.name, current, digest, flush=True)
                part_path.unlink()
                part_file = None
                current = 0

            for block in response.iter_content(chunk_size=READ):
                if not block:
                    continue
                if len(first) < 4:
                    first.extend(block[:4-len(first)])
                    if len(first) == 4 and first[:2] != b'PK':
                        raise RuntimeError('Kaggle response is not a ZIP archive; refusing to upload error pages.')
                full.update(block)
                total += len(block)
                offset = 0
                while offset < len(block):
                    if part_file is None:
                        index += 1
                        part_path = pathlib.Path(tmp) / f'{archive_name}.part{index:03d}'
                        part_file = part_path.open('xb')
                        part_hash = hashlib.sha256()
                    count = min(CHUNK - current, len(block) - offset)
                    piece = memoryview(block)[offset:offset+count]
                    part_file.write(piece)
                    part_hash.update(piece)
                    current += count
                    offset += count
                    if current == CHUNK:
                        finalize()
            finalize()
            if total < 4 or not parts:
                raise RuntimeError('Empty or malformed download')
            if expected_size is not None and expected_size != total:
                raise RuntimeError(f'Unexpected Content-Length: expected {expected_size}, got {total}')
            manifest = {
                'schema': 'TSRG-Kaggle-stream-split-v1',
                'kaggle_dataset': dataset,
                'kaggle_dataset_version': version,
                **version_detail,
                'source_download_endpoint': url,
                'downloaded_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                'archive_name_when_reconstructed': archive_name,
                'archive_bytes': total,
                'archive_sha256': full.hexdigest(),
                'chunk_bytes': CHUNK,
                'parts': parts,
                'note': ('Hash is of the fresh server-produced Kaggle ZIP byte stream, '
                         'not necessarily the same ZIP bytes as a previously downloaded local archive. '
                         'Individual ZIP member CRC checks are NOT performed by this streaming operation.'),
                'restore': 'Download every part, concatenate in numeric .part order, then compare ZIP SHA256 to archive_sha256.'
            }
            mp = pathlib.Path(tmp) / manifest_name
            mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            upload(release, mp, hashlib.sha256(mp.read_bytes()).hexdigest())
            print('BACKUP SUCCESS', json.dumps({'dataset': dataset, 'version': version,
                                                'parts': len(parts), 'bytes': total,
                                                'sha256': full.hexdigest(), 'manifest': manifest_name}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True, choices=DATASETS)
    parser.add_argument('--version', default='', help='Optional explicit Kaggle dataset version number')
    args = parser.parse_args()
    if not os.getenv('KAGGLE_API_TOKEN') or not os.getenv('GH_TOKEN'):
        raise RuntimeError('Missing Kaggle API token or GitHub Actions token. Store Kaggle token only in GitHub Actions Secrets.')
    repository = get_json(f'{API}/repos/{REPO}', gh_headers())
    if not repository.get('private'):
        raise RuntimeError('Repository is not private. Aborting transfer to avoid unauthorized disclosure.')
    release = get_json(f'{API}/repos/{REPO}/releases/tags/{TAG}', gh_headers())
    if release.get('draft'):
        raise RuntimeError('Expected the existing published private release.')
    dataset = DATASETS[args.dataset]
    version, info = get_version(dataset, kaggle_headers(), args.version)
    print(f'Target: {args.dataset}; Kaggle dataset version {version}; release {TAG}.', flush=True)
    stream_archive(dataset, version, args.dataset, release, info)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('BACKUP FAILED:', type(exc).__name__, str(exc), file=sys.stderr, flush=True)
        sys.exit(1)
