# Reader tab: your own books, your notes, and class follow-along

## 1. Requirements (decided 2026-11-27)
- Anyone opens a PDF (or a photo of a page). It stays on their device (browser storage), never uploaded.
- They read it page by page, highlight, and write notes beside any spot. Notes are saved on the device and export as one file.
- A teacher presses "Start class": a 6-letter code and a QR. Students join with no account.
- The teacher taps the line they are reading on their own copy. Every student screen shows that page with the line lit up.
- Students do not need the PDF: the teacher's device sends the page it is on.

Success checks (each is tested):
1. A 300-page, 50 MB scanned PDF opens and the first page shows within 2 s on a laptop; turning a page takes under 300 ms.
2. Notes survive a reload and a browser restart; export, then import on another browser, restores every note.
3. Two student devices follow a teacher's tap within 1 s on the live site; a student who joins late lands on the current page.
4. Nothing from the book reaches the server except the page the teacher is showing, and that page is never stored (only passed through).
5. The photo page reader (now in Dictionary) works the same after it moves.

## 2. Research
- PDF drawing: pdf.js (Mozilla, free, the engine inside Firefox). It renders one page at a time, so big books stay fast. Rejected: rendering on the server (uploads the book, which breaks requirement 1).
- Live link: a "room" on our own server. The teacher sends {page, spot, page picture}, the server passes it on to the students and keeps only the latest message in memory. Rejected: direct device-to-device (WebRTC), which still needs a server to connect people and fails on many school networks.
- Constraint found on checking: every /api call goes through Vercel to Oracle, and Oracle refuses anything that skips Vercel (the origin secret). Vercel's docs do not confirm that their forwarding carries a WebSocket. So the transport is decided by a spike on the live site, not assumed. In order of preference:
  1. WebSocket through the existing /api forwarding.
  2. Server-sent events (one long download the server keeps writing to; the browser reconnects by itself if it is cut) for students, and plain POST for the teacher's taps. Both are ordinary web requests.
  3. Students ask every 700 ms (a fallback that always works; about 1.5 requests a second per student, inside the rate limits only if the room has its own limit).
  The relay code sits behind one interface, so the choice is one file.
- Server limits: 1 GB machine. The rooms are in memory, the page picture is capped (~200 KB JPEG), rooms close after 3 hours idle, and the number of rooms is capped. All of these are config values.

## 3. Design
Picked: a new **Reader** tab under the existing "Read" group, owning everything about reading a book of your own. Rejected: growing the Dictionary's page reader, which mixes "look up a word" with "read a book" and is why it feels misplaced now.

Pieces (one job each):
| Piece | Where | Job |
|---|---|---|
| ReaderPanel | components/reader/ | the tab: your books (a "library", not "shelf"), open one |
| BookView | components/reader/ | page turning, zoom, tapping a line |
| NotesRail | components/reader/ | highlights and side notes for this page |
| PageReader (moved) | components/reader/ | a photo of a page, read into text; Dictionary links to it |
| book files | lib/reader/bookFiles.js | the PDF bytes in IndexedDB (too big for the existing store); nothing else |
| notes | existing lib/store/stored.js | highlights + side notes as one more saved list; a logged-in account's notes then follow it to other devices through the existing lib/store/shelf.js sync, with no new code |
| pdf source | lib/reader/pdfSource.js | the only file that knows pdf.js; a photo is a one-page source |
| class link | lib/reader/classLink.js | join/lead a room, send/receive the spot |
| room relay | backend/routers/classroom.py + services/classroom.py | WebSocket rooms in memory, size and time limits from config |

Each word lookup in a book reuses the Dictionary's word bar, like the page reader already does.

## 4. Slices (each ships alone, live-checked)
1. **Skeleton:** Reader tab, open a PDF, turn pages. Check 1. Done 2026-11-27: 300 pages, first page 0.3 s, turn 15 ms (preview build, laptop).
2. **Library:** books remembered on the device; reopen at the last page.
3. **Notes:** highlight + side note; export/import. Check 2.
4. **Move the page reader** into Reader; the Dictionary button opens it. Check 5.
5. **Class relay** (server). It starts with a spike: one test route, deployed, and each of the three transports tried through tafheem-app.vercel.app from a phone, measuring delay and whether it stays connected for 10 minutes. The winner is kept, and the rest is deleted. Then rooms, codes and limits, with tests for joining, a late joiner, a full room and an oversized picture.
6. **Lead + follow:** Start class, QR, tap a line → students follow. Check 3 and 4 on the live site with two browsers.

Pre-mortem:
- Scanned PDFs have no text layer, so "tap a line" can't find lines. Guard: the tap marks a horizontal band where you touched, not a text line. It works on any page.
- The phone's browser drops the WebSocket when the screen locks. Guard: reconnect and resend the latest spot on wake.
- Browser storage can be wiped by the browser. Guard: export is one tap and the library says plainly that books live on this device.

Checked against master (2026-11-27), so nothing is built twice: no PDF, IndexedDB, live-link or class code exists. "Shelf" already names the account's saved items (lib/store/shelf.js), so the reader does not reuse that word for books. The page reader's 2026-11-21 decision "PDFs keep the cannot-open card" is replaced: its PDF button opens the Reader.

Out of scope for now: syncing the book files themselves across devices, camera or voice following, students' own notes inside a class.
