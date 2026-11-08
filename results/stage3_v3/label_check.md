# Label check: T1547.001, T1059.003, T1003.006 (v3 pool)

Read only; nothing in the pool, builder or tables was changed. Parent chains were rebuilt from the raw file by following process-creation events upward: Sysmon 1 by `ParentProcessGuid`, else Security 4688 by host and PID (latest creation at or before the event). A chain stops where the raw file has no creation event for the next process; the last entry then comes from a parent field. The first entry is the event's own process.


## T1547.001 (3 events, 3 clusters)


### `d2d8a80c7c8a667f`

- cluster: `T1547.001|empire_persistence_registry_modification_run_keys_elevated_user_2020-07-22001847.json|2020-07-22 04:19`
- Event ID 13, channel `Microsoft-Windows-Sysmon/Operational`, time `2020-07-22 04:19:04.118`
- Image: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`; User: `NT AUTHORITY\SYSTEM`
- TargetObject: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\Updater`; Details: `"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -c "$x=$((gp HKLM:SOFTWARE\Microsoft\Windows\CurrentVersion Debug).Debug);powershell -Win Hidden -enc $x"`
- parent chain (own process first):

  | level | image | command line | from |
  |---|---|---|---|
  | 0 | `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe` |  | Image field in this event |

### `2a127f68cdc4410d`

- cluster: `T1547.001|empire_persistence_registry_modification_run_keys_standard_user_2020-09-04030609.json|2020-09-04 07:06`
- Event ID 13, channel `Microsoft-Windows-Sysmon/Operational`, time `2020-09-04 07:06:21.311`
- Image: `C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe`; User: `NT AUTHORITY\SYSTEM`
- TargetObject: `HKU\S-1-5-21-3125456671-949036322-3048627137-1104\Software\Microsoft\Windows\CurrentVersion\Run\Updater`; Details: `"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -c "$x=$((gp HKCU:Software\Microsoft\Windows\CurrentVersion Debug).Debug);powershell -Win Hidden -enc $x"`
- parent chain (own process first):

  | level | image | command line | from |
  |---|---|---|---|
  | 0 | `C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe` |  | Image field in this event |

### `243e55d798340ba4`

- cluster: `T1547.001|empire_persistence_registry_modification_run_keys_standard_user_2020-09-04030609.json|2020-09-04 07:08`
- Event ID 13, channel `Microsoft-Windows-Sysmon/Operational`, time `2020-09-04 07:08:01.140`
- Image: `C:\Program Files\Windows Defender\MsMpEng.exe`; User: `NT AUTHORITY\SYSTEM`
- TargetObject: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\WindowsDefender`; Details: `"%%ProgramFiles%%\Windows Defender\MSASCuiL.exe"`
- parent chain (own process first):

  | level | image | command line | from |
  |---|---|---|---|
  | 0 | `C:\Program Files\Windows Defender\MsMpEng.exe` | `"C:\Program Files\Windows Defender\MsMpEng.exe"` | 4688 at 2020-09-04 03:08:00 |
  | 1 | `C:\Windows\System32\services.exe` |  | 4688 at 2020-09-04 03:07:55 |
  | 2 | `C:\Windows\System32\wininit.exe` |  | parent field of the creation event above |

## T1059.003 (2 events, 2 clusters)


### `30f8bc022db8378b`

- cluster: `T1059.003|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-02 03:03`
- Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`, time `2020-05-02 03:03:41.438`
- Image: `C:\Windows\System32\conhost.exe`; User: `NT AUTHORITY\SYSTEM`
- CommandLine: `\??\C:\windows\system32\conhost.exe 0xffffffff -ForceV1`
- parent chain (own process first):

  | level | image | command line | from |
  |---|---|---|---|
  | 0 | `C:\Windows\System32\conhost.exe` | `\??\C:\windows\system32\conhost.exe 0xffffffff -ForceV1` | this event |
  | 1 | `C:\Windows\System32\cmd.exe` | `"cmd"` | Sysmon 1 at 2020-05-02 03:03:41.434 |
  | 2 | `C:\WindowsAzure\Packages\CollectGuestLogs.exe` | `"CollectGuestLogs.exe" -Mode:ga -FileName:C:\WindowsAzure\CollectGuestLogsTemp\c95ce60d-c0d8-4d55-9bfc-3a9937bf113e.zip` | Sysmon 1 at 2020-05-02 03:03:32.190 |
  | 3 | `C:\WindowsAzure\Packages\WaAppAgent.exe` | `C:\WindowsAzure\Packages\WaAppAgent.exe` | parent field of the creation event above |

### `ae4b62e1857e1a39`

- cluster: `T1059.003|cmd_dumping_ntds_dit_file_ntdsutil.json|2023-07-19 16:02`
- Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`, time `2023-07-19 16:02:24.116`
- Image: `C:\Windows\System32\conhost.exe`; User: `PANDALAB\Administrator`
- CommandLine: `\??\C:\Windows\system32\conhost.exe 0xffffffff -ForceV1`
- parent chain (own process first):

  | level | image | command line | from |
  |---|---|---|---|
  | 0 | `C:\Windows\System32\conhost.exe` | `\??\C:\Windows\system32\conhost.exe 0xffffffff -ForceV1` | this event |
  | 1 | `C:\Windows\System32\cmd.exe` | `"C:\Windows\system32\cmd.exe" ` | Sysmon 1 at 2023-07-19 16:02:23.992 |
  | 2 | `C:\Windows\explorer.exe` | `"C:\Windows\Explorer.EXE" /NoUACCheck` | parent field of the creation event above |

## T1003.006 (7 events, 3 clusters)


### `f75cb76d84f877ff`

- cluster: `T1003.006|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:16`
- Event ID 4662, channel `Security`, time `2020-05-01 23:16:15`
- SubjectUserName: `NEWYORK$` (domain `DMEVALS`)
- ObjectName: `%{11487126-e2dc-4f51-acb1-1b0df0573bb5}`; ObjectType: `%{19195a5b-6da0-11d0-afd3-00c04fd930c9}`; AccessMask: `0x100`
- Properties: `%%7688  		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}  	{19195a5b-6da0-11d0-afd3-00c04fd930c9}  `
- parent chain: none (4662 carries no process fields)

### `01699a20bb1240e9`

- cluster: `T1003.006|covenant_dcsync_dcerpc_drsuapi_DsGetNCChanges_2020-08-05020926.json|2020-08-05 02:10`
- Event ID 4662, channel `Security`, time `2020-08-05 02:10:02`
- SubjectUserName: `pgustavo` (domain `THESHIRE`)
- ObjectName: `%{3933c65d-ac7f-4c79-b5b7-ad0fb941333c}`; ObjectType: `%{19195a5b-6da0-11d0-afd3-00c04fd930c9}`; AccessMask: `0x100`
- Properties: `%%7688  		{1131f6ad-9c07-11d1-f79f-00c04fc2dcd2}  	{19195a5b-6da0-11d0-afd3-00c04fd930c9}  `
- parent chain: none (4662 carries no process fields)

### `2860976038ed386d`

- cluster: `T1003.006|covenant_dcsync_dcerpc_drsuapi_DsGetNCChanges_2020-08-05020926.json|2020-08-05 02:10`
- Event ID 4662, channel `Security`, time `2020-08-05 02:10:02`
- SubjectUserName: `pgustavo` (domain `THESHIRE`)
- ObjectName: `%{3933c65d-ac7f-4c79-b5b7-ad0fb941333c}`; ObjectType: `%{19195a5b-6da0-11d0-afd3-00c04fd930c9}`; AccessMask: `0x100`
- Properties: `%%7688  		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}  	{19195a5b-6da0-11d0-afd3-00c04fd930c9}  `
- parent chain: none (4662 carries no process fields)

### `897e82cd22af2fbd`

- cluster: `T1003.006|covenant_dcsync_dcerpc_drsuapi_DsGetNCChanges_2020-08-05020926.json|2020-08-05 02:10`
- Event ID 4662, channel `Security`, time `2020-08-05 02:10:02`
- SubjectUserName: `pgustavo` (domain `THESHIRE`)
- ObjectName: `%{3933c65d-ac7f-4c79-b5b7-ad0fb941333c}`; ObjectType: `%{19195a5b-6da0-11d0-afd3-00c04fd930c9}`; AccessMask: `0x100`
- Properties: `%%7688  		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}  	{19195a5b-6da0-11d0-afd3-00c04fd930c9}  `
- parent chain: none (4662 carries no process fields)

### `41c9803f3a1f27ef`

- cluster: `T1003.006|empire_dcsync_dcerpc_drsuapi_DsGetNCChanges_2020-09-21185829.json|2020-09-21 18:59`
- Event ID 4662, channel `Security`, time `2020-09-21 18:59:08`
- SubjectUserName: `pgustavo` (domain `THESHIRE`)
- ObjectName: `%{d613d8a5-418b-4b7a-83b8-ae1511c502c4}`; ObjectType: `%{19195a5b-6da0-11d0-afd3-00c04fd930c9}`; AccessMask: `0x100`
- Properties: `%%7688  		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}  	{19195a5b-6da0-11d0-afd3-00c04fd930c9}  `
- parent chain: none (4662 carries no process fields)

### `a8dacd4af416fb89`

- cluster: `T1003.006|empire_dcsync_dcerpc_drsuapi_DsGetNCChanges_2020-09-21185829.json|2020-09-21 18:59`
- Event ID 4662, channel `Security`, time `2020-09-21 18:59:08`
- SubjectUserName: `pgustavo` (domain `THESHIRE`)
- ObjectName: `%{d613d8a5-418b-4b7a-83b8-ae1511c502c4}`; ObjectType: `%{19195a5b-6da0-11d0-afd3-00c04fd930c9}`; AccessMask: `0x100`
- Properties: `%%7688  		{1131f6ad-9c07-11d1-f79f-00c04fc2dcd2}  	{19195a5b-6da0-11d0-afd3-00c04fd930c9}  `
- parent chain: none (4662 carries no process fields)

### `ac42058f1cdd3ac1`

- cluster: `T1003.006|empire_dcsync_dcerpc_drsuapi_DsGetNCChanges_2020-09-21185829.json|2020-09-21 18:59`
- Event ID 4662, channel `Security`, time `2020-09-21 18:59:08`
- SubjectUserName: `pgustavo` (domain `THESHIRE`)
- ObjectName: `%{d613d8a5-418b-4b7a-83b8-ae1511c502c4}`; ObjectType: `%{19195a5b-6da0-11d0-afd3-00c04fd930c9}`; AccessMask: `0x100`
- Properties: `%%7688  		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}  	{19195a5b-6da0-11d0-afd3-00c04fd930c9}  `
- parent chain: none (4662 carries no process fields)

## Notes on the chains

- `d2d8a80c7c8a667f`: the raw file has no Sysmon 1 and no 4688 events at all, so the chain cannot go above powershell.exe.
- `2a127f68cdc4410d`: no Sysmon 1 for this ProcessGuid; the only 4688 with PID 5376 is `taskhostw.exe` (parent `svchost.exe`) at 07:08:22 UTC, after this event at 07:06:21, so it is a reused PID and was not used.
- `243e55d798340ba4`: the 4688 `EventTime` is local time (UTC-4); 03:08:00 local = 07:08:00 UTC, and the first Sysmon event with this ProcessGuid is at 07:08:00.796 UTC, so the MsMpEng.exe creation match is consistent.
- `30f8bc022db8378b`: the full chain is Sysmon 1 by GUID: WaAppAgent.exe -> CollectGuestLogs.exe -> `cmd` -> conhost.exe (the Azure guest agent).

## Whole v3 pool

Defender pattern: `\WindowsAzure\`, `MsMpEng.exe`, `MpCmdRun.exe`, `NisSrv.exe`, `MsSense.exe`, `SenseIR.exe`, `SenseCncProxy.exe`, `MpDefenderCoreService.exe`, `\Windows Defender`, `Windows Defender Advanced Threat Protection` (case-insensitive). "In process or parent chain" checks the image of every chain entry, as rebuilt above. "Anywhere in the event" is a looser extra column: any field of the pool event itself (for example TargetImage or a command line).

| technique | events | process or parent chain matches | anywhere in the event | 4662 events | 4662 with SubjectUserName ending in $ |
|---|---|---|---|---|---|
| T1003.001 | 9 | 0 | 0 | 0 | 0 |
| T1003.006 | 7 | 0 | 0 | 7 | 1 |
| T1021.002 | 8 | 0 | 0 | 0 | 0 |
| T1053.005 | 4 | 0 | 0 | 0 | 0 |
| T1055 | 5 | 0 | 0 | 0 | 0 |
| T1059.001 | 199 | 0 | 0 | 0 | 0 |
| T1059.003 | 2 | 1 | 0 | 0 | 0 |
| T1546.003 | 12 | 0 | 0 | 0 | 0 |
| T1547.001 | 3 | 1 | 1 | 0 | 0 |
| T1562.002 | 40 | 0 | 0 | 0 | 0 |
| **all** | 289 | 2 | 1 | 7 | 1 |
