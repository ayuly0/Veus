from veus.console.registry import cmd
from veus.console.colors import Colors

@cmd.register(category="Config", description="Update a configuration setting")
async def config_set(ctx, key: str, value: str):
    """Set a config value. Example: config-set ssl_verify False"""
    if key not in ctx.config.all:
        ctx.logger.error(f"Unknown config key: {key}")
        return
        
    # Cast value appropriately
    old_val = ctx.config.get(key)
    new_val = value
    
    if isinstance(old_val, bool):
        new_val = value.lower() in ["true", "1", "yes"]
    elif isinstance(old_val, int):
        new_val = int(value)
    elif isinstance(old_val, float):
        new_val = float(value)

    ctx.config.set(key, new_val)
    ctx.logger.success(f"Config updated: {Colors.FG_CYAN}{key}{Colors.RESET} = {new_val}")
    
    # Apply immediate changes if applicable
    if key == "proxy_strategy":
        ctx.proxy_mgr.strategy = new_val
    elif key == "ssl_verify" and ctx.rq:
        ctx.rq.api._verify = new_val
        await ctx.rq.api.rotate_proxy() # Re-init client with new SSL setting

@cmd.register(name="settings", category="Config", description="View current settings", aliases=["config", "cfg", "view"])
async def settings(ctx):
    """Display all persistent settings."""
    print(f"\n {Colors.FG_CYAN}○{Colors.RESET} {Colors.FG_WHITE}VEUS CONFIGURATION{Colors.RESET}\n")
    for k, v in ctx.config.all.items():
        print(f"   {Colors.FG_CYAN}{k.ljust(15)}{Colors.RESET} : {v}")
    print("")
