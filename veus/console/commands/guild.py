import asyncio
from typing import Optional
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from veus.console.registry import cmd
from veus.console.colors import Colors
from veus.core.guild import Guild

@cmd.register(name="servers", category="Guild", description="Select a guild to manage", aliases=["guilds", "sv"])
async def servers(ctx):
    if not ctx.guilds or not ctx.guilds.items:
        ctx.logger.warn("No guilds found for this account.")
        return
        
    choices = [Choice(gid, name) for gid, name in ctx.guilds.items.items()]
    selected_id = await inquirer.fuzzy(
        message="Select Guild:",
        choices=choices,
        vi_mode=True
    ).execute_async()
    
    if not selected_id: return # User cancelled
    
    ctx.current_guild = Guild(ctx.rq, ctx.logger, selected_id)
    await ctx.current_guild.initialize()
    
    # Clear channel context on server switch
    ctx.last_channel_id = None
    ctx.last_channel_name = None
    ctx.last_messages = {}
    
    ctx.logger.success(f"Context switched to: {ctx.current_guild.name}")

@cmd.register(name="channels", category="Guild", description="List channels in current guild", aliases=["ch", "ls"])
async def channels(ctx, refresh: str = ""):
    if not ctx.current_guild:
        ctx.logger.error("No guild selected. Use 'servers' first.")
        return
    
    do_refresh = refresh.lower() in ["--refresh", "-r", "refresh"]
    channels = await ctx.current_guild.get_channels(force=do_refresh)
    if not channels:
        ctx.logger.warn("No channels found or missing permissions.")
        return
        
    print(f"\n{Colors.FG_BLUE}Channels in {ctx.current_guild.name}:{Colors.RESET}")
    for c in channels:
        if c['type'] != 0: continue # Only text for now
        prefix = f"{Colors.FG_GREEN}▶{Colors.RESET} " if ctx.last_channel_id == c['id'] else "  "
        print(f" {prefix}{Colors.FG_CYAN}{c['id']}{Colors.RESET} | {c['name']}")
    print("")

@cmd.register(name="select", category="Guild", description="Select a channel to focus", aliases=["focus", "use"])
async def select(ctx, channel_id: Optional[str] = None):
    if not ctx.current_guild:
        ctx.logger.error("No guild selected.")
        return
        
    # Use cache for selection UI
    channels = await ctx.current_guild.get_channels()
    
    if not channel_id:
        choices = [Choice(c['id'], c['name']) for c in channels if c['type'] == 0]
        channel_id = await inquirer.fuzzy(message="Select Channel:", choices=choices).execute_async()
        if not channel_id: return
        
        # Extract name from selection
        for c in choices:
            if c.value == channel_id:
                ctx.last_channel_name = c.name
                break
    else:
        # Try to resolve name from cache if ID was provided directly
        for c in channels:
            if c['id'] == channel_id:
                ctx.last_channel_name = c['name']
                break

    ctx.last_channel_id = channel_id
    ctx.logger.success(f"Focused on channel: {ctx.last_channel_name or channel_id}")

@cmd.register(name="purge", category="Moderation", description="Mass delete messages in current channel", aliases=["p"])
async def purge(ctx, amount: int = 50):
    channel_id = getattr(ctx, "last_channel_id", None)
    if not channel_id:
        ctx.logger.error("No channel active. Use 'fetch' or 'message' first.")
        return
        
    ctx.logger.info(f"Purging {amount} messages in {channel_id}...")
    # Fetch message IDs first
    data, status = await ctx.rq.api.get(f"channels/{channel_id}/messages?limit={amount}")
    if status != 200:
        ctx.logger.error("Failed to fetch messages for purge.")
        return
        
    message_ids = [m['id'] for m in data]
    # Re-using delete_channels logic for mass message deletion
    tasks = [ctx.rq.api.delete(f"channels/{channel_id}/messages/{mid}") for mid in message_ids]
    await asyncio.gather(*tasks)
    ctx.logger.success(f"Purged {len(message_ids)} messages.")

@cmd.register(name="slowmode", category="Moderation", description="Set channel slowmode in seconds", aliases=["sm"])
async def slowmode(ctx, seconds: int = 0):
    channel_id = getattr(ctx, "last_channel_id", None)
    if not channel_id:
        ctx.logger.error("No channel active.")
        return
        
    _, status = await ctx.rq.api.patch(f"channels/{channel_id}", {"rate_limit_per_user": seconds})
    if status == 200:
        ctx.logger.success(f"Slowmode set to {seconds}s.")
    else:
        ctx.logger.error("Failed to set slowmode.")
