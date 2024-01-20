import os
import time
from threading import Thread
import redis
from discord.ext import commands
from substrateinterface import SubstrateInterface, Keypair
from prometheus_client import start_http_server, Counter

# prometheus metrics
INVOCATION_COUNT = Counter('invocation_count', 'Number of times tokens have been requested.')
ISSUANCE_TOTAL = Counter('issuance_total', 'Total tokens issued.')
ISSUANCE_THROTTLED = Counter('issuance_throttled', 'Total issuance requests throttled (too quickly requested again).')


def notify_exit():
    time.sleep(30)
    import sys
    sys.exit(1)


def get_env_var_or_exit(var_name):
    var = os.environ.get(var_name)

    if var is None or len(var) == 0:
        print("Please check if [{}] is defined. Will exit after 30s sleep".format(var_name))
        notify_exit()

    return var


# Your Discord bot token
DISCORD_BOT_TOKEN = get_env_var_or_exit("DISCORD_BOT_TOKEN")
# the address of our network, seperate by "," and should be "ws" or "wss"
NODE_RPC = get_env_var_or_exit("NODE_RPC")
# to construct the private/public key pair, seperate by ","
FAUCET_MNEMONIC = get_env_var_or_exit("FAUCET_MNEMONIC")
# how many tokens to send, on peaq network 1 PEAQ = 1,000,000,000,000,000,000
TOKENS_TO_SEND = int(get_env_var_or_exit("TOKENS_TO_SEND"))
# how many tokens in one token, 10 ** 18
TOKENS_DECIMAL = int(get_env_var_or_exit("TOKENS_DECIMAL"))
# the token symbol
TOKEN_SYMBOL = get_env_var_or_exit("TOKEN_SYMBOL")
# how often can a user ask for a token? in seconds
ISSUE_INTERVAL = int(get_env_var_or_exit("ISSUE_INTERVAL"))
# redis
REDIS_IP = get_env_var_or_exit("REDIS_IP")
REDIS_PORT = int(get_env_var_or_exit("REDIS_PORT"))
# prometheus
PROMETHEUS_PORT = int(get_env_var_or_exit("PROMETHEUS_PORT"))

# associated address 5CfVS8r8sNiioYi4YmtJjPhYgxcxuMXYg1Gkp91LtHCmkqiQ
bot = commands.Bot(command_prefix='!')


def prepare_url_key_pairs(node_rpcs, faucet_mnemonics):
    node_rpc_entires = node_rpcs.split(',')
    for rpc in node_rpc_entires:
        if not rpc.lower().startswith('ws://') and not rpc.lower().startswith('wss://'):
            print('{} fails, please check the env again'.format(rpc))
            notify_exit()

    faucet_mnemonics_entries = faucet_mnemonics.split(',')

    if len(node_rpc_entires) != len(faucet_mnemonics_entries):
        print('the rpc entry is not the same as the faucet entry, please check and redeploy')
        notify_exit()

    return [{
        'rpc_url': node_rpc_entires[i],
        'faucet_kp': Keypair.create_from_mnemonic(faucet_mnemonics_entries[i])
    } for i in range(0, len(node_rpc_entires))]


info_pairs = prepare_url_key_pairs(NODE_RPC, FAUCET_MNEMONIC)


@bot.command(name='send', help='Send token from faucet')
async def nine_nine(ctx, arg):

    INVOCATION_COUNT.inc()

    if arg is not None and len(arg) != 48:
        # Inform of an invalid address
        await ctx.send(str(ctx.author.mention) + " That wallet address seems odd - sure you got that right?")
        return

    if (str(ctx.channel.type) == "private"):
        # Forbid DM in discord
        await ctx.send("Hold on Capt'ain, you can't send me private messages !")
        return

    else:
        username = str(ctx.author.name)

        # ensure we comply with send frequency
        r = redis.Redis(host=REDIS_IP, port=REDIS_PORT)
        if r.exists(username):
            await ctx.send(str(ctx.author.mention) + " You can only request once every [{}] second(s) !".format(ISSUE_INTERVAL))
            ISSUANCE_THROTTLED.inc()
            return
        else:
            r.set(name=username, value="set")
            r.expire(username, ISSUE_INTERVAL)

        extrinsic_url = []
        for info in info_pairs:
            rpc_url = info['rpc_url']
            faucet_kp = info['faucet_kp']

            with SubstrateInterface(url=rpc_url) as substrate:
                call = substrate.compose_call(
                    call_module='Balances',
                    call_function='transfer',
                    call_params={
                        'dest': arg,
                        'value': TOKENS_TO_SEND}
                )
                reply = ""
                extrinsic = substrate.create_signed_extrinsic(call=call, keypair=faucet_kp)
                reply = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False)
                extrinsic_url.append(
                    '{1} on {0}'.format(rpc_url, reply['extrinsic_hash']))

        # inform user
        msg = " Awesome, you just received {} Token! Please check these extrinsic hash. \n {}".format(
            TOKENS_TO_SEND / TOKENS_DECIMAL,
            '\n'.join(extrinsic_url))
        await ctx.send(str(ctx.author.mention) + msg)

        # log to console
        print(str(ctx.author.name) + msg)

        # store metrics
        ISSUANCE_TOTAL.inc(TOKENS_TO_SEND / TOKENS_DECIMAL)


def prometheus_server():
    start_http_server(PROMETHEUS_PORT)


print("Starting prometheus server")
t_prometheus = Thread(target=prometheus_server)
t_prometheus.start()

print("Starting bot")
bot.run(DISCORD_BOT_TOKEN)
