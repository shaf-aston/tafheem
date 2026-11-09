"""Send the store listing, images and app bundle to Google Play through its free API.

python store/publish.py            check only: opens a draft edit, uploads, validates, throws it away
python store/publish.py --commit   same, then saves it in Play Console (release stays a draft until rolled out there)

Settings: store/play.json. Listing text: store/listing.md. Login: the service-account key at key_file (gitignored).
"""
import json, re, sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

HERE = Path(__file__).parent
CFG = json.loads((HERE / "play.json").read_text())


def listing_text():
    md = (HERE / "listing.md").read_text(encoding="utf-8")
    pick = lambda label: re.search(rf"\*\*{label}\*\*[^:]*:\s*(.+)", md).group(1).strip()
    full = md.split("**Full description:**", 1)[1].split("**Category:**", 1)[0].strip()
    title, short = pick("App name"), pick("Short description")
    assert len(title) <= 30 and len(short) <= 80 and len(full) <= 4000, "listing text over Play's limits"
    return {"title": title, "shortDescription": short, "fullDescription": full}


def main(commit):
    creds = service_account.Credentials.from_service_account_file(
        HERE / CFG["key_file"], scopes=["https://www.googleapis.com/auth/androidpublisher"])
    edits = build("androidpublisher", "v3", credentials=creds, cache_discovery=False).edits()
    pkg, lang = CFG["package"], CFG["language"]
    eid = edits.insert(packageName=pkg, body={}).execute()["id"]
    try:
        edits.details().update(packageName=pkg, editId=eid, body={
            "defaultLanguage": lang, "contactEmail": CFG["contact_email"]}).execute()
        edits.listings().update(packageName=pkg, editId=eid, language=lang, body=listing_text()).execute()
        images = [("icon", CFG["icon"]), ("featureGraphic", CFG["feature_graphic"])] + \
                 [("phoneScreenshots", s) for s in CFG["screenshots"]]
        for kind in {k for k, _ in images}:
            edits.images().deleteall(packageName=pkg, editId=eid, language=lang, imageType=kind).execute()
        for kind, f in images:
            edits.images().upload(packageName=pkg, editId=eid, language=lang, imageType=kind,
                                  media_body=MediaFileUpload(str(HERE / f), mimetype="image/png")).execute()
        code = edits.bundles().upload(packageName=pkg, editId=eid, media_body=MediaFileUpload(
            str(HERE / CFG["bundle"]), mimetype="application/octet-stream", resumable=True)).execute()["versionCode"]
        edits.tracks().update(packageName=pkg, editId=eid, track=CFG["track"], body={
            "track": CFG["track"], "releases": [{"versionCodes": [str(code)], "status": "draft"}]}).execute()
        edits.validate(packageName=pkg, editId=eid).execute()
        print(f"ok: listing, {len(images)} images, bundle v{code} on {CFG['track']}")
        if commit:
            edits.commit(packageName=pkg, editId=eid).execute()
            print("saved to Play Console")
    finally:
        if not commit:
            edits.delete(packageName=pkg, editId=eid).execute()


if __name__ == "__main__":
    main("--commit" in sys.argv)
