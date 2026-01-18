#!/usr/bin/env python3
import os, sys, json, re
from simperium.core import Api as SimperiumApi


def load_env(env_path=None):
    """Load environment variables from .env file"""
    if env_path is None:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def extract_filename(content, note_id):
    """ノート内容からファイル名を生成（#見出し優先、なければ最初の行）"""
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        # #見出しの場合は#を除去
        if line.startswith('#'):
            title = line.lstrip('#').strip()
        else:
            title = line
        # 禁止文字を置換
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = safe_title[:100]  # 長すぎる場合は切り詰め
        if safe_title:
            return safe_title
    return note_id  # 空のノートの場合のみIDを使用


def get_unique_filepath(dir_path, base_name, ext):
    """重複時に連番を付与してユニークなパスを返す"""
    path = os.path.join(dir_path, base_name + ext)
    if not os.path.exists(path):
        return path
    counter = 1
    while True:
        path = os.path.join(dir_path, f"{base_name}_{counter}{ext}")
        if not os.path.exists(path):
            return path
        counter += 1

load_env()

appname = 'chalk-bump-f49'  # Simplenote
token = os.environ.get('TOKEN')
if not token:
    print("Error: TOKEN not found. Set TOKEN in .env file or environment variable.")
    sys.exit(1)
backup_dir = sys.argv[1] if len(sys.argv) > 1 else (os.path.join(os.environ['HOME'], "Dropbox/SimplenoteBackups"))
print("Starting backup your simplenote to: %s" % backup_dir)
if not os.path.exists(backup_dir):
    print("Creating directory: %s" % backup_dir)
    os.makedirs(backup_dir)

api = SimperiumApi(appname, token)
#print token

dump = api.note.index(data=True)
index = dump['index']
# the dump might be paged; go through all the pages
while 'mark' in dump:
    dump = api.note.index(data=True, mark=dump['mark'])
    index = index + dump['index']

trashed = 0
for note in index:
    dir_path = backup_dir
    #if the note was trashed, put it into a 'TRASH' subdirectory
    if note['d']['deleted']== True:
        dir_path = os.path.join(dir_path, 'TRASH')
        trashed = trashed + 1

    #if the note has a single tag, put it into a subdirectory named as the tag
    if len(note['d']['tags'])==1:
        dir_path = os.path.join(dir_path, note['d']['tags'][0])

    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno == 17:
            # the subdir already exists
            pass

    filename = extract_filename(note['d']['content'], note['id'])
    path = get_unique_filepath(dir_path, filename, '.md')
    #print path
    with open(path, "w", encoding='utf-8') as f:
        # print json.dumps(note, indent=2)
        #f.write("id: %s\n" % note['id'])
        f.write(note['d']['content'])
        f.write("\n")
        f.write("Tags: %s\n" % ", ".join(note['d']['tags']))
        # record pinned notes and whatever else
        if len(note['d']['systemTags'])>0:
            f.write("System tags: %s\n" % ", ".join(note['d']['systemTags']))
    os.utime(path,(note['d']['modificationDate'],note['d']['modificationDate']))

print("Done: %d files (%d in TRASH)." % (len(index), trashed))
