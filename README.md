# Faucet bot for substrate python3 based

This bot is a really simple bot without security or threshold. It's used to send coins with discord.

## How to use :

A configmap named "test-net-faucet-bot-config" can be used to override the default values as specified in the following table
Please adapt to your target namespace

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-net-faucet-bot-config
  namespace: jx-devbr
data:
  DISCORD_BOT_TOKEN: very
  FAUCET_MNEMONIC: charm
```


Default values are as follows

|Key|Description|
|---|---|
|DISCORD_BOT_TOKEN|The secret bot token to use for connecting to discord|
|NODE_RPC|https://wss.test.peaq.network|
|FAUCET_MNEMONIC|use the value from subkey generate|
|TOKENS_TO_SEND|1000000000000000000|
|TOKEN_SYMBOL|PEAQ|
|ISSUE_INTERVAL|5|
|REDIS_IP|127.0.0.1|
|REDIS_PORT|6379|


Additionally a secret must be created under the name of "test-net-faucet-bot-secret" containing the bot token and key mnemonic.
Remember to change the DISCORD_BOT_TOKEN and FAUCET_MNEMONIC variable's data to actual values.
Use the following command to encode to base64

```bash
#encode with disabled line wrapping
echo -n 'secret here' | base64 -w 0
```

```yaml
apiVersion: v1
data:
  DISCORD_BOT_TOKEN: bXlwYXNzd29yZA==
  FAUCET_MNEMONIC: bXlwYXNzd29yZA==
kind: Secret
metadata:
  name: test-net-faucet-bot-secret
  namespace: jx-devbr
type: Opaque
```