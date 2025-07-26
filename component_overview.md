# Component Overview

This document summarises the build process for the standalone **Bankcleanr** executable.
It expands on the packaging steps described in `REFACTOR_PLAN.md` where PyInstaller
builds, macOS notarisation and Windows signing are required.

## Building with PyInstaller

All platforms share the same build script:

```bash
poetry run bash scripts/build_exe.sh
```

The script accepts two optional environment variables:

- `TARGETS` – space separated list of platforms (`linux macos windows` by default).
- `OUTDIR` – output directory for the compiled binaries (`dist` by default).

Each target directory will contain a single file binary named `bankcleanr` or
`bankcleanr.exe`.

## macOS Notarisation

To distribute on macOS the binary must be signed and notarised. After running the
build script for the `macos` target:

1. Sign the file using your *Developer ID Application* certificate:
   ```bash
   codesign --sign "Developer ID Application: <Team Name>" --options runtime dist/macos/bankcleanr
   ```
2. Compress and submit it to Apple for notarisation:
   ```bash
   zip bankcleanr.zip dist/macos/bankcleanr
   xcrun notarytool submit bankcleanr.zip --apple-id <apple id> --team-id <team id> --password <app-specific pwd> --wait
   ```
3. Staple the notarisation ticket to the binary:
   ```bash
   xcrun stapler staple dist/macos/bankcleanr
   ```

The signed and notarised binary can now be distributed to end users.

## Windows Code Signing

Windows builds should be signed with an EV certificate after running the script for
the `windows` target:

```bash
signtool sign /tr http://timestamp.digicert.com /td sha256 \
  /fd sha256 /a /f path\to\certificate.pfx /p <password> dist/windows/bankcleanr.exe
```

Verify the signature with:

```bash
signtool verify /pa dist/windows/bankcleanr.exe
```

## Verifying the Executable

Regardless of platform you can test the binary using the provided sample PDF.
After building, run:

```bash
./dist/<platform>/bankcleanr parse "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" --jsonl tx.jsonl
```

A `tx.jsonl` file should be created containing transactions. This mirrors the
behaviour driven test in `features/build.feature`.

## Relation to Refactor Plan

Section 2-D of `REFACTOR_PLAN.md` specifies that PyInstaller is used to package
the extractor for Windows and macOS, while section 9 mentions signed builds:

> **Packaging for non-tech users**<br>PyInstaller “one-file” builds for Win/macOS (see `component_overview.md`).
> **Signed builds** – follow `component_overview.md` for macOS notarisation & Windows EV cert.

This document fulfils those references by detailing the required steps.
