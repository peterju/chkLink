# AGENTS.md

## Project overview

- This is a Windows website link-checking project with two entry points:
- GUI: [chklink.py](/D:/pyTest/chkLink/chklink.py)
- CLI: [chklink_cli.py](/D:/pyTest/chkLink/chklink_cli.py)
- The main product is the GUI. The CLI is intentionally low-profile and is mainly for automation, scheduling, and debugging.
- The scan core is shared by both entry points and lives in [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py).
- Runtime constants, versioning, config defaults, update URLs, and migration helpers live in [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py).

## Build and release commands

- Stage 1 build: `make.cmd`
- Purpose: compile GUI and CLI, update `data\LocalVersion.yaml`, and write `installer\<version>\RemoteVersion.yaml`
- GUI output: `out\chklink.dist\chklink.exe`
- CLI output: `out\chklink_cli.exe`

- Stage 2 setup packaging: `make_setup.cmd`
- Purpose: build `installer\<version>\chklink_setup.exe` through [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1) and [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)

- Stage 3 signing: `make_sign.cmd`
- Purpose: sign three files through [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)
- Signed files:
- `out\chklink.dist\chklink.exe`
- `out\chklink_cli.exe`
- `installer\<version>\chklink_setup.exe`

## Dev environment tips

- This repo is Windows-first.
- Python files are UTF-8 without BOM.
- Markdown files are UTF-8 without BOM.
- PowerShell and YAML files are UTF-8 without BOM.
- `.cmd` files must remain Big5 / cp950.
- All text files should use CRLF line endings.
- Be careful with PowerShell text pipelines when editing Traditional Chinese text. They can corrupt file contents.

## Code structure

- GUI workflow and UI state: [chklink.py](/D:/pyTest/chkLink/chklink.py)
- CLI workflow: [chklink_cli.py](/D:/pyTest/chkLink/chklink_cli.py)
- Shared scan core and Excel report writer: [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py)
- Config defaults and parsing: [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- Installer generation: [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1)
- Inno Setup template: [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- Signing flow: [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)

## Important project decisions

- GUI uses Nuitka `--standalone` because it is more stable for Tk and related runtime assets.
- CLI uses Nuitka `--onefile` because it is more convenient for automation and low-exposure distribution.
- The installer includes both GUI and CLI, but only GUI gets shortcuts.
- Installer output is versioned under `installer\<version>\`.
- The installer must not include `data\config.yaml` or `data\visited_link.yaml`, to avoid overwriting user settings and cache on upgrade.
- Auto-update is installer-based, not single-exe replacement based.

## Versioning rules

- Version source of truth: `DEFAULT_APP_VERSION` in [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- Use three-part versions such as `1.4.0`
- Build scripts and installer output paths depend on this version string

## Scan behavior summary

- Internal links are validated and recursively scanned.
- External links are listed but not recursively validated.
- HTTP links can be reported as insecure depending on config.
- URL normalization, download detection, soft-404 detection, redirect classification, retry/backoff, and per-domain throttling are implemented in the shared core.
- Excel reports include an `錯誤類型` column.

## Config and migration notes

- Runtime config file: `data\config.yaml`
- Default config template: [config.yaml-default](/D:/pyTest/chkLink/config.yaml-default)
- Missing config keys are filled by `normalize_setting()` in [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- Existing users should receive new config keys on next app launch

## Testing instructions

- Python syntax check:
```powershell
python -m py_compile chklink.py chklink_cli.py chklink_config.py chklink_core.py
```

- If you change build or installer flow, re-check:
- [make.cmd](/D:/pyTest/chkLink/make.cmd)
- [make_setup.cmd](/D:/pyTest/chkLink/make_setup.cmd)
- [make_sign.cmd](/D:/pyTest/chkLink/make_sign.cmd)
- [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1)
- [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)

## Editing guidance for agents

- Prefer small, reversible changes.
- Respect existing scan logic unless the user explicitly asks for behavior changes.
- Do not silently change file encodings.
- Do not rewrite `.cmd` files as UTF-8.
- If you edit release flow, keep README and AGENTS.md in sync.
- If you rename a user-facing script, preserve a compatibility wrapper unless the user explicitly asks to remove it.

## Common tasks

- Change scan logic: start with [chklink_core.py](/D:/pyTest/chkLink/chklink_core.py)
- Change config defaults or version: start with [chklink_config.py](/D:/pyTest/chkLink/chklink_config.py)
- Change GUI scan flow or log behavior: start with [chklink.py](/D:/pyTest/chkLink/chklink.py)
- Change CLI flow: start with [chklink_cli.py](/D:/pyTest/chkLink/chklink_cli.py)
- Change installer output or packaging: start with [build_installer.ps1](/D:/pyTest/chkLink/build_installer.ps1) and [installer_template.iss](/D:/pyTest/chkLink/installer_template.iss)
- Change signing flow: start with [make_sign.cmd](/D:/pyTest/chkLink/make_sign.cmd) and [pycert.ps1](/D:/pyTest/chkLink/pycert.ps1)
