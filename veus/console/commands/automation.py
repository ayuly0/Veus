import asyncio
import re
from typing import Optional
from prompt_toolkit import print_formatted_text, ANSI
from veus.console.registry import cmd
from veus.console.colors import Colors

# Regex for Discord Gift Links
GIFT_REGEX = re.compile(r"(discord\.gift/|discord\.com/gifts/)([a-zA-Z0-9]+)")

@cmd.register(name="claim-nitro", category="Automation", description="Toggle automated Nitro gift claiming")
async def claim_nitro(ctx):
    """Enable or disable the background Nitro gift sniper."""
    if not hasattr(ctx, "nitro_sniper_active"):
        ctx.nitro_sniper_active = False
        
    ctx.nitro_sniper_active = not ctx.nitro_sniper_active
    status = f"{Colors.FG_GREEN}ENABLED{Colors.RESET}" if ctx.nitro_sniper_active else f"{Colors.FG_RED}DISABLED{Colors.RESET}"
    
    if ctx.nitro_sniper_active:
        ctx.gateway.on("MESSAGE_CREATE", _nitro_handler(ctx))
        ctx.logger.success(f"Nitro Sniper {status}. Watching all channel buffers...")
    else:
        # Note: Proper cleanup would require removing the listener, but for now we just toggle the flag
        ctx.logger.info(f"Nitro Sniper {status}. Stopping background listeners.")

def _nitro_handler(ctx):
    async def handler(data):
        if not getattr(ctx, "nitro_sniper_active", False): return
        
        content = data.get("content", "")
        match = GIFT_REGEX.search(content)
        if match:
            code = match.group(2)
            ctx.logger.warn(f"Gift Code Detected: {Colors.FG_CYAN}{code}{Colors.RESET} | Attempting claim...")
            
            # Redemption Endpoint
            res, status = await ctx.rq.api.post(f"entitlements/gift-codes/{code}/redeem", silent=True)
            if status == 200:
                ctx.logger.success(f"Successfully claimed Nitro gift: {code}!")
            else:
                ctx.logger.error(f"Failed to claim gift ({status}): {res.get('message', 'Unknown Error')}")
    return handler

@cmd.register(name="ghost-msg", category="Automation", description="Send a message via ghost webhook", aliases=["ghost"])
async def ghost_msg(ctx, channel_id: Optional[str] = None, *, content: str):
    """Send a message via a temporary webhook that is deleted immediately after."""
    cid = channel_id or ctx.last_channel_id
    if not cid:
        ctx.logger.error("No channel focused or ID provided.")
        return

    ctx.logger.info("Initializing ghost broadcast...")
    
    # 1. Create Webhook
    name = "Veus Ghost"
    wh = await ctx.current_guild.create_webhook(cid, name) if ctx.current_guild else None
    if not wh:
        # Fallback: try to create via direct API if guild context is missing
        res, status = await ctx.rq.api.post(f"channels/{cid}/webhooks", {"name": name}, silent=True)
        if status == 200: wh = res
        
    if not wh:
        ctx.logger.error("Failed to create ghost webhook. Check permissions.")
        return

    # 2. Send Message
    wh_url = wh['url']
    _, status = await ctx.rq.api.post(wh_url, {"content": content}, use_base_url=False, silent=True)
    
    # 3. Delete Webhook
    await ctx.rq.api.delete(f"webhooks/{wh['id']}", silent=True)
    
    if status in [200, 204]:
        ctx.logger.success("Ghost message broadcasted and trace purged.")
    else:
        ctx.logger.error(f"Failed to send ghost message (Status: {status})")

@cmd.register(name="react-all", category="Automation", description="Dispatch reactions from all vault tokens", aliases=["react-mass"])
async def react_all(ctx, message_id: str, emoji: str, channel_id: Optional[str] = None):
    """Orchestrate a mass reaction from all identity tokens."""
    cid = channel_id or ctx.last_channel_id
    if not cid:
        ctx.logger.error("No channel focused.")
        return

    ctx.logger.info(f"Dispatching reaction '{emoji}' from {len(ctx.rq.vault)} identities...")
    
    encoded_emoji = emoji.replace("#", "%23")
    tasks = [api.put(f"channels/{cid}/messages/{message_id}/reactions/{encoded_emoji}/@me", silent=True) for api in ctx.rq.vault]
    results = await asyncio.gather(*tasks)
    
    success = sum(1 for _, status in results if status == 204)
    if success > 0:
        ctx.logger.success(f"Orchestration complete. {success}/{len(ctx.rq.vault)} reactions placed.")
    else:
        ctx.logger.error("Failed to dispatch reactions. Check tokens and permissions.")
