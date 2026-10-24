// Copies a Tamreen Google Form score page to the clipboard, for build_tamreen.py save.
//
// Open the form's "view score" page, paste this whole file into the browser
// console, then run   copyForm('haal')   with a short name for the exercise.
// The page holds the whole form in FB_PUBLIC_LOAD_DATA_; the marking (which
// options are right) is only in what is drawn, so both are read.
//
// Why not post it straight to a local script: Chrome asks before a web page
// may talk to this machine, and that prompt freezes the page. The clipboard
// needs no permission.

function harvestForm() {
  const d = window.FB_PUBLIC_LOAD_DATA_;
  const dom = {};
  document.querySelectorAll('[data-item-id]').forEach((el) => { dom[el.dataset.itemId] = el; });
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const MARK = '[aria-label="Correct"],[aria-label="Incorrect"]';
  // The tick or cross beside the row a ticked cell sits in. "none" means the
  // row has no mark, which is how the form's own "Correct answers" grid looks.
  const rowMark = (e, root) => {
    for (let a = e; a && a !== root; a = a.parentElement) {
      const n = a.querySelectorAll(MARK).length;
      if (n === 1) return a.querySelector(MARK).getAttribute('aria-label');
      if (n > 1) return 'none';
    }
    return 'none';
  };
  const items = d[1][1].map((it) => {
    const el = dom[String(it[0])];
    const entries = (it[4] || []).map((e) => ({ options: (e[1] || []).map((o) => o[0]), row: e[3] ? e[3][0] : null }));
    const media = it[9] ? { caption: it[9][1] || null, size: it[9][0] ? it[9][0][2] : null } : null;
    const out = { id: it[0], title: it[1], description: it[2], type: it[3], entries, media };
    if (el) {
      const txt = el.innerText;
      const pts = (txt.match(/(\d+)\/(\d+)/) || []).slice(1).map(Number);
      const checked = [...el.querySelectorAll('[aria-checked="true"]')].map((e) => ({
        label: clean(e.getAttribute('aria-label')), mark: rowMark(e, el),
      }));
      const cb = txt.match(/Correct answers?\n([\s\S]*?)(\nFeedback\n|$)/);
      const fb = txt.match(/Feedback\n([\s\S]*?)(\nCorrect answer|$)/);
      out.dom = {
        points: pts.length === 2 ? pts : null,
        checked,
        correctBlock: cb ? cb[1].split('\n').map(clean).filter(Boolean) : null,
        feedback: fb ? clean(fb[1]) : null,
        imgs: [...el.querySelectorAll('img')].map((i) => i.src),
      };
    }
    return out;
  });
  return { title: d[3], description: d[1][0], items };
}

function copyForm(slug) {
  const form = harvestForm();
  const images = [];
  form.items.forEach((i) => {
    if (i.dom) i.dom.imgs = i.dom.imgs.map((src) => { images.push(src); return `${slug}-${String(images.length - 1).padStart(2, '0')}.png`; });
  });
  const ta = document.createElement('textarea');
  ta.value = JSON.stringify({ slug, form, images });
  document.body.appendChild(ta);
  ta.select();
  const ok = document.execCommand('copy');
  ta.remove();
  return `${ok ? 'copied' : 'copy failed'}: ${form.items.length} items, ${images.length} pictures`;
}
