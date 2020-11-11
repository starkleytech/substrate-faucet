import os
import random
import discord
from discord.ext import commands
from substrateinterface import SubstrateInterface, Keypair, SubstrateRequestException
from substrateinterface.utils.ss58 import ss58_encode

# Your Discord bot token
TOKEN = ''
faucet_mnemonic = ''
# associated address 5CfVS8r8sNiioYi4YmtJjPhYgxcxuMXYg1Gkp91LtHCmkqiQ
bot = commands.Bot(command_prefix='!')
keypair = Keypair.create_from_mnemonic('faucet_mnemonic')
# substrate RPC node
node_rpc = "http://127.0.0.1:9933"

@bot.command(name='send', help='Send token from faucet')
async def nine_nine(ctx, arg):
    if (ctx.channel.type == "private"):
        # Forbid DM in discord
        await ctx.send("Hold on Capt'ain, you can't send me private messages !")
    else:
        substrate = SubstrateInterface(
            url=node_rpc,
            address_type=42,
            type_registry_preset='substrate-node-template'
        )
        call = substrate.compose_call(
        call_module='Balances',
        call_function='transfer',
        call_params={
            'dest': arg,
            'value': 100 * 10**12
            }
        )   
        reply = ""
        keypair = Keypair.create_from_mnemonic(faucet_mnemonic)
        extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
        reply = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=False)
        await ctx.send(ctx.author.mention + " Awesome, you just received 100 dPIRL, it has no real value it's only the testnet token :) " +  reply['extrinsic_hash'] + str(ctx.channel.type))

bot.run(TOKEN)