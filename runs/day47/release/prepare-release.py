"""Prepare the seven-file Day47 release against the fresh server snapshot."""
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
from datetime import datetime, timezone
from urllib.parse import quote

root = Path(__file__).resolve().parents[3]
release = Path(__file__).resolve().parent
snapshot = json.loads((release / 'server-before/snapshot.json').read_text())
manifest = json.loads((root / 'xhs/day47/manifest.json').read_text())
paths = manifest['paths']
sha = lambda data: hashlib.sha256(data).hexdigest()
course, thumbnail, detail = paths['html'], paths['thumbnail'], paths['detail']
webp = str(Path(thumbnail).with_suffix('.webp'))
assert sha((root / 'html/assets/fitness-study-logo-open-circle.svg').read_bytes()) == snapshot['html/assets/fitness-study-logo-open-circle.svg']['sha256']
assert 'Day 47 · 速度敏捷SAQ训练' in (root / course).read_text()
assert json.loads((root / 'runs/day47/verification/report.json').read_text())['status'] == 'passed'
for name, record in json.loads((root / 'runs/day47/finish-20260927/delivery-hashes.json').read_text()).items():
    assert sha((root / name).read_bytes()) == record['sha256'], name

app = (release / 'server-before/app.js').read_text()
library = (release / 'server-before/library-index.html').read_text()
assert sha(app.encode()) == snapshot['app.js']['sha256']
assert sha(library.encode()) == snapshot['library/index.html']['sha256']
assert 'publishedPages.set(47,' not in app
previous_course = next(line for line in app.splitlines() if line.startswith('publishedPages.set(46,'))
app = app.replace(previous_course, previous_course + '\npublishedPages.set(47, ' + json.dumps(course) + ');', 1)
previous_thumbnail = '  [46, "html/thumbs/day46-soft-tissue-release-smr-thumbnail.png"],'
assert app.count(previous_thumbnail) == 1
app = app.replace(previous_thumbnail, previous_thumbnail + '\n  [47, ' + json.dumps(thumbnail) + '],', 1)
assert len(re.findall(r'app\.js\?v=[a-f0-9]+', library)) == 1
library = re.sub(r'app\.js\?v=[a-f0-9]+', 'app.js?v=' + sha(app.encode())[:12], library)
target = '../../' + quote(course, safe='/')
shortlink = f'''<!doctype html>
<html lang="zh-CN"><head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta http-equiv="refresh" content="0; url={target}" />
<meta name="robots" content="noindex" />
<title>正在前往 Day 47</title>
<link rel="icon" type="image/svg+xml" href="../../html/assets/fitness-study-logo-open-circle.svg?v=a6d8e5caaa61" />
<script>window.location.replace({json.dumps(target)});</script>
</head><body><p>正在前往 <a href="{target}">Day 47 课程页</a>。</p></body></html>
'''
payload = {name: (root / name).read_bytes() for name in [thumbnail, webp, detail, course]}
payload.update({'go/47/index.html': shortlink.encode(), 'app.js': app.encode(), 'library/index.html': library.encode()})
staged = release / 'staged-site'
for name, data in payload.items():
    output = staged / ('library-index.html' if name == 'library/index.html' else name)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
release_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-day47'
result = {'releaseId': release_id, 'day': 47, 'acceptedRevision': 'saq-draft-completed-20260927-caption-saq-explained', 'publicUrl': 'https://fitstudy.cn/go/47/', 'files': [
    {'path': name, 'bytes': len(data), 'sha256': sha(data), 'previousSha256': snapshot[name]['sha256']} for name, data in payload.items()
]}
manifest_bytes = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
(release / 'release-manifest.json').write_bytes(manifest_bytes)
with tarfile.open(release / 'day47-site.tar.gz', 'w:gz') as tar:
    for name, data in {'release-manifest.json': manifest_bytes, **payload}.items():
        info = tarfile.TarInfo(name)
        info.size, info.mode = len(data), 0o644
        tar.addfile(info, io.BytesIO(data))
with tarfile.open(release / 'day47-site.tar.gz') as tar:
    assert set(tar.getnames()) == {'release-manifest.json', *payload}
print(json.dumps({'releaseId': release_id, 'files': len(payload), 'status': 'prepared'}))
