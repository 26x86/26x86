<#
.SYNOPSIS
  Enforces the 26x86/26x86 pull-request-only branch strategy on `main`.
.DESCRIPTION
  Uses gh api to apply branch protection. Requires `gh` authenticated with a
  token that has admin permission on the repository. If the required status
  checks have not run yet on any pull request, GitHub rejects the context list;
  the script then applies reviews-only protection first and retries.
.PARAMETER Repo
  GitHub repository to protect. Default: 26x86/26x86
.PARAMETER Branch
  Branch to protect. Default: main
.PARAMETER ApplyContexts
  Required status-check contexts. Default: docs-build, isolated-asset-guard,
  workspace-tests
.EXAMPLE
  powershell -File tools/git/ensure-branch-protection.ps1
#>
param(
  [string]$Repo = "26x86/26x86",
  [string]$Branch = "main",
  [string[]]$ApplyContexts = @("docs-build", "isolated-asset-guard", "workspace-tests")
)

$ErrorActionPreference = "Stop"

function Invoke-ProtectionBody {
  param([hashtable]$Body)
  $json = $Body | ConvertTo-Json -Depth 10
  $result = $json | gh api -X PUT "repos/$Repo/branches/$Branch/protection" --input -
  if ($LASTEXITCODE -ne 0) {
    throw "gh api returned exit code $LASTEXITCODE: $result"
  }
  return $result
}

$base = [ordered]@{
  enforce_admins             = $true
  required_linear_history    = $true
  require_conversation_resolution = $true
  allow_force_pushes         = $false
  allow_deletions            = $false
  lock_branch                = $false
  allow_fork_pushes          = $false
  restrictions               = $null
  required_pull_request_reviews = @{
    required_approving_review_count = 1
    dismiss_stale_reviews    = $true
    require_code_owner_reviews = $false
  }
}

$checksBody = $base.Clone()
$checksBody["required_status_checks"] = @{
  strict   = $true
  contexts = @($ApplyContexts)
}

$reviewsOnlyBody = $base.Clone()
$reviewsOnlyBody["required_status_checks"] = $null

try {
  Write-Host "Applying branch protection on $Repo/$Branch with contexts: $($ApplyContexts -join ', ')"
  Invoke-ProtectionBody $checksBody | Out-Null
  Write-Host "OK: protection set with $($ApplyContexts.Count) required checks."
}
catch {
  Write-Host "WARN: context apply failed: $($_.Exception.Message)"
  Write-Host "Applying reviews-only protection first, then retrying contexts..."
  Invoke-ProtectionBody $reviewsOnlyBody | Out-Null
  Start-Sleep -Seconds 3
  try {
    Invoke-ProtectionBody $checksBody | Out-Null
    Write-Host "OK: protection set with $($ApplyContexts.Count) required checks."
  } catch {
    Write-Warning "Contexts still rejected: $($_.Exception.Message)"
    Write-Warning "Re-run this script once 'docs-build', 'isolated-asset-guard' and 'workspace-tests'"
    Write-Warning "have completed at least once on a pull request."
  }
}

Write-Host ""
Write-Host "Current protection summary:"
gh api "repos/$Repo/branches/$Branch/protection" --jq "{enforce_admins, required_linear_history, allow_force_pushes, allow_deletions, required_pr_reviews: .required_pull_request_reviews.required_approving_review_count, contexts: [.required_status_checks.contexts[]]}"