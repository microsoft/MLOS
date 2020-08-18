# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Install Visual Studio:
# See Also:
# https://docs.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2019
# https://docs.microsoft.com/en-us/visualstudio/install/workload-component-id-vs-enterprise?view=vs-2019#net-desktop-development

param(
	[Parameter(Mandatory = $false)]
	[ValidateSet('Community', 'Enterprise')]
	[string] $Sku = 'Community',

	[Parameter(Mandatory = $false)]
	[bool] $DoVsUpdates = $true
)

$exe = $null
if ($Sku -eq 'Community') {
	$exe = 'vs_community.exe'
}
elseif ($Sku -eq 'Enterprise') {
	$exe = 'vs_enterprise.exe'
}
else {
	throw 'Unhandled Sku: "{0}"' -f $Sku
}


$exePath = '{0}\{1}' -f $env:TEMP, $exe
if (!(Test-Path $exePath)) {
	$exeUrl = 'https://aka.ms/vs/16/release/{0}' -f $exe
	Invoke-WebRequest $exeUrl -OutFile $exePath
}

function WaitInstallerProcess {
	$proc = [IO.Path]::GetFileNameWithoutExtension($exe)
	do {
		Write-Host "Waiting for installer process $proc to end ..."
		Start-Sleep -Seconds 2
	} while ((Get-Process -ErrorAction SilentlyContinue $proc).Length -gt 0)
}

if ($DoVsUpdates)
{
	# First update the installer tool itself.
	# See Also: https://docs.microsoft.com/en-us/visualstudio/install/command-line-parameter-examples?view=vs-2019#using---installpath
	&$exePath --update --quiet --wait
	WaitInstallerProcess

	# Also be sure if we've already installed VS 2019 that it's up to date.
	$installPath = 'C:\Program Files (x86)\Microsoft Visual Studio\2019\{0}\Common7\IDE\devenv.exe' -f $Sku
	if (Test-Path $installPath) {
		&$exePath update --wait --norestart --passive
		WaitInstallerProcess
	}
}

# Now make sure we have the right set of VS2019 components installed.
&$exePath `
	--wait `
	--norestart `
	--passive `
	--add Microsoft.VisualStudio.Workload.ManagedDesktop `
	--add Microsoft.NetCore.Component.DevelopmentTools `
	--add Microsoft.NetCore.Component.Runtime.3.1 `
	--add Microsoft.NetCore.Component.SDK `
	--add Microsoft.VisualStudio.Workload.NativeDesktop `
	--add Microsoft.Net.ComponentGroup.TargetingPacks.Common `
	--add Microsoft.VisualStudio.Component.NuGet `
	--add Microsoft.VisualStudio.Component.VC.CMake.Project `
	--add Microsoft.VisualStudio.Component.DiagnosticTools `
	--add Microsoft.VisualStudio.Component.VC.DiagnosticTools `
	--add Microsoft.VisualStudio.Component.IntelliTrace.FrontEnd `
	--add Microsoft.VisualStudio.Component.Debugger.JustInTime `
	--add Microsoft.VisualStudio.Component.VC.TestAdapterForBoostTest `
	--add Microsoft.VisualStudio.Component.VC.TestAdapterForGoogleTest `
	--add Microsoft.VisualStudio.Component.LiveUnitTesting `
	--add Microsoft.VisualStudio.Component.VC.ATL `

WaitInstallerProcess
Write-Host "Done"
