1. An agent file with referenced files e.g. AGENT.md

Observations:
- Claude asked if it could have permissions higher up in the directory tree but I declined.
- Agent creates temp files for scripts. We want a persistent/common interface.
- Haiku model in Claude does not seem to be very good at figuring out the issues. First it was using bash scripting. I had to ask for an update on progress multiple times, at which point I had to direct it on how to proceed before it would make intelligent decisions. It tried Expect scipting next. Then went to Pyton. I had to tell it to send linefeeds after the menu choices.
