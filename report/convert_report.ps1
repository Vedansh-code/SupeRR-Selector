# Print report/Methodology_Report.html to report/Methodology_Report.pdf with Microsoft Edge (headless).
# Usage (from the project root):  powershell -ExecutionPolicy Bypass -File report\convert_report.ps1
# (Automating Word to save the file hung on a hidden dialog on this machine, so the PDF is printed by
#  Edge instead. For an editable copy, open the .html in Word and use Save As > Word Document.)
$ErrorActionPreference = "Stop"
$dir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$html = Join-Path $dir "Methodology_Report.html"
$pdf  = Join-Path $dir "Methodology_Report.pdf"
$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
          "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw "Microsoft Edge not found" }
$url = "file:///" + ($html -replace '\\', '/')
& $edge --headless=new --disable-gpu --no-pdf-header-footer "--print-to-pdf=$pdf" $url
"Wrote $pdf"
