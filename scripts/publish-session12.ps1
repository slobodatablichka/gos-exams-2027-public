#requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Private = "https://github.com/slobodatablichka/gos-exams-2027.git"
$Public = "https://github.com/slobodatablichka/gos-exams-2027-public.git"
$Work = Join-Path $env:TEMP ("gos-exams-2027-publish-12-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Work | Out-Null

function Git-Checked {
    & git @args
    if ($LASTEXITCODE -ne 0) { throw "Git failed: git $($args -join ' ')" }
}
function Python-Checked {
    param([string[]]$Arguments)
    $cmdArgs = @($script:PythonArgs) + @($Arguments)
    & $script:PythonExe @cmdArgs
    if ($LASTEXITCODE -ne 0) { throw "Python failed: $($Arguments -join ' ')" }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is required." }
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonExe = "py"; $PythonArgs = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = "python"; $PythonArgs = @()
} else {
    throw "Python 3 is required. Install Python 3 and rerun."
}

Git-Checked clone --quiet $Private (Join-Path $Work "private")
Git-Checked clone --quiet $Public (Join-Path $Work "public")
$privateRoot = Join-Path $Work "private"
$publicRoot = Join-Path $Work "public"
$progress = Import-Csv -Encoding UTF8 (Join-Path $privateRoot "planning\lesson-progress.csv") |
    Where-Object { $_.meeting -eq "12" }
if ($progress.Count -ne 6) { throw "Expected 6 topics in the private quality ledger." }
foreach ($item in $progress) {
    foreach ($field in @("sources","l3","l2","l1")) {
        if ($item.$field -ne "done") { throw "Quality gate not complete for question $($item.question): $field" }
    }
    if ($item.quality -ne "approved") { throw "Question $($item.question) is not approved." }
}

Set-Location -LiteralPath $publicRoot
$branch = "publish/session-12-" + (Get-Date -Format "yyyyMMdd-HHmmss")
Git-Checked switch -c $branch

$generator = Join-Path $publicRoot "scripts\publish-lesson.py"
$patchPath = Join-Path $Work "patch-session12.py"
@'
from pathlib import Path
import re
import sys

p = Path(sys.argv[1])
code = p.read_text(encoding="utf-8")
match = re.search(r"(?m)^Q_RE = re\.compile\(.*$", code)
if not match:
    raise SystemExit("Missing Q_RE in generator")
code = code[:match.start()] + 'Q_RE = re.compile(r"^> (.+)$", re.M)' + code[match.end():]

hook = """
_original_session12_name_and_body = name_and_body
def name_and_body(raw, level):
    title, body = _original_session12_name_and_body(raw, level)
    # Do not publish internal editorial state as exam content.
    body = re.sub(r"(?m)^\\*\\*(?:L[123][^\\n]*|Редакция по проверенному источнику[^\\n]*)\\*\\*\\s*$", "", body)
    body = re.sub(
        r"(?ms)^## (?:Источниковая оговорка|Источниковое ограничение|Ограничение источников|Вывод и граница проверки)\\n.*?(?=^## |\\Z)",
        "", body,
    )
    body = re.sub(r"(?m)^\\*\\*Источник:\\*\\*.*$", "", body)
    return title, re.sub(r"\\n{3,}", "\\n\\n", body).strip()

"""
anchor = "\ndef topic_title(raw):"
if code.count(anchor) != 1:
    raise SystemExit("Unexpected generator structure")
code = code.replace(anchor, "\n" + hook + anchor, 1)
p.write_text(code, encoding="utf-8")
print("PATCHED: source formula and private editorial notes")
'@ | Set-Content -LiteralPath $patchPath -Encoding UTF8

Python-Checked -Arguments @($patchPath, $generator)
Python-Checked -Arguments @("-m", "py_compile", $generator)
Python-Checked -Arguments @($generator, "check")
Python-Checked -Arguments @($generator, "build", "12", "--private-root", $privateRoot)
Python-Checked -Arguments @($generator, "build", "12", "--private-root", $privateRoot, "--apply")
Git-Checked diff --check
Git-Checked restore -- scripts/publish-lesson.py

$expected = @(Get-ChildItem -LiteralPath (Join-Path $publicRoot "sessions\12") -Filter "*.md")
if ($expected.Count -ne 20) { throw "Expected 20 lesson pages, got $($expected.Count)" }

Git-Checked add -- sessions/12 index.md materials/index.md schedule.md _data/published_sessions.csv
Git-Checked -c user.name="Gos Exams Publication" -c user.email="publication@users.noreply.github.com" commit -m "Publish session 12 with six approved liturgics topics"
Git-Checked push --set-upstream origin $branch
Write-Host ""
Write-Host "PUBLISH BRANCH: $branch"
Write-Host "BRANCH HEAD:"
Git-Checked rev-parse HEAD
Write-Host "PUBLIC PR: https://github.com/slobodatablichka/gos-exams-2027-public/compare/main...$branch"
Write-Host "All 20 lesson pages and navigation are committed on the publication branch. Merge and Pages deployment are still pending."
