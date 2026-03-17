from prompt_toolkit import print_formatted_text, ANSI
from veus.console.registry import cmd
from veus.console.colors import Colors

@cmd.register(category="Proxy", description="Show proxy pool statistics")
async def proxy_stats(ctx):
    mgr = ctx.rq.api._proxy_mgr
    if not mgr:
        ctx.logger.error("No proxy manager active.")
        return
        
    print_formatted_text(ANSI(f"\n{Colors.FG_BLUE}Proxy Pool Stats:{Colors.RESET}"))
    print_formatted_text(ANSI(f"  Strategy: {mgr.strategy}"))
    print_formatted_text(ANSI(f"  Total:    {mgr.total_count}"))
    print_formatted_text(ANSI(f"  Healthy:  {mgr.healthy_count}"))
    print_formatted_text(ANSI(f"  Current Index: {mgr._index}"))
    print_formatted_text(ANSI(""))

@cmd.register(category="Proxy", description="Switch rotation strategy")
async def proxy_mode(ctx, mode: str):
    """Switch between 'round-robin' and 'random'."""
    mgr = ctx.rq.api._proxy_mgr
    if not mgr: return
    
    if mode.lower() in ["round-robin", "random"]:
        mgr.strategy = mode.lower()
        ctx.config.set("proxy_strategy", mode.lower())
        ctx.logger.success(f"Strategy switched to: {mode}")
    else:
        ctx.logger.error("Invalid strategy. Use 'round-robin' or 'random'.")

@cmd.register(category="Proxy", description="Force proxy rotation")
async def proxy_rotate(ctx):
    if not ctx.rq.api._proxy_mgr:
        ctx.logger.error("No proxies loaded.")
        return
        
    await ctx.rq.api.rotate_proxy()
    ctx.logger.success("Proxy manually rotated.")

@cmd.register(category="Proxy", description="Add a proxy to the pool")
async def proxy_add(ctx, proxy_url: str):
    mgr = ctx.rq.api._proxy_mgr
    if not mgr:
        ctx.logger.error("No proxy manager active.")
        return
        
    mgr.add_proxies([proxy_url])
    ctx.logger.success(f"Added proxy to pool: {proxy_url}")
