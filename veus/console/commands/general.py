import os
import inspect
from typing import Optional
from prompt_toolkit import print_formatted_text, ANSI
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
    """Senior help system, legacy hybrid style."""
    base = "  "
    
    if command:
        metadata = cmd.get_command(command)
        if metadata:
            # Command header: Square brackets
            hdr = f"{Colors.FG_CYAN}[{Colors.RESET}{Colors.FG_WHITE}{metadata.name.upper()}{Colors.RESET}{Colors.FG_CYAN}]{Colors.RESET}"
            print_formatted_text(ANSI(f"\n{base}{hdr}"))
            if metadata.aliases:
                print_formatted_text(ANSI(f"{base} {Colors.FG_CYAN}Aliases{Colors.RESET}  {Colors.FG_WHITE}·{Colors.RESET} {', '.join(metadata.aliases)}"))
            print_formatted_text(ANSI(f"{base} {Colors.FG_CYAN}Usage{Colors.RESET}    {Colors.FG_WHITE}·{Colors.RESET} {metadata.usage}"))
            print_formatted_text(ANSI(f"{base} {Colors.FG_CYAN}About{Colors.RESET}    {Colors.FG_WHITE}·{Colors.RESET} {metadata.description}"))
            if metadata.params:
                print_formatted_text(ANSI(f"{base} {Colors.FG_CYAN}Args{Colors.RESET}"))
                for p in metadata.params:
                    default_str = f" = {p.default}" if p.default != inspect.Parameter.empty else ""
                    print_formatted_text(ANSI(f"{base}   {Colors.FG_CYAN}◌{Colors.RESET} {p.name}{default_str}"))
            print_formatted_text(ANSI(""))
        else:
            ctx.logger.error(f"command '{command}' unknown")
        return

    categories = cmd.get_categories()
    # Header: Legacy minimalist style
    header = f"{Colors.FG_CYAN}○{Colors.RESET} {Colors.FG_WHITE}VEUS COMMANDS{Colors.RESET}"
    print_formatted_text(ANSI(f"\n{base}{header}\n"))
    
    for category, cmd_names in categories.items():
        # Minimalist grouped display
        names_str = f"{Colors.FG_WHITE}, {Colors.RESET}".join([f"{Colors.FG_CYAN}{name}{Colors.RESET}" for name in sorted(cmd_names)])
        # Category as a clean bracketed tag
        cat_tag = f"{Colors.FG_CYAN}[{Colors.RESET}{Colors.FG_WHITE}{category.ljust(10)}{Colors.RESET}{Colors.FG_CYAN}]{Colors.RESET}"
        print_formatted_text(ANSI(f"{base}{cat_tag} {Colors.FG_CYAN}·{Colors.RESET} {names_str}"))
    
    tip = f"{Colors.FG_WHITE}Tip:{Colors.RESET} Use {Colors.FG_CYAN}help <command>{Colors.RESET} for details."
    print_formatted_text(ANSI(f"\n{base}{tip}\n"))
