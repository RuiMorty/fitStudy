import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

release = Path(__file__).resolve().parent
manifest = json.loads((release / 'release-manifest.json').read_text())


def verify(record):
    url = 'https://fitstudy.cn/' + quote(record['path'], safe='/')
    if record['path'] == 'app.js':
        url += '?v=' + record['sha256'][:12]
    with urlopen(Request(url, headers={'User-Agent': 'FitStudy-Release-Verification/1.0'}), timeout=30) as response:
        data = response.read()
        result = {'path': record['path'], 'url': url, 'status': response.status, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    assert result['status'] == 200, result
    assert result['bytes'] == record['bytes'], result
    assert result['sha256'] == record['sha256'], result
    return result


with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(verify, manifest['files']))
report = {'status': 'passed', 'releaseId': manifest['releaseId'], 'checkedAt': datetime.now(timezone.utc).isoformat(), 'files': results}
(release / 'live-files-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('All seven public Day43 files return HTTP 200 and match the release SHA-256 hashes.')
