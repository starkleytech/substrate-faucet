import os
from pickletools import read_decimalnl_short
import time
from threading import Thread
import redis
from discord.ext import commands
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
from substrateinterface.utils.ss58 import ss58_encode
from prometheus_client import start_http_server, Counter

# prometheus metrics
INVOCATION_COUNT = Counter('invocation_count', 'Number of times tokens have been requested.')
ISSUANCE_TOTAL = Counter('issuance_total', 'Total tokens issued.')
ISSUANCE_THROTTLED = Counter('issuance_throttled', 'Total issuance requests throttled (too quickly requested again).')

def get_env_var_or_exit(var_name):
    var = os.environ.get(var_name)
    
    if var == None or len(var) == 0:
        print("Please check if [{}] is defined. Will exit after 30s sleep".format(var_name))
        time.sleep(30)
        import sys
        sys.exit(1)
    
    return var    

# Your Discord bot token
DISCORD_BOT_TOKEN = get_env_var_or_exit("DISCORD_BOT_TOKEN")
#the address of our network
NODE_RPC = get_env_var_or_exit("NODE_RPC")
#to construct the private/public key pair
FAUCET_MNEMONIC = get_env_var_or_exit("FAUCET_MNEMONIC")
#how many tokens to send, on peaq network 1 PEAQ = 1,000,000,000,000,000,000
TOKENS_TO_SEND = int(get_env_var_or_exit("TOKENS_TO_SEND"))
#the token symbol
TOKEN_SYMBOL = get_env_var_or_exit("TOKEN_SYMBOL")
#how often can a user ask for a token? in seconds
ISSUE_INTERVAL = int(get_env_var_or_exit("ISSUE_INTERVAL"))
#redis
REDIS_IP = get_env_var_or_exit("REDIS_IP")
REDIS_PORT = int(get_env_var_or_exit("REDIS_PORT"))
#prometheus
PROMETHEUS_PORT = int(get_env_var_or_exit("PROMETHEUS_PORT"))

# associated address 5CfVS8r8sNiioYi4YmtJjPhYgxcxuMXYg1Gkp91LtHCmkqiQ
bot = commands.Bot(command_prefix='!')
keypair = Keypair.create_from_mnemonic(FAUCET_MNEMONIC)

@bot.command(name='send', help='Send token from faucet')
async def nine_nine(ctx, arg):
    
    INVOCATION_COUNT.inc()
    
    if arg != None and len(arg) != 48:
        # Inform of an invalid address
        await ctx.send(str(ctx.author.mention) + " That wallet address seems odd - sure you got that right?")
        return
    
    if (str(ctx.channel.type) == "private"):
        # Forbid DM in discord
        await ctx.send("Hold on Capt'ain, you can't send me private messages !")
        return
    
    else:
        
        username = str(ctx.author.name)
        
        #ensure we comply with send frequency
        r = redis.Redis(host=REDIS_IP, port=REDIS_PORT)
        if r.exists(username):
            await ctx.send(str(ctx.author.mention) + " You can only request once every [{}] second(s) !".format(ISSUE_INTERVAL))
            ISSUANCE_THROTTLED.inc()
            return
        else:
            r.set(name=username, value="set")
            r.expire(username, ISSUE_INTERVAL)    
        
        
        substrate = SubstrateInterface(
            url=NODE_RPC
        )
        call = substrate.compose_call(
        call_module='Balances',
        call_function='transfer',
        call_params={
            'dest': arg,
            'value': TOKENS_TO_SEND
            }
        )   
        reply = ""
        extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
        reply = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False)
        
        # inform user
        msg = " Awesome, you just received \"{}\" {}! The extrinsic hash is [{}]".format(TOKENS_TO_SEND/1000000000000000000, TOKEN_SYMBOL, reply['extrinsic_hash'])
        await ctx.send(str(ctx.author.mention) + msg)
        
        # log to console
        print(str(ctx.author.name) + msg)
        
        # store metrics
        ISSUANCE_TOTAL.inc(TOKENS_TO_SEND/1000000000000000000)

def prometheus_server():
    start_http_server(PROMETHEUS_PORT)

print("Starting prometheus server")
t_prometheus = Thread(target=prometheus_server)
t_prometheus.start()

print("Starting bot")
bot.run(DISCORD_BOT_TOKEN)
