#!/usr/bin/env python3
"""Apply the Day43 scoped release only if every payload and remote base hash match."""
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def install(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.fitstudy-', dir=destination.parent)
    os.close(fd)
    try:
        shutil.copyfile(source, temporary)
        os.chmod(temporary, 0o644)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    if len(sys.argv) != 3:
        sys.exit('Usage: apply-release.py SITE_DIR ARCHIVE')
    site, archive = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    assert site.is_dir(), 'Site directory missing'
    with (site / '.fitstudy-publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
            assert len({member.name for member in members}) == len(members), 'Duplicate archive paths'
            assert all(member.isfile() for member in members), 'Only regular files allowed'
            manifest = json.load(tar.extractfile('release-manifest.json'))
            assert manifest['day'] == 43
            release_id = manifest['releaseId']
            assert release_id.replace('-', '').isalnum(), 'Invalid release ID'
            records = manifest['files']
            assert len(records) == 7
            assert set(member.name for member in members) == {'release-manifest.json', *(record['path'] for record in records)}
            payload, prior = {}, {}
            for record in records:
                name = record['path']
                pure = PurePosixPath(name)
                assert not pure.is_absolute() and '..' not in pure.parts
                target = site / name
                assert not target.is_symlink() and target.resolve().is_relative_to(site)
                content = tar.extractfile(name).read()
                assert len(content) == record['bytes'] and sha(content) == record['sha256'], name
                old = target.read_bytes() if target.exists() else None
                old_hash = sha(old) if old is not None else None
                assert old_hash in (record['previousSha256'], record['sha256']), f'Remote changed: {name}'
                prior[name], payload[name] = old, content

        if all(prior[record['path']] is not None and sha(prior[record['path']]) == record['sha256'] for record in records):
            print('All seven release files already match; no writes needed.')
            return

        backup_root = site.parent / '.fitstudy-deploy-backups'
        backup_root.mkdir(mode=0o700, exist_ok=True)
        backup = backup_root / release_id
        backup.mkdir(mode=0o700, exist_ok=False)
        (backup / 'release-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        absent = []
        for name, old in prior.items():
            if old is None:
                absent.append(name)
            else:
                saved = backup / name
                saved.parent.mkdir(parents=True, exist_ok=True)
                saved.write_bytes(old)
        (backup / 'previously-absent.json').write_text(json.dumps(absent))

        changed = []
        try:
            with tempfile.TemporaryDirectory(prefix='.day43-stage-', dir=site) as temporary:
                stage = Path(temporary)
                for record in records:
                    name = record['path']
                    source = stage / name
                    source.parent.mkdir(parents=True, exist_ok=True)
                    source.write_bytes(payload[name])
                    install(source, site / name)
                    changed.append(name)
                for record in records:
                    assert sha((site / record['path']).read_bytes()) == record['sha256']
                marker = stage / 'marker'
                marker.write_text(release_id + '\n')
                install(marker, site / '.deploy-day43-current')
        except BaseException:
            for name in reversed(changed):
                if prior[name] is None:
                    (site / name).unlink(missing_ok=True)
                else:
                    install(backup / name, site / name)
            raise
        print(f'Published Day43 release {release_id}; backup: {backup}')


if __name__ == '__main__':
    main()
