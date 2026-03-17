import os
import inspect
from typing import Optional
from veus.console.registry import cmd
from veus.console.colors import Colors

@cmd.register(category="General", description="Clear terminal screen")
async def clear(ctx):
    os.system("cls" if os.name == "nt" else "clear")

@cmd.register(category="General", description="Exit application", aliases=["q", "quit"])
async def exit(ctx):
    ctx._running = False
    if ctx.rq: await ctx.rq.shutdown()
    os._exit(0)

@cmd.register(category="General", description="Show this message", aliases=["h"])
async def help(ctx, command: Optional[str] = None):
    """Minimal and beautiful help system."""
    if command:
        metadata = cmd.get_command(command)
        if metadata:
            print(f"\n {Colors.FG_CYAN}○{Colors.RESET} {Colors.FG_WHITE}{metadata.name.upper()}{Colors.RESET}")
            if metadata.aliases:
                print(f"   {Colors.FG_CYAN}Aliases:{Colors.RESET} {', '.join(metadata.aliases)}")
            print(f"   {Colors.FG_CYAN}Usage:{Colors.RESET}   {metadata.usage}")
            print(f"   {Colors.FG_CYAN}About:{Colors.RESET}   {metadata.description}")
            if metadata.params:
                print(f"   {Colors.FG_CYAN}Args:{Colors.RESET}")
                for p in metadata.params:
                    default_str = f" = {p.default}" if p.default != inspect.Parameter.empty else ""
                    print(f"     - {p.name}{default_str}")
            print("")
        else:
            ctx.logger.error(f"Command '{command}' unknown.")
        return

    categories = cmd.get_categories()
    print(f"\n {Colors.FG_CYAN}VEUS{Colors.RESET} {Colors.FG_WHITE}COMMANDS{Colors.RESET}\n")
    
    for category, cmd_names in categories.items():
        # Minimalist grouped display
        names_str = f"{Colors.FG_WHITE}, {Colors.RESET}".join([f"{Colors.FG_CYAN}{name}{Colors.RESET}" for name in sorted(cmd_names)])
        print(f"  {Colors.FG_WHITE}{category.ljust(12)}{Colors.RESET} {Colors.FG_CYAN}·{Colors.RESET} {names_str}")
    
    print(f"\n {Colors.FG_WHITE}Tip:{Colors.RESET} Use {Colors.FG_CYAN}help <command>{Colors.RESET} for details.")
    print("")
