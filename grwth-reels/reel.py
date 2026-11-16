# GRWTH reel builder. One config file per reel; three steps:
#   python reel.py cut    reel.json   -> band.mp4   (clips joined, cropped to the 4:5 band, zooms applied)
#   python reel.py words  reel.json   -> words.json (word timings of band.mp4, free faster-whisper)
#   python reel.py render reel.json   -> <out>      (hook, captions, key words, cutaways, end card, loudness)
# Every look value lives in STYLE below; every per-reel value lives in reel.json.
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

STYLE = {
    "W": 1080, "H": 1920, "BAND_W": 1080, "BAND_H": 1350, "TOP": 285, "FPS": 30,
    "HOOK_RIGHT": 1010, "HOOK_Y": 325, "HOOK_SMALL": 54, "HOOK_BIG": 118,
    "CAP_SIZE": 70, "CAP_STROKE": 6, "CAP_Y": 0.66, "KEY_SIZE": 104, "KEY_LIFT": 40, "CAP_HOLD": 0.6,
    "ICE_TOP": (236, 247, 253), "ICE_BOT": (150, 205, 235),
    "CUTAWAY_DARKEN": -0.08, "LUFS": -14, "PEAK": -1.5, "FADE_OUT": 0.5,
    "END_SECONDS": 1.6, "END_LOGO_W": 560, "END_LOGO_Y": 820,
}

def ffmpeg(*a): subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)
def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True, check=True).stdout)
def norm(word): return re.sub(r"[^a-z0-9']", "", word.lower())

def font(cfg, kind, size):
    path = cfg["fonts"][kind]
    if not os.path.exists(path): sys.exit(f"Font not found: {path}. Fix 'fonts' in the config.")
    return ImageFont.truetype(path, size)

def ice(txt, f):
    b = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), txt, font=f); w, h = b[2], b[3]
    m = Image.new("L", (w, h)); ImageDraw.Draw(m).text((0, 0), txt, font=f, fill=255)
    g = Image.new("RGBA", (w, h)); dg = ImageDraw.Draw(g)
    for y in range(h):
        t = y / h
        dg.line([(0, y), (w, y)], fill=tuple(int(STYLE["ICE_TOP"][i] + (STYLE["ICE_BOT"][i] - STYLE["ICE_TOP"][i]) * t) for i in range(3)) + (255,))
    g.putalpha(m); return g

def fit_band(zoom, y):
    """Filter that scales any source to cover the band (times zoom) and crops it. y: 0 = keep top, 0.5 = centre, 1 = bottom."""
    bw, bh = STYLE["BAND_W"], STYLE["BAND_H"]
    return (f"scale={int(bw * zoom)}:{int(bh * zoom)}:force_original_aspect_ratio=increase,"
            f"crop={bw}:{bh}:(iw-{bw})/2:(ih-{bh})*{y},setsar=1,fps={STYLE['FPS']}")

def cut(cfg):
    ins, fc, parts = [], "", ""
    for k, s in enumerate(cfg["segments"]):
        ins += ["-i", s["src"]]
        fc += (f"[{k}:v]trim={s['in']}:{s['out']},setpts=PTS-STARTPTS,{fit_band(s.get('zoom', 1.0), s.get('y', 0.5))}[v{k}];"
               f"[{k}:a]atrim={s['in']}:{s['out']},asetpts=PTS-STARTPTS,volume={s.get('volume', 1.0)},aresample=48000[a{k}];")
        parts += f"[v{k}][a{k}]"
    fc += f"{parts}concat=n={len(cfg['segments'])}:v=1:a=1[v][a]"
    ffmpeg(*ins, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "band.mp4")
    print(f"band.mp4 written, {duration('band.mp4'):.2f} s")

def words(cfg):
    from faster_whisper import WhisperModel
    segs, _ = WhisperModel(cfg.get("whisper_model", "small"), compute_type="int8").transcribe("band.mp4", word_timestamps=True)
    out = [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)} for seg in segs for w in seg.words]
    json.dump(out, open("words.json", "w"), indent=1)
    print(" ".join(w["w"] for w in out)); print("Check every word above against what is said. Fix spellings in words.json by hand.")

def hook_pngs(cfg):
    small, big = font(cfg, "regular_bold", STYLE["HOOK_SMALL"]), font(cfg, "black", STYLE["HOOK_BIG"])
    lines = cfg["hook"]["lines"]; times = sorted({l["at"] for l in lines}); out = []
    for k, t in enumerate(times):
        im = Image.new("RGBA", (STYLE["W"], STYLE["H"])); d = ImageDraw.Draw(im); y = STYLE["HOOK_Y"]
        for l in lines:
            if l["at"] > t: break
            f = big if l["size"] == "big" else small; b = d.textbbox((0, 0), l["text"], font=f); yy = y - b[1]; x = STYLE["HOOK_RIGHT"] - b[2]
            if l.get("ice"): im.alpha_composite(ice(l["text"], f), (x, yy))
            else:
                d.text((x + 3, yy + 3), l["text"], font=f, fill=(0, 0, 0, 110)); d.text((x, yy), l["text"], font=f, fill="white")
            y += (b[3] - b[1]) + (16 if l["size"] == "big" else 12)
        p = f"ov/h{k}.png"; im.save(p); out.append((p, t, times[k + 1] if k + 1 < len(times) else cfg["hook"]["until"]))
    return out

def caption_pngs(cfg, end):
    cap, key = font(cfg, "black", STYLE["CAP_SIZE"]), font(cfg, "black", STYLE["KEY_SIZE"])
    keys = {norm(k): v for k, v in cfg.get("keys", {}).items()}
    w = [x for x in json.load(open("words.json")) if x["s"] >= cfg["captions_from"]]
    grp, i = [], 0
    while i < len(w):   # pair two short words unless a sentence ends or the next word is a key word
        if i + 1 < len(w) and len(w[i]["w"]) + len(w[i + 1]["w"]) <= 9 and not w[i]["w"].endswith((".", ",", "?", "!")) \
                and norm(w[i]["w"]) not in keys and norm(w[i + 1]["w"]) not in keys:
            grp.append((w[i]["w"] + " " + w[i + 1]["w"], w[i]["s"], w[i + 1]["e"])); i += 2
        else: grp.append((w[i]["w"], w[i]["s"], w[i]["e"])); i += 1
    out = []
    for k, (t, s, e) in enumerate(grp):
        nxt = grp[k + 1][1] if k + 1 < len(grp) else end
        colour = keys.get(norm(t)); f = key if colour else cap; tt = t.rstrip(".,")
        im = Image.new("RGBA", (STYLE["W"], STYLE["H"])); d = ImageDraw.Draw(im); b = d.textbbox((0, 0), tt, font=f)
        x = (STYLE["W"] - b[2]) // 2; y = int(STYLE["TOP"] + STYLE["BAND_H"] * STYLE["CAP_Y"]) - (STYLE["KEY_LIFT"] if colour else 0)
        if colour == "ice": d.text((x + 3, y + 4), tt, font=f, fill=(0, 0, 0, 170)); im.alpha_composite(ice(tt, f), (x, y))
        else: d.text((x, y), tt, font=f, fill="white", stroke_width=STYLE["CAP_STROKE"], stroke_fill=(0, 0, 0, 230))
        p = f"ov/c{k}.png"; im.save(p); out.append((p, s, min(nxt, e + STYLE["CAP_HOLD"])))
    print("Captions:", " | ".join(g[0] for g in grp))
    return out

def end_card(cfg):
    e = cfg["end_card"]; im = Image.new("RGB", (STYLE["W"], STYLE["H"]), "black"); lg = Image.open(e["logo"]).convert("RGBA")
    lw = STYLE["END_LOGO_W"]; lg = lg.resize((lw, int(lw * lg.height / lg.width))); im.paste(lg, ((STYLE["W"] - lw) // 2, STYLE["END_LOGO_Y"]), lg)
    d = ImageDraw.Draw(im); f = font(cfg, "regular_bold", STYLE["HOOK_SMALL"]); b = d.textbbox((0, 0), e["text"], font=f)
    d.text(((STYLE["W"] - b[2]) // 2, STYLE["END_LOGO_Y"] + lg.height + 60), e["text"], font=f, fill=STYLE["ICE_BOT"])
    im.save("ov/end.png")

def render(cfg):
    os.makedirs("ov", exist_ok=True); end = duration("band.mp4")
    ov = hook_pngs(cfg) + caption_pngs(cfg, end); end_card(cfg)
    ins, fc, last = ["-i", "band.mp4"], "", "0:v"
    for j, c in enumerate(cfg.get("cutaways", [])):   # b-roll shown over the band, voice keeps playing
        ins += ["-i", c["src"]]; n = len(ins) // 2 - 1
        fc += (f"[{n}:v]trim={c['from']}:{c['from'] + c['len']},setpts=PTS-STARTPTS+{c['at']}/TB,{fit_band(1.0, c.get('y', 0.5))},"
               f"eq=brightness={STYLE['CUTAWAY_DARKEN']}[b{j}];[{last}][b{j}]overlay=0:0:eof_action=pass:enable='between(t,{c['at']},{c['at'] + c['len']})'[x{j}];")
        last = f"x{j}"
    fc += f"[{last}]pad={STYLE['W']}:{STYLE['H']}:0:{STYLE['TOP']}:black[p0]"; last = "p0"
    for k, (p, s, e) in enumerate(ov):
        ins += ["-i", p]; n = len(ins) // 2 - 1
        fc += f";[{last}][{n}:v]overlay=0:0:enable='between(t,{s:.2f},{e:.2f})'[o{k}]"; last = f"o{k}"
    ins += ["-loop", "1", "-t", str(STYLE["END_SECONDS"]), "-i", "ov/end.png", "-f", "lavfi", "-t", str(STYLE["END_SECONDS"]), "-i", "anullsrc=r=48000:cl=stereo"]
    n_end = len([a for a in ins if a == "-i"]) - 2
    fc += (f";[{last}]setsar=1[m];[{n_end}:v]format=yuv420p,fps={STYLE['FPS']},fade=in:0:8,setsar=1[e]"
           f";[0:a]afade=t=out:st={end - STYLE['FADE_OUT']:.2f}:d={STYLE['FADE_OUT']}[ma]"
           f";[m][ma][e][{n_end + 1}:a]concat=n=2:v=1:a=1[v][a0];[a0]loudnorm=I={STYLE['LUFS']}:TP={STYLE['PEAK'] - 0.3}[a]")
    ffmpeg(*ins, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", cfg["out"])
    ffmpeg("-i", cfg["out"], "-vf", "fps=2,scale=200:-1,tile=9x6", "-frames:v", "1", "sheet.jpg")
    print(f"{cfg['out']} written, {duration(cfg['out']):.2f} s. Contact sheet: sheet.jpg")

if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("cut", "words", "render"): sys.exit(__doc__ or "usage: python reel.py cut|words|render reel.json")
    {"cut": cut, "words": words, "render": render}[sys.argv[1]](json.load(open(sys.argv[2])))
