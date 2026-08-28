# AGP-004 - Sensitive Data Handling

An agent that can access confidential, personal, or otherwise sensitive
data must keep its exposure to that data as small as possible, and must
never send it to a system or model that hasn't been approved to receive
it.

## Required controls

- Know what category of data an agent can touch before it's deployed.
- Share only the minimum data actually needed for the task at hand.
- Strip secrets and personal information out of logs and prompts before
  they're written or sent anywhere.
