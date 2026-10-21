# Code signing policy

Clawd is applying to the SignPath Foundation for free code signing of Windows release binaries.

After approval, Windows release artifacts will be built by GitHub Actions from this repository and signed through SignPath.io. The certificate will be issued to SignPath Foundation.

Planned statement:

> Free code signing provided by SignPath.io, certificate by SignPath Foundation

## What will be signed

- Windows x64 release executables (`.exe`) published on the GitHub Releases page.

## Build and signing process

- Builds run in GitHub Actions from the public source in this repository.
- Only CI-built release artifacts are submitted for signing.
- The private signing key is managed by SignPath in its HSM and is never stored in this repository.

## Team roles

- Maintainer, committer, and approver: [@bmarcnhii1-max](https://github.com/bmarcnhii1-max)

## Privacy

See [PRIVACY.md](PRIVACY.md).

## Status

Application pending. The current v1.0.0 executable is not yet signed.
