#!/usr/bin/env python3
"""
Simplenote Classify Script
Manages classification of untagged notes and file renaming.
"""
import os
import sys
import re
import json
import shutil


def get_default_backup_dir():
    """Get default backup directory"""
    return os.path.join(os.environ['HOME'], 'Dropbox/SimplenoteBackups')


def extract_title_from_content(content):
    """Extract title from first # heading or first line"""
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            title = line.lstrip('#').strip()
            # Sanitize for filename
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
            safe_title = safe_title[:100]
            if safe_title:
                return safe_title
        elif line and not line.startswith('Tags:') and not line.startswith('System tags:'):
            # Use first non-empty, non-tag line
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', line)
            safe_title = safe_title[:100]
            if safe_title:
                return safe_title
    return None


def parse_note_file(filepath):
    """Parse a note file and extract content and tags"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    tags = []
    system_tags = []
    content_lines = []

    for line in lines:
        if line.startswith('Tags: '):
            tag_str = line[6:].strip()
            if tag_str:
                tags = [t.strip() for t in tag_str.split(',') if t.strip()]
        elif line.startswith('System tags: '):
            tag_str = line[13:].strip()
            if tag_str:
                system_tags = [t.strip() for t in tag_str.split(',') if t.strip()]
        else:
            content_lines.append(line)

    # Remove trailing empty lines from content
    while content_lines and content_lines[-1] == '':
        content_lines.pop()

    return {
        'content': '\n'.join(content_lines),
        'tags': tags,
        'system_tags': system_tags,
        'filepath': filepath
    }


def get_existing_tags(backup_dir):
    """Get list of existing tag directories"""
    tags = []
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if os.path.isdir(item_path) and item != 'TRASH':
            tags.append(item)
    return sorted(tags)


def list_unclassified(backup_dir):
    """List files that need classification (no tags or ID-named)"""
    unclassified = []

    for filename in os.listdir(backup_dir):
        if not filename.endswith('.md'):
            continue
        filepath = os.path.join(backup_dir, filename)
        if os.path.isdir(filepath):
            continue

        note = parse_note_file(filepath)

        # Check if needs classification
        needs_tag = len(note['tags']) == 0
        # Check if filename is a hash (32 hex chars)
        basename = os.path.splitext(filename)[0]
        is_hash_name = bool(re.match(r'^[0-9a-f]{32}$', basename))

        if needs_tag or is_hash_name:
            unclassified.append({
                'filename': filename,
                'filepath': filepath,
                'content': note['content'],
                'tags': note['tags'],
                'needs_tag': needs_tag,
                'needs_rename': is_hash_name,
                'has_existing_tag': False
            })

    return unclassified


def list_all_root_files(backup_dir):
    """List ALL .md files in root directory (including tagged ones not yet moved)"""
    files = []

    for filename in os.listdir(backup_dir):
        if not filename.endswith('.md'):
            continue
        filepath = os.path.join(backup_dir, filename)
        if os.path.isdir(filepath):
            continue

        note = parse_note_file(filepath)

        # Check various states
        needs_tag = len(note['tags']) == 0
        basename = os.path.splitext(filename)[0]
        is_hash_name = bool(re.match(r'^[0-9a-f]{32}$', basename))
        has_existing_tag = len(note['tags']) > 0

        files.append({
            'filename': filename,
            'filepath': filepath,
            'content': note['content'],
            'tags': note['tags'],
            'needs_tag': needs_tag,
            'needs_rename': is_hash_name,
            'has_existing_tag': has_existing_tag
        })

    return files


def organize_tagged(backup_dir):
    """Move files that already have tags to their tag directories"""
    moved_count = 0

    for filename in os.listdir(backup_dir):
        if not filename.endswith('.md'):
            continue
        filepath = os.path.join(backup_dir, filename)
        if os.path.isdir(filepath):
            continue

        note = parse_note_file(filepath)

        # Skip files without tags
        if not note['tags']:
            continue

        # Use first tag as destination
        first_tag = note['tags'][0]
        tag_dir = os.path.join(backup_dir, first_tag)

        # Create tag directory if needed
        os.makedirs(tag_dir, exist_ok=True)

        # Move file
        dst_path = os.path.join(tag_dir, filename)
        counter = 1
        base, ext = os.path.splitext(filename)
        while os.path.exists(dst_path):
            dst_path = os.path.join(tag_dir, f"{base}_{counter}{ext}")
            counter += 1

        shutil.move(filepath, dst_path)
        print(f"Organized: {filename} -> {first_tag}/{os.path.basename(dst_path)}")
        moved_count += 1

    return moved_count


def apply_tag(backup_dir, filename, new_tag):
    """Apply a tag to a note file - move to tag directory and update Tags line"""
    src_path = os.path.join(backup_dir, filename)
    if not os.path.exists(src_path):
        print(f"Error: File not found: {src_path}")
        return False

    # Create tag directory if needed
    tag_dir = os.path.join(backup_dir, new_tag)
    os.makedirs(tag_dir, exist_ok=True)

    # Read and update content
    note = parse_note_file(src_path)

    # Update tags
    if new_tag not in note['tags']:
        note['tags'].append(new_tag)

    # Determine new filename
    new_filename = filename
    basename = os.path.splitext(filename)[0]
    if re.match(r'^[0-9a-f]{32}$', basename):
        # Need to rename
        title = extract_title_from_content(note['content'])
        if title:
            new_filename = title + '.md'

    # Build new content
    new_content = note['content']
    if not new_content.endswith('\n'):
        new_content += '\n'
    new_content += '\n'
    new_content += f"Tags: {', '.join(note['tags'])}\n"
    if note['system_tags']:
        new_content += f"System tags: {', '.join(note['system_tags'])}\n"

    # Get unique filepath in destination
    dst_path = os.path.join(tag_dir, new_filename)
    counter = 1
    while os.path.exists(dst_path):
        name, ext = os.path.splitext(new_filename)
        dst_path = os.path.join(tag_dir, f"{name}_{counter}{ext}")
        counter += 1

    # Write to new location
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # Preserve modification time
    stat = os.stat(src_path)
    os.utime(dst_path, (stat.st_mtime, stat.st_mtime))

    # Remove original
    os.remove(src_path)

    print(f"Moved: {filename} -> {new_tag}/{os.path.basename(dst_path)}")
    return True


def rename_file(backup_dir, old_filename, new_title):
    """Rename a file based on new title"""
    src_path = os.path.join(backup_dir, old_filename)
    if not os.path.exists(src_path):
        print(f"Error: File not found: {src_path}")
        return False

    # Sanitize title for filename
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', new_title)
    safe_title = safe_title[:100]
    new_filename = safe_title + '.md'

    dst_path = os.path.join(backup_dir, new_filename)
    counter = 1
    while os.path.exists(dst_path):
        dst_path = os.path.join(backup_dir, f"{safe_title}_{counter}.md")
        counter += 1

    shutil.move(src_path, dst_path)
    print(f"Renamed: {old_filename} -> {os.path.basename(dst_path)}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 simplenote-classify.py list [backup_dir]")
        print("  python3 simplenote-classify.py tags [backup_dir]")
        print("  python3 simplenote-classify.py apply <filename> <tag> [backup_dir]")
        print("  python3 simplenote-classify.py rename <filename> <new_title> [backup_dir]")
        print("  python3 simplenote-classify.py json [backup_dir]  # JSON output for Claude")
        print("  python3 simplenote-classify.py organize [backup_dir]  # Move tagged files to tag dirs")
        print("  python3 simplenote-classify.py status [backup_dir]  # Show all root files status")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'list':
        backup_dir = sys.argv[2] if len(sys.argv) > 2 else get_default_backup_dir()
        unclassified = list_unclassified(backup_dir)
        print(f"Found {len(unclassified)} files needing classification:\n")
        for note in unclassified[:50]:  # Limit output
            status = []
            if note['needs_tag']:
                status.append("needs tag")
            if note['needs_rename']:
                status.append("needs rename")
            print(f"  {note['filename']} ({', '.join(status)})")
            # Show first line of content
            first_line = note['content'].split('\n')[0][:60]
            print(f"    -> {first_line}...")
        if len(unclassified) > 50:
            print(f"\n  ... and {len(unclassified) - 50} more files")

    elif command == 'tags':
        backup_dir = sys.argv[2] if len(sys.argv) > 2 else get_default_backup_dir()
        tags = get_existing_tags(backup_dir)
        print("Existing tags:")
        for tag in tags:
            print(f"  - {tag}")

    elif command == 'apply':
        if len(sys.argv) < 4:
            print("Usage: python3 simplenote-classify.py apply <filename> <tag> [backup_dir]")
            sys.exit(1)
        filename = sys.argv[2]
        tag = sys.argv[3]
        backup_dir = sys.argv[4] if len(sys.argv) > 4 else get_default_backup_dir()
        apply_tag(backup_dir, filename, tag)

    elif command == 'rename':
        if len(sys.argv) < 4:
            print("Usage: python3 simplenote-classify.py rename <filename> <new_title> [backup_dir]")
            sys.exit(1)
        filename = sys.argv[2]
        new_title = sys.argv[3]
        backup_dir = sys.argv[4] if len(sys.argv) > 4 else get_default_backup_dir()
        rename_file(backup_dir, filename, new_title)

    elif command == 'json':
        backup_dir = sys.argv[2] if len(sys.argv) > 2 else get_default_backup_dir()
        all_root_files = list_all_root_files(backup_dir)
        existing_tags = get_existing_tags(backup_dir)

        # Separate by type
        needs_classification = [f for f in all_root_files if f['needs_tag']]
        has_tag_not_moved = [f for f in all_root_files if f['has_existing_tag']]

        # Output JSON for Claude to analyze
        output = {
            'existing_tags': existing_tags,
            'root_files_total': len(all_root_files),
            'needs_classification_count': len(needs_classification),
            'has_tag_not_moved_count': len(has_tag_not_moved),
            'notes': []
        }

        # Add files needing classification first
        for note in needs_classification[:100]:
            output['notes'].append({
                'filename': note['filename'],
                'needs_tag': note['needs_tag'],
                'needs_rename': note['needs_rename'],
                'has_existing_tag': note['has_existing_tag'],
                'existing_tags': note['tags'],
                'content_preview': note['content'][:500]
            })

        # Add tagged but not moved files
        for note in has_tag_not_moved[:20]:
            output['notes'].append({
                'filename': note['filename'],
                'needs_tag': False,
                'needs_rename': note['needs_rename'],
                'has_existing_tag': True,
                'existing_tags': note['tags'],
                'content_preview': note['content'][:200]
            })

        print(json.dumps(output, ensure_ascii=False, indent=2))

    elif command == 'organize':
        backup_dir = sys.argv[2] if len(sys.argv) > 2 else get_default_backup_dir()
        moved = organize_tagged(backup_dir)
        print(f"\nOrganized {moved} files with existing tags.")

    elif command == 'status':
        backup_dir = sys.argv[2] if len(sys.argv) > 2 else get_default_backup_dir()
        all_files = list_all_root_files(backup_dir)
        needs_tag = [f for f in all_files if f['needs_tag']]
        has_tag = [f for f in all_files if f['has_existing_tag']]

        print(f"=== Root Directory Status ===")
        print(f"Total .md files in root: {len(all_files)}")
        print(f"  - Needs classification (no tag): {len(needs_tag)}")
        print(f"  - Has tag but not moved: {len(has_tag)}")
        print()

        if has_tag:
            print("Files with tags (run 'organize' to move):")
            for f in has_tag[:10]:
                print(f"  {f['filename']} -> {f['tags'][0]}")
            if len(has_tag) > 10:
                print(f"  ... and {len(has_tag) - 10} more")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
