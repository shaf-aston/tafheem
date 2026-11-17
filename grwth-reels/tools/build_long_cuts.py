# Longer cuts: keep the whole point from each take, trim pauses, light overlays (~1 every 7 s) placed on spoken words.
import json, subprocess, re, sys
B = '/tmp/claude-0/-home-user-tafheem/8da1ac7c-cc1d-5ff9-b059-1539c9419264/scratchpad/grwth'
def norm(w): return re.sub(r"[^a-z0-9']", "", w.lower())
def C(name, word, ln, spec, n=1): return ('mg', name, word, n, ln, spec)
def R(src, frm, word, ln, n=1): return ('br', src, word, n, ln, frm)
END = None  # length "to end"
# reel: (source, out, start word time, end time, drop ranges in source seconds, items, word fixes)
P = {
'time-over-money': ('IMG_4549.MOV', 'v4', 1.0, 48.6, [], [
  C('t1', 'fancy', 3.2, 'FANCY CARS@0|LAMBORGHINIS@1.2:ice|FERRARIS@2.2:ice'),
  C('t2', 'high', 1.6, 'HIGH-TICKET@0|SALES@0.4:ice:big'),
  C('t3', 'friday', 1.6, 'FRIDAY@0|AFTERNOON@0.3:ice'),
  C('t5', 'chose', 1.6, 'I CHOSE@0|TO BE HERE@0.4:ice'),
  C('t6', 'valuing', END, 'VALUE YOUR@0|TIME@0.4:ice:big')], {}),
'pure-intent': ('IMG_4697.mov', 'v5', 11.74, 56.5, [], [
  C('p0', 'purpose', 1.6, 'STRONG@0|PURPOSE@0.3:ice:big'),
  C('p1', 'beyond', 1.6, 'BEYOND@0|MONEY@0.3:ice:big'),
  C('p2', 'greedy', 1.4, 'GREEDY@0:ice:big'),
  C('p5', 'community', 1.6, 'SERVE THE@0|COMMUNITY@0.3:ice'),
  C('p3', 'pure', 1.6, 'PURE@0|INTENT@0.3:ice:big'),
  C('p4', 'great', END, 'SOMETHING@0|GREAT@0.3:ice:big', 2)], {}),
'last-dollar': ('IMG_4702.mov', 'v6', 1.0, 54.0, [], [
  C('l1', 'conditioned', 1.4, 'CONDITIONED@0:ice:big'),
  C('l2', 'matrix', 1.4, 'THE SALES@0|MATRIX@0.2:ice:big'),
  C('l3', 'dire', 1.6, 'EXPLOITING@0|THEIR NEED@0.3:ice'),
  C('l4', 'gurus', 1.4, 'GURUS@0:ice:big'),
  C('l6', 'mindset', 1.6, 'THE MINDSET@0|THAT SERVES@0.3|YOU@0.5:ice:big'),
  C('l7', 'credit', 1.8, 'NO CREDIT@0|CARDS@0.3:ice:big|NO DEBT@0.9:ice:big')], {'excellency': 'excellence,'}),
'25k-not-salesy': ('IMG_4705.mov', 'v5', 0.0, 60.6, [(8.7, 11.3), (11.3, 13.4)], [
  C('k1', 'resistance', 2.2, 'SALES@0|RESISTANCE@0.15:ice|OBJECTIONS@1.0'),
  C('k3', 'fires', 1.6, 'PUTTING OUT@0|FIRES@0.3:ice:big'),
  C('k2', 'salesy', 1.6, 'NOT@0|SALESY@0.35:ice:big'),
  C('k6', 'human', 1.6, 'BE A@0|HUMAN BEING@0.3:ice'),
  C('k4', 'focused', 1.8, 'FOCUS ON@0|THE PERSON@0.4:ice:big'),
  C('k5', 'congruency', END, 'CONGRUENCY.@0:ice:big')], {'cool': 'congruency.'}),
'8k-no-sales-call': ('IMG_4708.MOV', 'v7', 1.7, 50.9, [], [
  C('e0', 'journey', 2.0, 'STEP 1@0|KNOW THEIR@0.3|JOURNEY@0.5:ice:big'),
  C('e1', 'terrible', 1.6, 'TERRIBLE@0|PRE-CALL@0.3:ice|PROCESS@0.5:ice'),
  C('e2', 'speed', 2.0, 'STEP 2@0|SPEED@0.3:ice:big|TO LEAD@0.5:ice:big'),
  C('e5', 'automated', 1.6, 'NO AUTOMATED@0|TEXTS@0.3:ice:big'),
  C('e6', 'application', 1.8, 'YOUR@0|APPLICATION@0.3:ice'),
  C('e3', 'golden', 2.0, 'STEP 3@0|GOLDEN@0.3:ice:big|QUESTION@0.5:ice:big'),
  C('e4', 'sold', 1.8, 'THE PROSPECT@0|SOLD@0.3:ice:big|HIMSELF@0.5:ice')], {}),
'close-anywhere': ('IMG_4712.MOV', 'v5', 0.8, 35.7, [(7.75, 11.1)], [
  C('c0', 'desk', 1.4, 'NO DESK@0|NEEDED@0.3:ice:big'),
  C('c1', 'walk', 1.4, 'OUT ON@0|A WALK@0.3:ice:big'),
  C('c4', 'skills', 1.6, 'THE RIGHT@0|SKILLS@0.3:ice:big'),
  C('c2', 'cap', 1.6, "DON'T CAP@0|YOURSELF@0.3:ice:big"),
  C('c3', 'simple', END, 'SIMPLE.@0:ice:big')], {}),
}

def segments(src, a, b, drops):
    w = [x for x in json.load(open(f'{B}/log/{src.rsplit(".",1)[0]}.words.json')) if x['s'] >= a and x['e'] <= b + 0.3
         and not any(d0 <= x['s'] < d1 for d0, d1 in drops)]
    segs, cur = [], [w[0]['s'] - 0.04, w[0]['e']]
    for x in w[1:]:
        if x['s'] - cur[1] > 0.45: segs.append(cur); cur = [x['s'] - 0.12, x['e']]   # trim pauses over 0.45 s
        else: cur[1] = x['e']
    segs.append(cur)
    return [{'src': f'../../src/{src}', 'in': round(max(0, s), 2), 'out': round(e + 0.15, 2), 'zoom': [1.0, 1.1][k % 2], 'y': [0.4, 0.55][k % 2]}
            for k, (s, e) in enumerate(segs)]

def find(words, word, n):
    hits = [x for x in words if norm(x['w']) == word or (word == 'congruency.' and norm(x['w']).startswith(word))]
    if not hits or len(hits) < n: sys.exit(f'word not found: {word} #{n}')
    return hits[n - 1 if n > 0 else n]['s']

for r in sys.argv[1:] or P:
    src, ver, a, b, drops, items, fixes = P[r]; d = f'{B}/reels/{r}'
    cfg = json.load(open(f'{d}/reel.json'))
    cfg['segments'] = segments(src, a, b, drops); cfg['out'] = f'2026-11-16-{r}-{ver}.mp4'
    cfg.pop('no_caps', None)
    if r == 'pure-intent': cfg['hook']['lines'] = []; cfg['tail'] = 0.6
    json.dump(cfg, open(f'{d}/reel.json', 'w'), indent=1)
    run = lambda *x: subprocess.run(['python3', 'reel_local.py', *x, 'reel.json'], cwd=d, check=True, capture_output=True)
    run('cut'); run('words')
    words = json.load(open(f'{d}/words.json'))
    for x in words:
        x['w'] = {'watcher,':'watches,','-tech':'-ticket','UN.':'US.','high':'high'}.get(x['w'], x['w'])
        if norm(x['w']) in fixes: x['w'] = fixes[norm(x['w'])]
    json.dump(words, open(f'{d}/words.json', 'w'), indent=1)
    end = words[-1]['e'] + 0.4; cuts = []
    for it in items:
        at = round(find(words, it[2], it[3]) - 0.05, 2); ln = it[4] or round(end - at + cfg['tail'] + 0.3, 2)
        if it[0] == 'mg':
            subprocess.run(['python3', f'{B}/tools/mg.py', f'{B}/mg/{it[1]}.mp4', str(ln + 0.1), it[5]], check=True, capture_output=True)
            cuts.append({'src': f'../../mg/{it[1]}.mp4', 'from': 0, 'len': ln, 'at': at, 'y': 0.5})
        else:
            cuts.append({'src': f'../../src/{it[1]}.mp4', 'from': it[5], 'len': ln, 'at': at, 'y': 0.5})
    cfg['cutaways'] = cuts; json.dump(cfg, open(f'{d}/reel.json', 'w'), indent=1)
    run('render')
    print(r, cfg['out'], 'gaps between overlays:', [round(cuts[i+1]['at'] - cuts[i]['at'], 1) for i in range(len(cuts) - 1)])
