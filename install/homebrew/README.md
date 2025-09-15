# Homebrew Formula (template)

This folder provides a template Homebrew formula for ReqStudio. To publish, create a Tap and update the formula URL and SHA256.

Steps (high-level):

1) Fork or create a tap, e.g., `github.com/your-org/homebrew-reqstudio`.
2) Place `reqstudio.rb` in the tap’s `Formula/` directory.
3) Edit `url` to a released tarball (GitHub release) and set `sha256` accordingly.
4) `brew tap your-org/reqstudio` and `brew install reqstudio`.

Notes:

- The formula uses a Python venv inside Homebrew’s prefix to isolate dependencies.
- PyQt6 runs on macOS via wheels; Homebrew downloads the wheels into the venv.
