# Refactor Plan

## Current State / Issues
- Demo run incorrect: Set3/Set4 DB outputs wrong; driver reports TIMEOUT even though nodes commit/execute, indicating reply path broken.
- After LF, elections/timers spam the log and keep running even when live nodes < 3; process doesn't exit promptly.
- NEW-VIEW handling likely incomplete: AcceptLog merge/no-op fill and majority ACCEPTED ? COMMIT may not drive followers to converge; followers may execute without COMMIT.
- Client/Driver coupling weak: driver relies on timeouts, not on client reply; committed TX still marked TIMEOUT.
- Recovering nodes replay/execute earlier seqs but may not catch up before elections, causing repeated elections and extra log noise.

## Goals
- Correct stable-leader Paxos per spec: Promise/AcceptLog ? NEW-VIEW with NO-OP fill ? ACCEPTED majority ? COMMIT ? EXECUTE (idempotent) with client reply.
- Message-driven completion only: driver waits for client reply; client keeps retrying/broadcasting until reply or explicit skip.
- Quorum awareness: when live < 3 (f=2), skip remaining TX and suppress elections/timers; when =3 continue.
- Clean exit after last set; eliminate runaway election/timer spam; reduce debug noise.

## Planned Changes
1) Client/Driver
   - Client retries indefinitely (periodic broadcast) until a CLIENT_REPLY arrives or an explicit skip is issued; no fixed max-attempt TIMEOUT exits.
   - Driver waits for client result instead of using fixed timeouts; marks SKIPPED immediately if live<3 after LF.
2) Leader/NEW-VIEW path
   - Merge AcceptLog on leadership change: highest ballot per seq, fill missing seq with NO-OP, send NEW-VIEW tagged with new ballot.
   - Followers on NEW-VIEW send ACCEPTED for each entry but execute only on COMMIT; leader waits for majority ACCEPTED, then COMMIT, executes idempotently, resends client reply.
3) Recovery / Election control
   - On RECOVER, request missing commits before participating; suppress starting elections when live<3; short, bounded election timers to avoid log storms.
4) Logging/Performance
   - Keep PrintDB/PrintLog/PrintStatus/PrintView; reduce timer/election debug spam to speed runs.

## Verification
- Run `py -3.7 -m da paxos.da demo > run_demo.log 2>&1` and confirm DB per set:
  - Set1 A:9 B:11 C:9 D:11 E:10 F:10 G:10 H:10 I:10 J:10
  - Set2 A:9 B:11 C:9 D:11 E:9 F:11 G:9 H:11 I:10 J:10
  - Set3 A:10 B:10 C:9 D:11 E:9 F:11 G:9 H:11 I:9 J:11
  - Set4 A:10 B:10 C:10 D:10 E:10 F:10 G:10 H:10 I:9 J:11
- Ensure process exits cleanly after demo; no endless election/timer loops when quorum is lost.
