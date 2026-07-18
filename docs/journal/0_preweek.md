# Preweek Technical Documnetation

## Technical Goals
1. Main: Determine how well Agent Architectures fit our business use case.
2. Additional/Personal: Learn new things like Claude Code, Skills, and AI Agents

## Technical Uncertainty
- Scope of Agent/Harness folder access
- Level of intelligence of the various Claude models and how well they will do playing the MUD

## Technical Hypotheses
I think the agent will be able to play the game moderately well.

## Technical Observations
Sonnet was much batter than Haiku at navigating the world. Leveling up did not go well as the character kept dying.
### Observations with Haiku:
- Claude asked if it could have permissions higher up in the directory tree but I declined.
- Agent creates temp files for scripts. We want a persistent/common interface.
- Haiku model in Claude does not seem to be very good at figuring out the issues.

### Observations with Sonnet:
- Moved world-haiku file (world data output by Haiku) up a directory so that sonnet wouldn't cheat and use it
- Sonnet found the bakery quickly and printed the menu.

## Technical Conclusions
- Agent Skill does work, but we'll need much more complex state
- We need auditable visibility

## Key Takeaway
When we have a specialized use-case like a playing a MUD, we likely cannot leverage generic SDKs or Agents because we need specialized tooling and agentic loops.