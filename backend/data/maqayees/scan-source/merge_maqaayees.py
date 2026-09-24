import json, glob, os, re, sys

# The summary at the foot prints Arabic letters, and a Windows console is
# cp1252 by default — without this the script does all its work and then dies
# on the last print, which reads as a failed run.
sys.stdout.reconfigure(encoding='utf-8')

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maqaayees_db')

files = [
    ('range_a_55_942.json', 'A'),
    ('range_b_943_1830.json', 'B'),
    ('range_c_1831_2716.json', 'C'),
]

all_entries = []
total_issues = 0
for fname, tag in files:
    with open(os.path.join(DB_DIR, fname), encoding='utf-8') as f:
        d = json.load(f)
    entries = d.get('entries', [])
    total_issues += len(d.get('issues_found', []))
    for e in entries:
        e['_range'] = tag
    all_entries.extend(entries)

# sort by pdf_page_index for stable reading order
all_entries.sort(key=lambda e: (e.get('pdf_page_index') or 0))

# group by first root letter (normalize alef variants to bare alef for grouping)
NORM = str.maketrans({'\u0623':'\u0627','\u0625':'\u0627','\u0622':'\u0627'})

def first_letter(root):
    root = (root or '').strip()
    return root[0].translate(NORM) if root else '_unknown'

groups = {}
for e in all_entries:
    letter = first_letter(e.get('root'))
    groups.setdefault(letter, []).append(e)

os.makedirs(os.path.join(DB_DIR, 'by_root_letter'), exist_ok=True)
manifest = {
    'source': "Ibn Faris, Maqaayees al-Lugha (مقاييس اللغة)",
    'pdf_range_covered': [55, 2716],
    'total_entries': len(all_entries),
    'total_audit_corrections': total_issues,
    'schema': {
        'root': 'root letters as printed',
        'root_letters': 'array of individual letters',
        'core_meaning': 'classical Arabic core meaning statement',
        'core_meaning_english': 'literal English gloss only, no grammar commentary',
        'sarf_pattern': 'Arabic morphology/sarf term if named (e.g. المضاعف), else empty',
        'variances': 'array of {usage, meaning, meaning_english, citation}',
        'printed_page_number': 'page number printed on the scanned page',
        'pdf_page_index': 'index into the source PDF',
        'notes': 'uncertainty/illegibility/continuation flags',
    },
    'files': [],
}

for letter, entries in sorted(groups.items()):
    entries.sort(key=lambda e: e.get('pdf_page_index') or 0)
    for e in entries:
        e.pop('_range', None)
    safe_name = f"root_{letter}.json" if letter != '_unknown' else "root__unknown.json"
    out_path = os.path.join(DB_DIR, 'by_root_letter', safe_name)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'root_letter': letter, 'entry_count': len(entries), 'entries': entries}, f, ensure_ascii=False, indent=1)
    manifest['files'].append({'file': f'by_root_letter/{safe_name}', 'root_letter': letter, 'entry_count': len(entries)})

with open(os.path.join(DB_DIR, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)

print('Total entries:', len(all_entries))
print('Total audit corrections:', total_issues)
print('Groups:', len(groups))
for letter, entries in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:10]:
    print(f'  {letter}: {len(entries)}')
