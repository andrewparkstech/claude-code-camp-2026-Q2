# Explore Agent Architectures
## 1. An agent file with referenced files e.g. AGENT.md
### Technical Conclusions

#### Observations with Haiku:
- Claude asked if it could have permissions higher up in the directory tree but I declined.
- Agent creates temp files for scripts. We want a persistent/common interface.
- Haiku model in Claude does not seem to be very good at figuring out the issues. First it was using bash scripting. I had to ask for an update on progress multiple times, at which point I had to direct it on how to proceed before it would make intelligent decisions. It tried Expect scipting next. Then went to Pyton. I had to tell it to send linefeeds after the menu choices.

#### Observations with Sonnet:
- Moved world-haiku file up a directory so that sonnet wouldn't cheat and use it
- Sonnet used python right away, logged in to the MUD, searched around, found the bakery and printed the menu.
- Deleted and recreated the dummy user to test Sonnet again
- Sonnet still found the bakery fairly quickly without any issues and updated world.md

## 2. Agent skills driven by main agent e.g. ~/.skills

A common way to drive specific functionality is via Agent Skills which is an open format for agents
adopted by many coding harnesses and agent SDKs.

We should create a skill to connects to the MUD and manages its own data.

### Technical Observations

Used the official claude skill creator and the Sonnet model.

When asked to find the newbie area, it was able to successfully do so.

Next it was asked to level up to level 2. This caused the character to die a few times and the agent then paused asking if it should proceed or not.

### Technical Conclusions
Agent SKill does work, but we'll need much more complex state, world and player management. We need auditable visibility for reporting token/usage and to review the player journey. We need a custom agentic loop that acts and spends less time asking.

#### Additional notes:
- Used /plugins and searched for skill-creator. Chose to install for local scope. Claude installed and enabled. Typed /skills and skill-creator was listed.
- When creating the skill, I noticed Claude accessing circlemud-world-parser so I interrupted and asked it to only access 02_agent_skills.
- Claude asked me a few design questions to complete the skill
- When done, I prompted Claude to find the bakery and show me the menu. It completed this within a few seconds.
- Updated skill with ability to store memory in player.md and world.md
- Asked skill to level up to level 2
  - agent says: 9 exp for 3 HP lost, unarmed — that trade rate would take ~200 fights and isn't safe without healing. Let me check for a weapon shop before grinding further; fighting bare-fisted is inefficient and risky.
