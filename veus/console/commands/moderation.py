from typing import Optional
from veus.console.registry import cmd
from veus.console.colors import Colors

@cmd.register(name="ban", category="Moderation", description="Ban a user from the server")
async def ban(ctx, user_id: str, reason: Optional[str] = None):
    if not ctx.current_guild:
        ctx.logger.error("No guild selected.")
        return
        
    # [Inference] Most "Senior" tools allow 4-digit ID resolution for users too, 
    # but for now we stick to full Snowflakes for safety on bans.
    
    success = await ctx.current_guild.ban(user_id, reason)
    if success:
        ctx.logger.success(f"Successfully banned {user_id}")
    else:
        ctx.logger.error(f"Failed to ban {user_id}. check permissions.")

@cmd.register(name="kick", category="Moderation", description="Kick a user from the server")
async def kick(ctx, user_id: str, reason: Optional[str] = None):
    if not ctx.current_guild:
        ctx.logger.error("No guild selected.")
        return
        
    success = await ctx.current_guild.kick(user_id, reason)
    if success:
        ctx.logger.success(f"Successfully kicked {user_id}")
    else:
        ctx.logger.error(f"Failed to kick {user_id}. Check permissions.")
