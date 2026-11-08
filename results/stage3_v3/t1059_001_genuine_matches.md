# T1059.001 genuine pairs whose evidence matches another candidate technique or loads a tool

Scanned 53 T1059.001 genuine pairs (51 with evidence, 2 excluded by hand: 10e28166046adcc9|genuine, 565fa9197f8b105b|genuine). 5 pairs match at least one pattern. Nothing is excluded by this list. Categories marked (extra) go beyond the requested list.

| pair | cluster | link | evidence EID | category | field | matched | context |
|---|---|---|---|---|---|---|---|
| `10c9e2221a786d8e|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:11 | pid | 1 | T1021.002 PsExec / remote service | Product | `PsExec` | Sysinternals PsExec |
| `10c9e2221a786d8e|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:11 | pid | 1 | T1021.002 PsExec / remote service | CommandLine | `PsExec` | "C:\Program Files\SysinternalsSuite\PsExec64.exe" -accepteula \\[HOST] -u dmevals\pbeesly -p Fl0nk3rt0n!T0by -i ... |
| `10c9e2221a786d8e|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:11 | pid | 1 | T1021.002 PsExec / remote service | Image | `PsExec` | C:\Program Files\SysinternalsSuite\PsExec64.exe |
| `10c9e2221a786d8e|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:11 | pid | 1 | T1021.002 PsExec / remote service | OriginalFileName | `psexec` | psexec.c |
| `df28c325f68125d2|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:12 | pid | 1 | T1021.002 PsExec / remote service | Product | `PsExec` | Sysinternals PsExec |
| `df28c325f68125d2|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:12 | pid | 1 | T1021.002 PsExec / remote service | CommandLine | `PsExec` | "C:\Program Files\SysinternalsSuite\PsExec64.exe" -accepteula \\[HOST] -u dmevals\pbeesly -p Fl0nk3rt0n!T0by -i ... |
| `df28c325f68125d2|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:12 | pid | 1 | T1021.002 PsExec / remote service | Image | `PsExec` | C:\Program Files\SysinternalsSuite\PsExec64.exe |
| `df28c325f68125d2|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:12 | pid | 1 | T1021.002 PsExec / remote service | OriginalFileName | `psexec` | psexec.c |
| `2120d356ca88c930|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:13 | pid | 1 | T1021.002 PsExec / remote service | Product | `PsExec` | Sysinternals PsExec |
| `2120d356ca88c930|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:13 | pid | 1 | T1021.002 PsExec / remote service | CommandLine | `PsExec` | "C:\Program Files\SysinternalsSuite\PsExec64.exe" -accepteula \\[HOST] -u dmevals\pbeesly -p Fl0nk3rt0n!T0by -i ... |
| `2120d356ca88c930|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:13 | pid | 1 | T1021.002 PsExec / remote service | Image | `PsExec` | C:\Program Files\SysinternalsSuite\PsExec64.exe |
| `2120d356ca88c930|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:13 | pid | 1 | T1021.002 PsExec / remote service | OriginalFileName | `psexec` | psexec.c |
| `d2ea07bf752be380|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:14 | pid | 1 | T1021.002 PsExec / remote service | Product | `PsExec` | Sysinternals PsExec |
| `d2ea07bf752be380|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:14 | pid | 1 | T1021.002 PsExec / remote service | CommandLine | `PsExec` | "C:\Program Files\SysinternalsSuite\PsExec64.exe" -accepteula \\[HOST] -u dmevals\pbeesly -p Fl0nk3rt0n!T0by -i ... |
| `d2ea07bf752be380|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:14 | pid | 1 | T1021.002 PsExec / remote service | Image | `PsExec` | C:\Program Files\SysinternalsSuite\PsExec64.exe |
| `d2ea07bf752be380|genuine` | apt29_evals_day1_manual_2020-05-01225525.json|2020-05-01 23:14 | pid | 1 | T1021.002 PsExec / remote service | OriginalFileName | `psexec` | psexec.c |
| `71baed215173a602|genuine` | psh_disable_eventlog_service_startuptype_modification.json|2022-08-04 08:37 | time | 4103 | T1562.002 Event Log service | Payload | `EventLog` | ...ce): "Set-Service" ParameterBinding(Set-Service): name="Name"; value="EventLog" ParameterBinding(Set-Service): name="StartupType"; value="Disabled"  |

Pairs per category: T1021.002 PsExec / remote service: 4; T1562.002 Event Log service: 1
