param(
    [Parameter(Mandatory = $true)][string]$ToolchainDirectory,
    [string]$WslDistro = 'Ubuntu-24.04',
    [string]$SevenZip = 'C:\Program Files\7-Zip\7z.exe'
)
# Downloads/extracts tools into the requested workspace directory only.
# Does not run the LLVM installer, install packages globally, or install WSL.
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SevenZip -PathType Leaf)) { throw '7-Zip is required for archive extraction.' }
$taskDestination = [IO.Path]::GetFullPath($ToolchainDirectory)
New-Item -ItemType Directory -Path $taskDestination -Force | Out-Null
$taskPackages = @(
    @{
        Name = 'LLVM-20.1.8-win64.exe'
        Url = 'https://github.com/llvm/llvm-project/releases/download/llvmorg-20.1.8/LLVM-20.1.8-win64.exe'
        Sha256 = '3197846a2b19063687dd56e93e34cd941e3548d907f23a6131571321bdf9fe7b'
    },
    @{
        Name = 'ld64_osx-64-609-h14dcee2_16.conda'
        Url = 'https://conda.anaconda.org/conda-forge/linux-64/ld64_osx-64-609-h14dcee2_16.conda'
        Sha256 = '6a1ed3ee5cf105f2659dc0c30568f6bba982374f897924d2b970e6c1f13a9008'
    },
    @{
        Name = 'tapi-1100.0.11-h1bb5118_0.tar.bz2'
        Url = 'https://conda.anaconda.org/conda-forge/linux-64/tapi-1100.0.11-h1bb5118_0.tar.bz2'
        Sha256 = '21de9687d4760e61032efae57584835fbac424203c8df552c4c019a30a11f5c8'
    }
)
foreach ($taskPackage in $taskPackages) {
    $taskArchive = Join-Path $taskDestination $taskPackage.Name
    if (-not (Test-Path -LiteralPath $taskArchive -PathType Leaf)) {
        & curl.exe -L --fail --retry 2 -o $taskArchive $taskPackage.Url
        if ($LASTEXITCODE -ne 0) { throw "Download failed: $($taskPackage.Name)" }
    }
    if ((Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPackage.Sha256) {
        throw "SHA256 mismatch: $($taskPackage.Name)"
    }
}
$taskLlvm = Join-Path $taskDestination 'llvm-20.1.8'
& $SevenZip x (Join-Path $taskDestination 'LLVM-20.1.8-win64.exe') "-o$taskLlvm" '-y' 'bin/clang.exe' 'bin/clang++.exe' 'bin/ld64.lld.exe' 'bin/llvm-nm.exe' 'bin/llvm-readobj.exe' 'bin/llvm-objdump.exe' 'lib/clang/*/include/*'
if ($LASTEXITCODE -ne 0) { throw 'LLVM extraction failed.' }
$taskPackageDir = Join-Path $taskDestination 'ld64-package'
& $SevenZip e (Join-Path $taskDestination 'ld64_osx-64-609-h14dcee2_16.conda') "-o$taskPackageDir" '-y' 'pkg-*'
if ($LASTEXITCODE -ne 0) { throw 'ld64 package extraction failed.' }
& $SevenZip e (Join-Path $taskPackageDir 'pkg-ld64_osx-64-609-h14dcee2_16.tar.zst') "-o$taskPackageDir" '-y'
if ($LASTEXITCODE -ne 0) { throw 'ld64 tar decompression failed.' }
function ConvertTo-MellowWslPath([string]$TaskPath) {
    $taskFull = [IO.Path]::GetFullPath($TaskPath)
    if ($taskFull -notmatch '^([A-Za-z]):[\\/](.*)$') { throw 'WSL tools require a Windows drive path.' }
    return '/mnt/' + $Matches[1].ToLowerInvariant() + '/' + $Matches[2].Replace('\', '/')
}
$taskPrefix = Join-Path $taskDestination 'ld64-prefix'
$taskLinuxPrefix = ConvertTo-MellowWslPath $taskPrefix
& wsl.exe -d $WslDistro -- mkdir -p $taskLinuxPrefix
if ($LASTEXITCODE -ne 0) { throw 'Existing WSL distribution is required.' }
& wsl.exe -d $WslDistro -- tar -xf (ConvertTo-MellowWslPath (Join-Path $taskPackageDir 'pkg-ld64_osx-64-609-h14dcee2_16.tar')) -C $taskLinuxPrefix
if ($LASTEXITCODE -ne 0) { throw 'ld64 tar extraction failed.' }
& wsl.exe -d $WslDistro -- tar -xf (ConvertTo-MellowWslPath (Join-Path $taskDestination 'tapi-1100.0.11-h1bb5118_0.tar.bz2')) -C $taskLinuxPrefix
if ($LASTEXITCODE -ne 0) { throw 'tapi extraction failed.' }
& wsl.exe -d $WslDistro -- "$taskLinuxPrefix/bin/x86_64-apple-darwin13.4.0-ld" -v
if ($LASTEXITCODE -ne 0) { throw 'Extracted Darwin linker did not run.' }
$taskPackages | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskDestination 'toolchain-packages.json') -Encoding utf8
Write-Output "LLVM bin: $taskLlvm\bin"
Write-Output "Darwin linker: $taskPrefix\bin\x86_64-apple-darwin13.4.0-ld"
