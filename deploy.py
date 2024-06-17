#!/usr/bin/env python3
import json
import os
import shutil
import subprocess

FILES = [
    '__init__.py',
    'outline_measure.py',
    'icon.png',
]


def get_version():
    return subprocess.check_output(['git', 'describe', '--tags', '--match', r'v*', '--always']).strip().decode('utf-8')[1:]


def make_metadata(version):
    with open('README.md', 'r') as f:
        readme = f.read()
    metadata = {
        "$schema": "https://go.kicad.org/pcm/schemas/v1",
        "name": "JLCPCB ",
        "description": "A plugin to create zip compressed gerber files to order PCB for JLCPCB.",
        "description_full": readme,
        "identifier": "com.github.macdems.KiCad-JLCPCB",
        "type": "plugin",
        "author": {
            "name": "Maciek Dems",
            "contact": {
                "web": "https://github.com/macdems"
            }
        },
        "maintainer": {
            "name": "Maciek Dems",
            "contact": {
                "web": "https://github.com/macdems"
            }
        },
        "license": "MIT",
        "resources": {
            "homepage": "https://github.com/macdems/KiCad-JLCPCB",
        },
        "versions": [
            {
                "version": version,
                "status": "stable",
                "kicad_version": "7.0",
            }
        ]
    }
    return metadata


os.remove('KiCad-JLCPCB.zip') if os.path.exists('KiCad-JLCPCB.zip') else None
shutil.rmtree('dist', ignore_errors=True)

os.makedirs(os.path.join('dist', 'plugins'))
os.makedirs(os.path.join('dist', 'resources'))

with open(os.path.join('dist', 'metadata.json'), 'w') as f:
    json.dump(make_metadata(get_version()), f, indent=4)

for file in FILES:
    shutil.copy(file, os.path.join('dist', 'plugins'))

shutil.copy('icon.png', os.path.join('dist', 'resources'))

os.chdir('dist')
subprocess.run(['zip', '-r', '../KiCad-JLCPCB.zip', '.'])
os.chdir('..')

print('Plugin created in KiCad-JLCPCB.zip')
