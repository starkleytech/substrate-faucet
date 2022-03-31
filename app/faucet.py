import os
from pickletools import read_decimalnl_short
import time
import redis
from discord.ext import commands
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException
from substrateinterface.utils.ss58 import ss58_encode

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
TOKENS_TO_SEND = get_env_var_or_exit("TOKENS_TO_SEND")
#the token symbol
TOKEN_SYMBOL = get_env_var_or_exit("TOKEN_SYMBOL")
#how often can a user ask for a token? in seconds
ISSUE_INTERVAL = get_env_var_or_exit("ISSUE_INTERVAL")
#redis
REDIS_IP = get_env_var_or_exit("REDIS_IP")
REDIS_PORT = get_env_var_or_exit("REDIS_PORT")

# associated address 5CfVS8r8sNiioYi4YmtJjPhYgxcxuMXYg1Gkp91LtHCmkqiQ
bot = commands.Bot(command_prefix='!')
keypair = Keypair.create_from_mnemonic(FAUCET_MNEMONIC)


@bot.command(name='send', help='Send token from faucet')
async def nine_nine(ctx, arg):
    
    if (str(ctx.channel.type) == "private"):
        # Forbid DM in discord
        await ctx.send("Hold on Capt'ain, you can't send me private messages !")
    else:
        
        #ensure we comply with send frequency
        r = redis.Redis(host=REDIS_IP, port=REDIS_PORT)
        if r.exists(arg):
            await ctx.send("You can only request once every [{}] second(s) !".format(ISSUE_INTERVAL))
            return
        else:
            r.set(name=arg,value="set")
            r.expire(arg,ISSUE_INTERVAL)    
        
        
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
        
        msg = " Awesome, you just received \"{}\" {}! The extrinsic hash is [{}]".format(int(TOKENS_TO_SEND)/1000000000000000000, TOKEN_SYMBOL, reply['extrinsic_hash'])
        await ctx.send(str(ctx.author.mention) + msg)
        print(str(ctx.author.name) + msg)

print("Starting bot")
bot.run(DISCORD_BOT_TOKEN)
