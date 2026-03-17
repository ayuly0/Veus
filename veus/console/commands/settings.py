from veus.console.registry import cmd
from veus.console.colors import Colors
from InquirerPy import inquirer

@cmd.register(name="settings", category="System", description="Manage application settings", aliases=["config", "pref"])
async def settings(ctx):
    """Interactive settings menu to manage Veus preferences."""
    while True:
        choices = [
            {"name": f"API Logging: {'[ON]' if ctx.config.get('show_proxy_logs', True) else '[OFF]'}", "value": "show_proxy_logs"},
            {"name": f"SSL Verification: {'[ON]' if ctx.config.get('ssl_verify', True) else '[OFF]'}", "value": "ssl_verify"},
            {"name": "Done", "value": "exit"}
        ]
        
        selected = await inquirer.select(
            message="Application Settings:",
            choices=choices,
            pointer="◌"
        ).execute_async()
        
        if selected == "exit":
            break
            
        if selected == "show_proxy_logs":
            current = ctx.config.get("show_proxy_logs", True)
            new_val = not current
            ctx.config.set("show_proxy_logs", new_val)
            
            # Application of "Hot-Reload"
            if ctx.rq:
                ctx.rq.api._show_logs = new_val
                
            state = f"{Colors.FG_GREEN}Enabled{Colors.RESET}" if new_val else f"{Colors.FG_RED}Disabled{Colors.RESET}"
            ctx.logger.success(f"API Request Logging: {state}")
                
        elif selected == "ssl_verify":
            current = ctx.config.get("ssl_verify", True)
            new_val = not current
            ctx.config.set("ssl_verify", new_val)
            
            state = f"{Colors.FG_GREEN}Enabled{Colors.RESET}" if new_val else f"{Colors.FG_RED}Disabled{Colors.RESET}"
            ctx.logger.success(f"SSL Verification: {state} (Session restart required)")
