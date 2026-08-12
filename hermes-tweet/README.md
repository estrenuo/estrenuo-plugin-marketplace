# Hermes Tweet

Claude Code guidance for installing, configuring, and troubleshooting the
[Hermes Tweet](https://github.com/Xquik-dev/hermes-tweet) plugin on a Hermes
Agent host.

## Install in Claude Code

```text
/plugin marketplace add estrenuo/estrenuo-plugin-marketplace
/plugin install hermes-tweet@estrenuo-plugin-marketplace
```

This marketplace plugin provides the `hermes-tweet` guidance skill. It does not
run Hermes Tweet tools inside Claude Code.

## Install on the Hermes host

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
```

Configure `XQUIK_API_KEY` on the Hermes runtime host for authenticated reads.
The local `tweet_explore` catalogue remains available without a key. Leave
`HERMES_TWEET_ENABLE_ACTIONS` unset or false unless the workflow needs an
explicitly approved action.

After changing runtime variables, use `/reload` in an active Hermes CLI session
or restart gateway and cron sessions.

## Verify

```bash
hermes plugins list
hermes tools list
```

Confirm that `hermes-tweet` is enabled. `tweet_read` requires
`XQUIK_API_KEY`. `tweet_action` stays hidden or disabled unless
`HERMES_TWEET_ENABLE_ACTIONS=true`.

## Source

- [Hermes Tweet repository](https://github.com/Xquik-dev/hermes-tweet)
- [Hermes Tweet installation guide](https://github.com/Xquik-dev/hermes-tweet#install)
- [Xquik dashboard](https://dashboard.xquik.com)

Xquik is an independent third-party service. Not affiliated with X Corp.
"Twitter" and "X" are trademarks of X Corp.
