# TSRG archive: targeted read-only audit. Windows PowerShell 5.1+.
# Reads only the 9 known ZIP archives and creates a report on Desktop.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$base = 'G:\'
$targets = @(
  @{ Stage='R18冻结'; Name='tourism-puffin-r18-m2-par-freeze-v1zip.zip'; Must=@('R18') },
  @{ Stage='训练数据'; Name='Tourism Puffin Geometry Training.zip'; Must=@('trainable_manifest_final.csv') },
  @{ Stage='M0预测'; Name='tourism-puffin-m0-train742-merged-v1.zip'; Must=@() },
  @{ Stage='RADIO缓存'; Name='tourism-puffin-m1-v3-radio-cache-742.zip'; Must=@() },
  @{ Stage='R14审计'; Name='tourism-puffin-m1-v4-r14-oof-reveal.zip'; Must=@() },
  @{ Stage='R16路由'; Name='tourism-puffin-m1-v4-r16-category-routing.zip'; Must=@() },
  @{ Stage='R17分支'; Name='tourism-puffin-r17-adapter-branch-closure-v1.zip'; Must=@() },
  @{ Stage='R19模型'; Name='tourism-puffin-r19-m2par-full-pitch-specialist-v1.zip'; Must=@('R19_final_model_lock.json','epoch_3/qwen_lora/adapter_model.safetensors') },
  @{ Stage='R20 V3结果'; Name='tourism-puffin-r20-one-time-batch1-r11-v3.zip'; Must=@('R20_V3_protocol.json','R20_V3_final_verdict.json','R20_V3_final_predictions_reference.csv','R20_V3_sha256_manifest.json') }
)
$expectedZipHash = @{
  'R19模型'='674F53DA5FDF65901F81CDAEA80D2D18B4C3DB16462E7C21FA1386C17DB6D3B6'
  'R20 V3结果'='0B7C2F35C9BDC2B21DADB0228D43EA3F7107D95A46C3BF1367A7DD092B1FAF3E'
}
$expectedAdapter = '1DC8AFA37C4947D30F58E9AE3AA260C76730DD7201A042F98FCBFD97AE0DA8B0'
$desk = [Environment]::GetFolderPath('Desktop')
$dest = Join-Path $desk ('TSRG_G盘定点核验_'+(Get-Date -Format yyyyMMdd_HHmmss))
New-Item -Path $dest -ItemType Directory -Force | Out-Null
$summary = New-Object 'System.Collections.Generic.List[object]'
$inventory = New-Object 'System.Collections.Generic.List[object]'
$deep = New-Object 'System.Collections.Generic.List[object]'
function Zip-Entry-SHA256($entry) {
  $stream=$entry.Open(); $hash=[System.Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','').ToUpperInvariant() }
  finally { $stream.Dispose(); $hash.Dispose() }
}
foreach($t in $targets) {
  $p=Join-Path $base $t.Name
  Write-Host ('Checking: '+$t.Stage+' ...') -ForegroundColor Cyan
  if(-not (Test-Path -LiteralPath $p -PathType Leaf)) {
    $summary.Add([pscustomobject]@{项目=$t.Stage;ZIP=$p;状态='缺少该精确文件名';文件数=0;大小GB='';ZIP_SHA256='';与先前ZIP完全一致='未检查';必要条目='未检查';说明='检查是否改过名称或移动了位置'})
    continue
  }
  $archive=$null
  try {
    $file=Get-Item -LiteralPath $p
    $zipHash=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToUpperInvariant()
    $compare='无此前ZIP哈希参考'
    if($expectedZipHash.ContainsKey($t.Stage)) {if($zipHash -eq $expectedZipHash[$t.Stage]){$compare='是'}else{$compare='否（可能只是重新压缩，需比较内部文件）'}}
    $archive=[System.IO.Compression.ZipFile]::OpenRead($p)
    $all=@($archive.Entries | Where-Object { -not [string]::IsNullOrEmpty($_.Name) })
    foreach($e in $all) {$inventory.Add([pscustomobject]@{阶段=$t.Stage;ZIP=$t.Name;内部路径=$e.FullName;字节=$e.Length})}
    $names=@($all | ForEach-Object {$_.FullName})
    $miss=@($t.Must | Where-Object { $req=$_; -not @($names | Where-Object {$_ -like ('*'+$req)}).Count })
    $required=if($miss.Count -eq 0){'路径检查通过'}else{'缺少 '+($miss -join '; ')}
    if($t.Stage -eq 'R19模型') {
      $adapter=@($all | Where-Object {$_.FullName -like '*epoch_3/qwen_lora/adapter_model.safetensors'})
      if($adapter.Count -eq 1) {
        $sha=Zip-Entry-SHA256 $adapter[0]
        $deep.Add([pscustomobject]@{阶段='R19模型';文件=$adapter[0].FullName;计算SHA256=$sha;预期SHA256=$expectedAdapter;结果=$(if($sha -eq $expectedAdapter){'PASS'}else{'MISMATCH'})})
      }
    }
    if($t.Stage -eq 'R20 V3结果') {
      $manifestEntry=@($all | Where-Object {$_.FullName -eq 'R20_V3_sha256_manifest.json'})
      if($manifestEntry.Count -eq 1) {
        $reader=New-Object System.IO.StreamReader($manifestEntry[0].Open(),[System.Text.Encoding]::UTF8)
        try {$m=($reader.ReadToEnd() | ConvertFrom-Json)} finally {$reader.Dispose()}
        foreach($prop in $m.PSObject.Properties) {
          $entry=@($all | Where-Object {$_.FullName -eq $prop.Name})
          $actual=if($entry.Count -eq 1){Zip-Entry-SHA256 $entry[0]}else{'MISSING'}
          $expected=([string]$prop.Value).ToUpperInvariant()
          $deep.Add([pscustomobject]@{阶段='R20 V3结果';文件=$prop.Name;计算SHA256=$actual;预期SHA256=$expected;结果=$(if($actual -eq $expected){'PASS'}else{'MISMATCH'})})
        }
      }
    }
    $summary.Add([pscustomobject]@{项目=$t.Stage;ZIP=$p;状态='可读取';文件数=$all.Count;大小GB=[math]::Round($file.Length/1GB,3);ZIP_SHA256=$zipHash;与先前ZIP完全一致=$compare;必要条目=$required;说明='ZIP目录可读，不代表所有数据字节均已核验'})
  } catch {
    $summary.Add([pscustomobject]@{项目=$t.Stage;ZIP=$p;状态='读取失败';文件数=0;大小GB='';ZIP_SHA256='';与先前ZIP完全一致='未检查';必要条目='未检查';说明=$_.Exception.Message})
  } finally {if($null -ne $archive){$archive.Dispose()}}
}
$summary | Export-Csv (Join-Path $dest '01_九项归档核验.csv') -NoTypeInformation -Encoding UTF8
$inventory | Export-Csv (Join-Path $dest '02_ZIP全部内部文件目录.csv') -NoTypeInformation -Encoding UTF8
$deep | Export-Csv (Join-Path $dest '03_R19_R20关键SHA256核验.csv') -NoTypeInformation -Encoding UTF8
$summary | Format-Table 项目,状态,文件数,与先前ZIP完全一致,必要条目 -AutoSize
Write-Host ('Report: '+$dest) -ForegroundColor Green
Invoke-Item $dest
