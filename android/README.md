# Tafheem Android app (Google Play)

The website wrapped as an Android app (a Trusted Web Activity: Chrome shows tafheem-app.vercel.app full screen, no browser bar). Updating the website updates the app; rebuild only to change the app's name, icon, colours or version.

App ID: `tafheem.app` (permanent). Settings: `twa-manifest.json`. Tools live in `C:\Users\Shaf\.bubblewrap` (Java 17, Android SDK; `bubblewrap` from npm).

## Build (PowerShell, from the no-space junction `C:\Users\Shaf\.bubblewrap\tafheem-android`, which points here; gradle breaks on the space in "aRABIC GRAMMAR TOOL")
1. Raise `appVersionCode` (and `appVersionName`) in `twa-manifest.json`, then `bubblewrap update --skipVersionUpgrade`.
2. Load `signing.env` into env, set `JAVA_HOME` and `ANDROID_HOME`, run `.\gradlew.bat assembleRelease bundleRelease`.
3. Sign: `zipalign` + `apksigner` for the test `.apk`, `jarsigner` for `app-release-bundle.aab` (the file Play takes). `bubblewrap build` does this too, but its own gradle call fails on this machine.

## Secrets (gitignored, back them up)
`upload.keystore` + `signing.env` (its password). It is the upload key only: Play App Signing holds the real key, so a lost upload key can be reset in Play Console.
Upload key SHA-256: `BB:EF:DB:78:34:7B:93:9E:68:F4:2D:03:B8:CD:58:FD:A9:E2:AB:B9:F8:52:E1:24:5E:D3:1C:AC:19:93:79:2C`

## Site link
`frontend/public/.well-known/assetlinks.json` must list the upload key and Play's app-signing key (Play Console, Test and release, App integrity), or the app shows a browser bar.

## Publish to Play (no browser)
`python store/publish.py` checks the listing, images and bundle against Play and throws the draft away; add `--commit` to save it. Settings `store/play.json`, text `store/listing.md`. Login: robot account `play-uploader@tafheem-play-57707.iam.gserviceaccount.com` (Google Cloud project `tafheem-play-57707`), key in gitignored `play-key.json`; in Play Console it can release and edit the listing for this app only.
Update flow: raise the version, rebuild (above), `publish.py --commit`, then roll out the draft release in Play Console.
Play app-signing SHA-256: `D8:08:7C:E8:A2:CE:5F:0C:AE:F5:EB:02:B4:1B:08:5D:DB:52:32:12:2F:B3:21:C3:7C:04:AA:ED:8A:DF:38:18`
