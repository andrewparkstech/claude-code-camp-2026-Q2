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

- Used /plugins and searched for skill-creator. Chose to install for local scope. Claude installed and enabled. Typed /skills and skill-creator was listed.
- When creating the skill, I noticed Claude accessing circlemud-world-parser so I interrupted and asked it to only access 02_agent_skills.
- Claude asked me a few design questions to complete the skill
- When done, I prompted Claude to find the bakery and show me the menu. It completed this within a few seconds.