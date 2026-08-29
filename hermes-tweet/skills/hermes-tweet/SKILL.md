---
name: hermes-tweet
description: >
  Install, configure, verify, or troubleshoot Hermes Tweet, the native Hermes
  Agent X/Twitter plugin powered by Xquik. Use when the user asks how to add
  Hermes Tweet, enable its toolset, configure XQUIK_API_KEY, diagnose missing
  tweet tools, or keep X actions approval-gated.
allowed-tools: Read
---

# Hermes Tweet

Use this skill to guide Hermes Tweet setup on the user's Hermes Agent host.
Do not claim that Claude Code can call Hermes Tweet tools directly.

## Install

1. Ask which machine runs Hermes Agent.
2. Tell the user to run
   `hermes plugins install Xquik-dev/hermes-tweet --enable` on that host.
3. Ask them to configure `XQUIK_API_KEY` in the Hermes runtime environment
   without pasting the key into chat.
4. Tell them to run `hermes plugins list` and `hermes tools list`.

## Tool Gating

- `tweet_explore` searches the bundled endpoint catalogue without an API key.
- `tweet_read` requires `XQUIK_API_KEY`.
- `tweet_action` stays hidden or disabled unless
  `HERMES_TWEET_ENABLE_ACTIONS=true`.
- Keep action mode disabled for read-only, unattended, scheduled, or gateway
  workflows unless the user has an explicit approval step.

## Troubleshooting

- If the plugin is `not enabled`, run
  `hermes plugins enable hermes-tweet`.
- After changing environment variables, use `/reload` in an active Hermes CLI
  session or restart gateway and cron sessions.
- For remote gateway profiles, install and configure Hermes Tweet on the remote
  host where plugin code executes.
- Never request, display, or store an API key in chat.
- Never invent tool availability. Ask for the output of
  `hermes plugins list` and `hermes tools list`.

## Source

Use <https://github.com/Xquik-dev/hermes-tweet> as the authoritative
installation and runtime reference.

Xquik is an independent third-party service. Not affiliated with X Corp.
"Twitter" and "X" are trademarks of X Corp.
