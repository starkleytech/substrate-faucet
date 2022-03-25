import os
import time
import random
import discord
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
NODE_RPC = get_env_var_or_exit("NODE_RPC")
FAUCET_MNEMONIC = get_env_var_or_exit("FAUCET_MNEMONIC")
TOKENS_TO_SEND = get_env_var_or_exit("TOKENS_TO_SEND")
CURRENCY_SYMBOL = get_env_var_or_exit("CURRENCY_SYMBOL")

# associated address 5CfVS8r8sNiioYi4YmtJjPhYgxcxuMXYg1Gkp91LtHCmkqiQ
bot = commands.Bot(command_prefix='!')
keypair = Keypair.create_from_mnemonic(FAUCET_MNEMONIC)


@bot.command(name='send', help='Send token from faucet')
async def nine_nine(ctx, arg):
    if (ctx.channel.type == "private"):
        # Forbid DM in discord
        await ctx.send("Hold on Capt'ain, you can't send me private messages !")
    else:
        substrate = SubstrateInterface(
            url=NODE_RPC,
            address_type=42,
            type_registry_preset='substrate-node-template'
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
        await ctx.send(ctx.author.mention + " Awesome, you just received {} {}, it has no real value it's only the testnet token :) ".format(TOKENS_TO_SEND, CURRENCY_SYMBOL) +  reply['extrinsic_hash'] + str(ctx.channel.type))

bot.run(DISCORD_BOT_TOKEN)
