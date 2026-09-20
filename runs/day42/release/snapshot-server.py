import base64
import hashlib
import json
from pathlib import Path

site = Path('/home/zhaoqr/fitness/site')
paths = [
    'html/thumbs/day42-upper-body-barbell-technique-thumbnail.png',
    'html/thumbs/day42-upper-body-barbell-technique-thumbnail.webp',
    'html/assets/阶段2训练科学/day42-自由重量-上肢杠铃技术.png',
    'html/day42-自由重量-上肢杠铃技术.html',
    'go/42/index.html', 'app.js', 'library/index.html',
    'html/assets/fitness-study-logo-open-circle.svg',
    'progress.json', '.progress.json',
    'html/day40-反馈与动作学习.html',
    'html/day41-自由重量-下肢杠铃技术.html',
]
result = {'site': str(site), 'files': {}}
for name in paths:
    path = site / name
    if not path.exists():
        result['files'][name] = None
        continue
    assert path.is_file() and not path.is_symlink(), name
    data = path.read_bytes()
    record = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if name in ('app.js', 'library/index.html'):
        record['base64'] = base64.b64encode(data).decode()
    result['files'][name] = record
print(json.dumps(result, ensure_ascii=False, indent=2))
