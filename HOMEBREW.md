# Publishing Luma Messenger with Homebrew

A GUI app ships as a **cask** (a `.app` bundle), not a formula. The plan: build the
`.app` with PyInstaller, attach the zip to a GitHub release, and host the cask in a
personal tap repo. One-time setup, then each update is just a new release + one
line changed in the cask.

## 1. Build the app (on the Mac, in this folder)

```bash
cd ~/luma_messanger
bash build-app.sh 0.1.0
```

This creates `dist/Luma Messenger.app` and `Luma-Messenger-0.1.0-macOS.zip`, and
prints the zip's SHA-256 — save that value, the cask needs it.

## 2. Put the code on GitHub (first time only)

```bash
cd ~/luma_messanger
git init
git add main.py requirements.txt pyproject.toml build-app.sh HOMEBREW.md
git commit -m "Luma Messenger 0.1.0"
gh repo create Jimboo1865/luma-messenger --public --source=. --push
```

(If `gh` isn't installed: `brew install gh`, then `gh auth login` once.)

## 3. Make the release and upload the zip

```bash
gh release create v0.1.0 Luma-Messenger-0.1.0-macOS.zip --title "0.1.0" --notes "First release"
```

## 4. Create the tap repo and add the cask (first time only)

```bash
gh repo create Jimboo1865/homebrew-tap --public --clone
cd homebrew-tap
mkdir -p Casks
cp ~/luma_messanger/luma-messenger.rb Casks/luma-messenger.rb
git add Casks/luma-messenger.rb
git commit -m "Add luma-messenger 0.1.0"
git push
```

Before committing, replace `REPLACE_WITH_SHA256_OF_THE_ZIP` in the cask with the
SHA-256 printed by `build-app.sh`.

## 5. Install it

```bash
brew tap Jimboo1865/tap
brew install --cask luma-messenger
```

The app lands in /Applications as "Luma Messenger".

## 6. Updating later

1. Bump the version, rebuild: `bash build-app.sh 0.2.0`
2. `gh release create v0.2.0 Luma-Messenger-0.2.0-macOS.zip`
3. In the tap repo, update `version` and `sha256` in `Casks/luma-messenger.rb`, commit, push.
4. Users update with `brew upgrade --cask luma-messenger`.

## Notes

- First launch will ask for macOS permission to control Messages (for sending)
  and to access Contacts (for Save to Contacts). That's expected — approve both.
- The `.app` is unsigned, so macOS may warn on first open; right-click → Open
  the first time if it blocks you.
- The cask file lives in the tap repo (`homebrew-tap/Casks/luma-messenger.rb`),
  not in this app repo. A copy is kept in the workspace at
  `your_files/luma-messenger/luma-messenger.rb` for reference.
