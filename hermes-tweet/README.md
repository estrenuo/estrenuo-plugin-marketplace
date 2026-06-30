# hermes-tweet plugin

Native Hermes Agent X/Twitter plugin for read-first social research, public thread context, monitored account summaries, and approval-gated publishing workflows through Xquik.

## Bevat

**Skills**:

- `hermes-tweet` - routes social research, thread analysis, monitoring, and publishing requests to the Hermes Tweet plugin.

## Installeren

```text
/plugin marketplace add estrenuo/claude-plugin-marketplace
/plugin install hermes-tweet@claude-plugin-marketplace
```

## Vereisten

- Hermes Agent host with the Hermes Tweet plugin installed.
- `XQUIK_API_KEY` configured in the runtime environment.
- `HERMES_TWEET_ENABLE_ACTIONS=true` only when posting, replying, liking, reposting, or following should be available.

## Gebruik

Use this plugin for X/Twitter research, tweet and thread analysis, account monitoring summaries, and draft-first publishing workflows. Read tools stay available with `XQUIK_API_KEY`; write actions stay gated until action mode is explicitly enabled.

## Bron

- Source: <https://github.com/Xquik-dev/hermes-tweet>
- Claude plugin manifest: <https://github.com/Xquik-dev/hermes-tweet/blob/master/.claude-plugin/plugin.json>
