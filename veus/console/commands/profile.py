from veus.console.registry import cmd

@cmd.register(name="relogin", category="Session", description="Switch account / Relogin", aliases=["switch"])
async def relogin(ctx):
    await ctx.login()

@cmd.register(name="profile", category="Profile", description="Update user bio", aliases=["bio", "me", "whoami"])
async def profile(ctx, bio: str):
    if await ctx.user.update_profile(bio=bio):
        ctx.logger.success("Profile updated.")

@cmd.register(name="status", category="Profile", description="Set online status (online, dnd, idle, invisible)", aliases=["presence"])
async def status(ctx, type: str):
    types = ["online", "dnd", "idle", "invisible"]
    if type.lower() not in types:
        ctx.logger.error(f"Invalid status. Choose from: {', '.join(types)}")
        return
        
    payload = {"status": type.lower()}
    _, res_status = await ctx.rq.api.patch("users/@me/settings", payload)
    if res_status == 200:
        ctx.logger.success(f"Status set to {type}.")
    else:
        ctx.logger.error("Failed to set status (Note: Some User tokens may not support this endpoint).")

@cmd.register(name="activity", category="Profile", description="Set custom status text", aliases=["custom"])
async def activity(ctx, text: str):
    payload = {"custom_status": {"text": text}}
    _, res_status = await ctx.rq.api.patch("users/@me/settings", payload)
    if res_status == 200:
        ctx.logger.success(f"Activity set to: {text}")
    else:
        ctx.logger.error("Failed to set activity.")
