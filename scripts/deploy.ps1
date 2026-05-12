# deploy.ps1 — commit generated sites + push to GitHub Pages.
#
# Usage:
#   .\scripts\deploy.ps1                         # commit + push to default branch (gh-pages)
#   .\scripts\deploy.ps1 -Branch gh-pages        # explicit branch
#
# What this does:
#   1. Detects which site directories under sites/ are new vs last commit
#   2. Stages sites/, data/prospects.csv, dashboard.md
#   3. Commits with a timestamped message
#   4. Pushes to origin <branch>
#   5. Prints live URLs for any newly added site folders

[CmdletBinding()]
param(
    [string]$Branch = "gh-pages"
)

$ErrorActionPreference = "Stop"

# Move to project root (one level up from scripts/)
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

# Detect remote
$remoteUrl = (& git config --get remote.origin.url 2>$null)
if (-not $remoteUrl) {
    Write-Error "No 'origin' remote configured. Run:`n  git remote add origin git@github.com:<user>/<repo>.git"
    exit 1
}

# Parse "git@github.com:user/repo.git" or "https://github.com/user/repo.git"
$ghUser = ""
$ghRepo = ""
if ($remoteUrl -match 'github\.com[:/]([^/]+)/([^/.]+?)(\.git)?$') {
    $ghUser = $Matches[1]
    $ghRepo = $Matches[2]
} else {
    Write-Warning "Could not parse GitHub user/repo from: $remoteUrl"
}

$pagesBase = ""
if ($ghUser -and $ghRepo) {
    if ($ghRepo -eq "$ghUser.github.io") {
        $pagesBase = "https://$ghUser.github.io"
    } else {
        $pagesBase = "https://$ghUser.github.io/$ghRepo"
    }
}

# Detect newly added site subdirectories. `git status --porcelain` collapses
# untracked directories to the parent, so we ask for --untracked-files=all to
# recurse into them. We then keep only entries whose second path segment is
# non-empty (skips the bare `sites/` parent).
$newSites = @()
$statusLines = & git status --porcelain --untracked-files=all sites/ 2>$null
foreach ($line in $statusLines) {
    if (-not $line) { continue }
    $code = $line.Substring(0, 2)
    $path = $line.Substring(3)
    if ($code -match '^\?\?' -or $code -match '^A ') {
        $parts = $path -split '/'
        if ($parts.Length -ge 2 -and $parts[0] -eq 'sites' -and $parts[1]) {
            $newSites += $parts[1]
        }
    }
}
$newSites = $newSites | Sort-Object -Unique

# Stage. We include templates/ and scripts/ so iterative design + scraper work
# doesn't sit untracked across deploys (this hit us once already).
& git add sites/ data/prospects.csv dashboard.md templates/ scripts/ docs/ 2>$null | Out-Null

# Bail out if nothing staged
$cached = & git diff --cached --name-only
if (-not $cached) {
    Write-Output "Nothing to deploy — no staged changes."
    exit 0
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
& git commit -m "Deploy site batch — $stamp" | Out-Null

$currentBranch = (& git rev-parse --abbrev-ref HEAD).Trim()
if ($currentBranch -ne $Branch) {
    Write-Output "Pushing $currentBranch -> origin/$Branch"
    & git push origin "HEAD:$Branch"
} else {
    & git push origin $Branch
}

Write-Output ""
Write-Output "Deployed. Newly published previews:"
if ($newSites.Count -eq 0) {
    Write-Output "  (no new site directories detected - content updates only)"
} else {
    foreach ($slug in $newSites) {
        if ($pagesBase) {
            Write-Output "  $pagesBase/sites/$slug/"
        } else {
            Write-Output "  sites/$slug/"
        }
    }
}
