import discord
from discord.ext import commands
import os
import random
import asyncio
import aiohttp
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup with all intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Remove default help command
bot.remove_command('help')

# Store user warnings (in production, use a database)
user_warnings = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set bot status
    await bot.change_presence(activity=discord.Game(name="!help for commands"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument. Use `!help {ctx.command.name}` for usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Invalid argument. Use `!help {ctx.command.name}` for correct usage.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# ==================== COMMAND 1: HELP ====================
@bot.command(name='help')
async def custom_help(ctx, command_name=None):
    """Shows help information for all commands or a specific command"""
    if command_name:
        # Show help for specific command
        command = bot.get_command(command_name)
        if command:
            embed = discord.Embed(
                title=f"Help: !{command.name}",
                description=command.help or "No description available.",
                color=discord.Color.blue()
            )
            if command.aliases:
                embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
            embed.add_field(name="Usage", value=f"!{command.name} {command.signature}", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Command `{command_name}` not found.")
    else:
        # Show all commands grouped by category
        embed = discord.Embed(
            title="🤖 Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )
        
        # Fun Commands
        fun_commands = ["`!ping`", "`!roll`", "`!8ball`", "`!meme`", "`!rps`"]
        embed.add_field(
            name="🎮 Fun Commands",
            value=", ".join(fun_commands),
            inline=False
        )
        
        # Utility Commands
        utility_commands = ["`!userinfo`", "`!avatar`", "`!serverinfo`", "`!weather`"]
        embed.add_field(
            name="🔧 Utility Commands",
            value=", ".join(utility_commands),
            inline=False
        )
        
        # Moderation Commands
        mod_commands = ["`!kick`", "`!ban`", "`!clear`", "`!warn`"]
        embed.add_field(
            name="🛡️ Moderation Commands",
            value=", ".join(mod_commands),
            inline=False
        )
        
        embed.set_footer(text="Use !help <command> for more details on a specific command.")
        await ctx.send(embed=embed)

# ==================== COMMAND 2: PING ====================
@bot.command(name='ping', help='Check bot latency')
async def ping(ctx):
    """Check the bot's response time"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: **{latency}ms**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# ==================== COMMAND 3: ROLL ====================
@bot.command(name='roll', aliases=['dice'], help='Roll a dice (e.g., !roll 6)')
async def roll(ctx, sides: int = 6):
    """Roll a dice with specified number of sides (default: 6)"""
    if sides < 2:
        await ctx.send("❌ Dice must have at least 2 sides!")
        return
    
    result = random.randint(1, sides)
    embed = discord.Embed(
        title="🎲 Dice Roll",
        description=f"You rolled a **{result}** (1-{sides})",
        color=discord.Color.random()
    )
    await ctx.send(embed=embed)

# ==================== COMMAND 4: 8BALL ====================
@bot.command(name='8ball', help='Ask the magic 8-ball a question')
async def eight_ball(ctx, *, question):
    """Ask the magic 8-ball a question and get a mystical answer"""
    responses = [
        "It is certain.", "It is decidedly so.", "Without a doubt.",
        "Yes - definitely.", "You may rely on it.", "As I see it, yes.",
        "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
        "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
        "Cannot predict now.", "Concentrate and ask again.",
        "Don't count on it.", "My reply is no.", "My sources say no.",
        "Outlook not so good.", "Very doubtful."
    ]
    
    embed = discord.Embed(
        title="🎱 Magic 8-Ball",
        color=discord.Color.purple()
    )
    embed.add_field(name="Question", value=question, inline=False)
    embed.add_field(name="Answer", value=random.choice(responses), inline=False)
    embed.set_footer(text=f"Asked by {ctx.author.name}")
    await ctx.send(embed=embed)

# ==================== COMMAND 5: RPS ====================
@bot.command(name='rps', help='Play Rock Paper Scissors with the bot (!rps rock)')
async def rps(ctx, choice: str):
    """Play Rock Paper Scissors against the bot"""
    choices = ['rock', 'paper', 'scissors']
    if choice.lower() not in choices:
        await ctx.send("❌ Please choose from: rock, paper, or scissors")
        return
    
    bot_choice = random.choice(choices)
    player_choice = choice.lower()
    
    # Determine winner
    if player_choice == bot_choice:
        result = "It's a tie!"
    elif (player_choice == 'rock' and bot_choice == 'scissors') or \
         (player_choice == 'paper' and bot_choice == 'rock') or \
         (player_choice == 'scissors' and bot_choice == 'paper'):
        result = "You win! 🎉"
    else:
        result = "Bot wins! 🤖"
    
    embed = discord.Embed(
        title="✂️ Rock Paper Scissors",
        color=discord.Color.blue()
    )
    embed.add_field(name="Your choice", value=player_choice.capitalize(), inline=True)
    embed.add_field(name="Bot's choice", value=bot_choice.capitalize(), inline=True)
    embed.add_field(name="Result", value=result, inline=False)
    await ctx.send(embed=embed)

# ==================== COMMAND 6: USERINFO ====================
@bot.command(name='userinfo', aliases=['ui'], help='Get information about a user')
async def userinfo(ctx, member: discord.Member = None):
    """Get detailed information about a user (defaults to yourself)"""
    if member is None:
        member = ctx.author
    
    roles = [role.mention for role in member.roles[1:]]  # Skip @everyone
    
    embed = discord.Embed(
        title=f"User Info - {member.name}",
        color=member.color or discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
    embed.add_field(name="Bot", value="✅ Yes" if member.bot else "❌ No", inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Joined Discord", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles) if roles else "None", inline=False)
    
    await ctx.send(embed=embed)

# ==================== COMMAND 7: AVATAR ====================
@bot.command(name='avatar', aliases=['av'], help='Get a user\'s avatar')
async def avatar(ctx, member: discord.Member = None):
    """Get the avatar of a user (defaults to yourself)"""
    if member is None:
        member = ctx.author
    
    embed = discord.Embed(
        title=f"{member.name}'s Avatar",
        color=member.color or discord.Color.blue()
    )
    embed.set_image(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

# ==================== COMMAND 8: SERVERINFO ====================
@bot.command(name='serverinfo', aliases=['si'], help='Get information about the server')
async def serverinfo(ctx):
    """Get detailed information about the current server"""
    guild = ctx.guild
    
    # Count members by status
    online = sum(1 for member in guild.members if member.status != discord.Status.offline)
    total = guild.member_count
    bots = sum(1 for member in guild.members if member.bot)
    humans = total - bots
    
    embed = discord.Embed(
        title=guild.name,
        description=guild.description or "No description",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.utcnow()
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name=f"Members ({total})", value=f"👤 Humans: {humans}\n🤖 Bots: {bots}\n🟢 Online: {online}", inline=True)
    embed.add_field(name="Channels", value=f"📁 Categories: {len(guild.categories)}\n💬 Text: {len(guild.text_channels)}\n🔊 Voice: {len(guild.voice_channels)}", inline=True)
    embed.add_field(name="Other", value=f"🚀 Boost Level: {guild.premium_tier}\n🎨 Roles: {len(guild.roles)}", inline=True)
    
    await ctx.send(embed=embed)

# ==================== COMMAND 9: KICK ====================
@bot.command(name='kick', help='Kick a member from the server (requires kick permissions)')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kick a member from the server (Moderator only)"""
    if member == ctx.author:
        await ctx.send("❌ You cannot kick yourself!")
        return
    
    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ You cannot kick someone with equal or higher roles!")
        return
    
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"{member.mention} has been kicked.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to kick that member!")

# ==================== COMMAND 10: CLEAR ====================
@bot.command(name='clear', aliases=['purge'], help='Clear messages in the channel (requires manage_messages)')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """Clear a specified number of messages (Moderator only)"""
    if amount <= 0:
        await ctx.send("❌ Please specify a positive number of messages to clear!")
        return
    
    if amount > 100:
        await ctx.send("❌ You can only clear up to 100 messages at once!")
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)  # +1 for the command message
    await ctx.send(f"✅ Cleared {len(deleted) - 1} messages!", delete_after=3)

# ==================== EXTRA COMMANDS (Bonus) ====================

# COMMAND 11: WEATHER (Bonus)
@bot.command(name='weather', help='Get weather information for a city')
async def weather(ctx, *, city):
    """Get current weather for a city (mock data - in production use weather API)"""
    # This is mock weather data - in production, use a weather API
    weather_conditions = ["☀️ Sunny", "⛅ Partly Cloudy", "☁️ Cloudy", "🌧️ Rainy", "⛈️ Thunderstorm", "❄️ Snowy"]
    temperatures = range(-10, 40)
    
    embed = discord.Embed(
        title=f"Weather for {city.title()}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Condition", value=random.choice(weather_conditions), inline=True)
    embed.add_field(name="Temperature", value=f"{random.choice(temperatures)}°C", inline=True)
    embed.add_field(name="Humidity", value=f"{random.randint(30, 90)}%", inline=True)
    embed.add_field(name="Wind Speed", value=f"{random.randint(0, 30)} km/h", inline=True)
    embed.set_footer(text="Note: This is simulated weather data")
    await ctx.send(embed=embed)

# COMMAND 12: MEME (Bonus)
@bot.command(name='meme', help='Get a random meme')
async def meme(ctx):
    """Get a random meme (mock data - in production use meme API)"""
    memes = [
        "https://i.imgur.com/3PzjRqV.jpg",
        "https://i.imgur.com/4ZQjKqX.jpg",
        "https://i.imgur.com/5YRqVpZ.jpg",
        "https://i.imgur.com/6GqVrXq.jpg"
    ]
    
    embed = discord.Embed(
        title="😂 Random Meme",
        color=discord.Color.gold()
    )
    embed.set_image(url=random.choice(memes))
    embed.set_footer(text="Note: This is simulated meme data")
    await ctx.send(embed=embed)

# COMMAND 13: WARN (Bonus)
@bot.command(name='warn', help='Warn a member (requires moderate_members)')
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    """Warn a member and keep track of warnings"""
    if member == ctx.author:
        await ctx.send("❌ You cannot warn yourself!")
        return
    
    if member.id not in user_warnings:
        user_warnings[member.id] = []
    
    warning = {
        'moderator': ctx.author.id,
        'reason': reason,
        'date': datetime.datetime.utcnow().isoformat()
    }
    
    user_warnings[member.id].append(warning)
    warn_count = len(user_warnings[member.id])
    
    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=f"{member.mention} has been warned.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Warning Count", value=str(warn_count), inline=True)
    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Error: DISCORD_TOKEN not found in .env file")
