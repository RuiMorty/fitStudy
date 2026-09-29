"""Build the seven-file Day48 release from the current server snapshot."""
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tarfile
from datetime import datetime, timezone
from urllib.parse import quote

root = Path(__file__).resolve().parents[3]
release = Path(__file__).resolve().parent
snapshot = json.loads((release / 'server-before/snapshot.json').read_text())['files']
sha = lambda data: hashlib.sha256(data).hexdigest()
manifest = json.loads((root / 'xhs/day48/manifest.json').read_text())
status = json.loads((root / 'runs/day48/status.json').read_text())
paths = manifest['paths']
course, thumbnail, detail = paths['html'], paths['thumbnail'], paths['detail']
webp = str(Path(thumbnail).with_suffix('.webp'))

assert manifest['day'] == 48 and manifest['status'] == 'ready'
assert manifest['deliveryMode'] == 'local-draft' and manifest['publishApproved'] is False
assert status['status'] == 'awaiting-review' and status['localVerification'] == 'passed'
assert json.loads((root / 'runs/day48/verification/report.json').read_text())['status'] == 'passed'
assert sha((root / 'html/assets/fitness-study-logo-open-circle.svg').read_bytes()) == snapshot['html/assets/fitness-study-logo-open-circle.svg']['sha256']
assert 'Day 48 · 热身设计与整理恢复' in (root / course).read_text()
assert (root / thumbnail).read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
assert (root / webp).read_bytes()[:4] == b'RIFF' and (root / webp).read_bytes()[8:12] == b'WEBP'
assert (root / detail).read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'

base_app = (release / 'server-before/app.js').read_text()
base_library = (release / 'server-before/index.html').read_text()
assert sha(base_app.encode()) == snapshot['app.js']['sha256']
assert sha(base_library.encode()) == snapshot['library/index.html']['sha256']
assert 'publishedPages.set(48,' not in base_app
prior_course = next(line for line in base_app.splitlines() if line.startswith('publishedPages.set(47,'))
app = base_app.replace(prior_course, prior_course + '\npublishedPages.set(48, ' + json.dumps(course) + ');', 1)
prior_thumbnail = '  [47, "html/thumbs/day47-speed-agility-saq-thumbnail.png"],'
assert app.count(prior_thumbnail) == 1
app = app.replace(prior_thumbnail, prior_thumbnail + '\n  [48, ' + json.dumps(thumbnail) + '],', 1)
assert len(re.findall(r'app\.js\?v=[a-f0-9]+', base_library)) == 1
library = re.sub(r'app\.js\?v=[a-f0-9]+', 'app.js?v=' + sha(app.encode())[:12], base_library)

target = '../../' + quote(course, safe='/')
shortlink = f'''<!doctype html>
<html lang="zh-CN"><head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta http-equiv="refresh" content="0; url={target}" />
<meta name="robots" content="noindex" />
<title>正在前往 Day 48</title>
<link rel="icon" type="image/svg+xml" href="../../html/assets/fitness-study-logo-open-circle.svg?v=a6d8e5caaa61" />
<script>window.location.replace({json.dumps(target)});</script>
</head><body><p>正在前往 <a href="{target}">Day 48 课程页</a>。</p></body></html>
'''
payload = {name: (root / name).read_bytes() for name in [thumbnail, webp, detail, course]}
payload.update({'go/48/index.html': shortlink.encode(), 'app.js': app.encode(), 'library/index.html': library.encode()})
assert set(payload) == {thumbnail, webp, detail, course, 'go/48/index.html', 'app.js', 'library/index.html'}

staged = release / 'staged-site'
if staged.exists():
    shutil.rmtree(staged)
for name, data in payload.items():
    output = staged / ('library-index.html' if name == 'library/index.html' else name)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)

release_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-day48'
result = {
    'releaseId': release_id,
    'day': 48,
    'acceptedRevision': 'revision-01-expanded-xhs-explanations',
    'publicUrl': 'https://fitstudy.cn/go/48/',
    'files': [
        {'path': name, 'bytes': len(data), 'sha256': sha(data), 'previousSha256': snapshot[name]['sha256']}
        for name, data in payload.items()
    ]
}
manifest_bytes = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
(release / 'release-manifest.json').write_bytes(manifest_bytes)
with tarfile.open(release / 'day48-site.tar.gz', 'w:gz') as archive:
    for name, data in {'release-manifest.json': manifest_bytes, **payload}.items():
        entry = tarfile.TarInfo(name)
        entry.size, entry.mode = len(data), 0o644
        archive.addfile(entry, io.BytesIO(data))
with tarfile.open(release / 'day48-site.tar.gz') as archive:
    assert set(archive.getnames()) == {'release-manifest.json', *payload}
print(json.dumps({'releaseId': release_id, 'files': len(payload), 'status': 'prepared'}))
