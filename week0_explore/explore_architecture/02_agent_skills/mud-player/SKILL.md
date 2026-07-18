---
name: mud-player
description: Play tbaMUD (a CircleMUD/DikuMUD-derived text adventure) running on localhost:4000 using the existing "dummy" character. Use this skill whenever the user asks to explore, play, log into, or interact with the MUD, the game on port 4000, tbaMUD, CircleMUD, or "the dummy character" — including requests like "go explore the mud," "level up my character," "see what's in the bakery," "fight some rats," "check on the dummy account," or longer-running goals like "get dummy to level 7" or "go kill the swamp troll" that may span more than one conversation. This skill keeps persistent notes in data/player.md and data/world.md so goals and world knowledge survive between sessions — check those files whenever the user references earlier MUD progress ("how's the leveling going," "keep going," "did we ever find that shop"). Do not attempt to talk to the MUD with raw telnet/nc commands or one-off socket scripts — this skill's daemon handles the login handshake (including MOTD pager screens) and keeps the character safely connected between commands, which a fire-and-forget connection cannot do.
---

# Playing tbaMUD

This skill drives a live, persistent, text-based multiplayer game (a MUD —
Multi-User Dungeon) over a raw TCP socket. There is exactly **one** shared
test character, `dummy` / `helloworld`, so treat it like a shared resource:
other people may be using or reviewing this same character, and its state
(inventory, gold, location, whether it's alive) persists across sessions.

## Long-term memory: data/player.md and data/world.md

`dummy`'s state in the game world outlives any single conversation, and so
can the user's goals — "get to level 7" or "go kill the swamp troll" is
realistically a multi-session project. To make that possible, this skill
keeps two markdown files next to `scripts/` as memory that survives after
the daemon stops and the conversation ends:

- **`data/player.md`** — dummy's own state: level, stats, equipment, gold,
  last known location, and any active long-term goal along with its
  progress (current level vs. target, mobs found vs. still searching for,
  etc).
- **`data/world.md`** — what's been learned about the game world: rooms
  and their exits, shops and their prices, mobs and how dangerous they
  are, quest hooks. There's no in-game map command and no bundled parser
  (see below), so this file *is* the map — without it, every session
  re-discovers Midgaard from scratch.

**At the start of a session**, read both files before doing anything else,
so you're not starting blind on a character/world you've already
partially explored. If they're empty — brand new character, or this is
the very first play session — that's expected; bootstrap them by running
`score`, `inventory`, and `equipment` right after login and writing down
what comes back, then fill in `world.md` as you explore.

**While playing**, treat these as living notes, not a form to fill out
once. Update them when something worth remembering happens: a level or
equipment change, a newly discovered room/shop/NPC, progress toward an
active goal, or something dangerous worth avoiding next time. Don't stop
to edit a file after every single command — that wastes effort and slows
down play — batch updates at natural checkpoints instead (leaving an area
you spent time in, finishing a fight, hitting a milestone), the same way
you'd batch status updates to the user.

**When the user hands you a multi-step goal**, write it into `player.md`
as an explicit active goal with whatever progress markers matter. That's
what lets a *later* conversation — one with no memory of this one — read
the goal back out of `player.md` and keep working toward it when the user
says something as thin as "keep going" or "how's it coming along."

**Trust the live game over stale notes.** If `world.md` says a room has
an exit north but `look` shows otherwise, or `player.md` says dummy was
last in the Armory but the game clearly disagrees, believe the game right
now and correct the note — these files describe the world as of the last
update, not necessarily the present, since other sessions or other people
may have touched the shared character in between.

Keep both files as plain prose you can skim quickly — a few headers
(vitals, active goal, inventory for the player file; one entry per room
or area for the world file) go a long way. Don't force a rigid schema
onto them; what's worth recording varies a lot from session to session,
and free text is easier to extend than a fixed template.

## Why this needs a daemon, not a one-off script

A MUD connection is a live, stateful TCP session, not a request/response
API. Reconnecting for every single command would:
- Re-run the whole login handshake (name → password → MOTD pager screens →
  menu) each time, which is slow and noisy.
- Leave the character **linkless** between commands. In CircleMUD-derived
  games, combat does not pause for a linkless character — if `dummy` is
  fighting something when you disconnect, it can keep taking damage and
  die before you reconnect.

So this skill uses a small background daemon (`scripts/mud_daemon.py`)
that opens the socket once, logs in once, and then stays connected for the
whole play session. You talk to it through a FIFO and read a log file —
both scripts below hide that plumbing.

## Quick start

Run these from the `mud-player/` skill directory (paths below assume that;
adjust if you `cd` elsewhere).

**1. Start a session** (only if one isn't already running — see below):

```bash
python3 scripts/mud_daemon.py > session/daemon_stderr.log 2>&1 &
```

This backgrounds the daemon and returns immediately. Login takes a couple
seconds, so poll `session/status` until it says `ready` (or starts with
`error:`):

```bash
for i in $(seq 1 20); do
  st=$(cat session/status 2>/dev/null)
  [ "$st" = "ready" ] && break
  [[ "$st" == error* ]] && break
  sleep 0.5
done
cat session/status
```

If `session/status` already contains `ready` from an earlier command in
this conversation, there's no need to start a new daemon — reuse it.
`mud_daemon.py` refuses to start a second session on top of an existing
one (it checks `session/daemon.pid`), so if you get a "session already
appears active" error, you already have one running; just start sending
commands.

**2. Send commands and read responses:**

```bash
python3 scripts/mud_cmd.py "look"
python3 scripts/mud_cmd.py "north"
python3 scripts/mud_cmd.py "kill rat"
```

Each call sends one command and prints only the *new* game text that
arrived in response (ANSI color codes and telnet control bytes are
already stripped for you). It waits for the output to go quiet before
returning, so slower responses (e.g. a shop listing, or several rounds of
combat text arriving in bursts) are still captured — but if you send a
command that triggers an extended sequence (multi-round combat, a long
shop transaction), it's fine to call `mud_cmd.py` again with an empty
follow-up like `"look"` if you suspect more happened than what you saw.

**3. Stop the session when you're done** (always do this — see Cleanup):

```bash
python3 scripts/mud_stop.py
```

This sends `quit` through the actual game connection (so the character
logs out cleanly to the character menu, not linkless) before tearing down
the daemon.

## Reading the game's output

CircleMUD-style prompts look like:

```
20H 100M 84V (news) (motd) >
```

That's current hit points / mana / movement points, followed by flags for
unread news/MOTD (harmless, ignore them), then the `>` prompt. When you
see this line at the end of a `mud_cmd.py` response, the game is idle and
waiting for your next command. A room description typically looks like:

```
The Bakery
   You are standing inside the small bakery. ...
[ Exits: s ]
```

There's no bundled parser for room names, exits, or combat messages —
read the cleaned text yourself and reason about it the way you would any
other text. This is deliberate: MUD output is too varied (combat spam,
shop menus, tells, deaths, quest text) for a fixed regex parser to cover
well, and you're better at interpreting free text than a script is.

## Playing autonomously toward a goal

When the user gives you a goal rather than a single command (e.g.
"explore the starting area," "grind to level 3," "find some armor to
buy"), drive the loop yourself: send a command, read the result, decide
the next command, repeat. A few things worth watching for as you do:

- **Track HP.** If the `H` number in the prompt is dropping and you don't
  have a clear plan to win the fight (flee, use a potion, whatever the
  game offers), don't just keep attacking — a MUD character can actually
  die, which has real consequences (possibly losing items/gold, being
  sent back to a starting point). If things look dangerous, consider
  fleeing (`flee` is a common CircleMUD command) or stopping to check with
  the user.
- **Don't loop blindly.** If the same command produces the same "you
  can't do that" or "there's no path that way" response more than once or
  twice, stop and try something else rather than repeating it — the model
  equivalent of walking into a wall.
- **Check in periodically, not after every single move.** For a
  multi-step goal, report back a summary every several actions (where you
  are, what happened, current HP/level) rather than narrating every
  keystroke — that matches what the user actually wants to know.
- **Avoid destructive/irreversible actions** (dropping or selling items,
  giving away gold, character deletion via menu option `5`) unless the
  user's request clearly calls for it — this is a shared character other
  people may be using for other purposes.
- **If the goal spans more than this conversation** (leveling up several
  times, hunting a specific mob that hasn't turned up yet), record it as
  the active goal in `data/player.md` as soon as you understand it, and
  update its progress at the checkpoints described above — see
  [Long-term memory](#long-term-memory-dataplayermd-and-dataworldmd). That
  way if the conversation ends mid-goal, the next one can pick it back up.

## Cleanup

Always call `mud_stop.py` when you're done with a play session — at the
end of the user's request, or before you'd otherwise stop responding.
Leaving the daemon running:
- Keeps `dummy` occupying a connection slot in a live game world.
- Risks the character sitting somewhere unsafe (mid-room, near hostile
  mobs) if a later, unrelated conversation starts a fresh session and
  gets confused by leftover state.

Before stopping, make sure `data/player.md` and `data/world.md` reflect
where things actually stand — current location, level, and active goal
progress in particular. This is the handoff to whatever conversation
picks the character up next, including one where the user doesn't
re-explain the goal at all.

If you started a daemon and the conversation is ending or moving to an
unrelated task, stop it even if the user didn't explicitly ask.

## Troubleshooting

`session/status` is the first thing to check when something seems wrong:

- `connecting` — still logging in; wait and poll again.
- `ready` — connected and idle, safe to send commands.
- `error: <reason>` — login failed. Common causes: the MUD server isn't
  running on port 4000 (check with `nc -z -w2 localhost 4000`), the
  password changed, or the server's MOTD/menu text changed enough that
  `mud_daemon.py`'s pattern matching (`Make your choice`, `PRESS RETURN`,
  the `H`/`M`/`V` prompt) no longer matches — if you suspect this, read
  `session/output.log` directly to see exactly what the server sent
  before giving up.
- `stopped` — session ended cleanly; start a new one before sending more
  commands.

If `mud_cmd.py` reports "No active MUD session," the daemon isn't running
(or died) — check `session/status` and `session/daemon_stderr.log`, then
restart with `mud_daemon.py`.

By default all three scripts default `--session-dir` to the `session/`
directory next to `scripts/`, and `mud_daemon.py` defaults to
`--username dummy --password helloworld` against `localhost:4000` — so
plain `mud_daemon.py` / `mud_cmd.py "look"` / `mud_stop.py` calls with no
extra flags are the normal case. Pass `--username`/`--password` explicitly
only if the user asks you to use a different character.
