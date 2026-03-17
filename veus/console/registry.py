import inspect
from dataclasses import dataclass, field
from typing import Callable, Optional, Any, Union
from InquirerPy.base.control import Choice

@dataclass
class CommandMetadata:
    name: str
    func: Callable
    category: str
    description: str
    usage: str
    aliases: list[str] = field(default_factory=list)
    params: list[inspect.Parameter] = field(default_factory=list)
    is_async: bool = True

class CommandRegistry:
    """Senior command registry with metadata and contextual logic."""
    
    def __init__(self):
        self._commands: dict[str, CommandMetadata] = {}
        self._categories: dict[str, list[str]] = {}

    def register(self, name: Optional[str] = None, category: str = "General", description: str = "", aliases: list[str] = None):
        """Decorator to register a command with optional aliases."""
        def decorator(func: Callable):
            cmd_name = name or func.__name__.replace("_", "-")
            cmd_aliases = aliases or []
            
            sig = inspect.signature(func)
            params = list(sig.parameters.values())[1:] # Skip 'ctx'
            
            # Professional usage string generation
            usage = f"{cmd_name}"
            for p in params:
                if p.default == inspect.Parameter.empty:
                    usage += f" <{p.name}>"
                else:
                    usage += f" [{p.name}]"

            metadata = CommandMetadata(
                name=cmd_name,
                func=func,
                category=category,
                description=description,
                usage=usage,
                aliases=cmd_aliases,
                params=params,
                is_async=inspect.iscoroutinefunction(func)
            )
            
            self._commands[cmd_name.lower()] = metadata
            # Map aliases to the same metadata
            for alias in cmd_aliases:
                self._commands[alias.lower()] = metadata
                
            if category not in self._categories:
                self._categories[category] = []
            if cmd_name not in self._categories[category]:
                self._categories[category].append(cmd_name)
            
            return func
        return decorator

    def get_command(self, name: str) -> Optional[CommandMetadata]:
        return self._commands.get(name.lower())

    def get_all_commands(self) -> dict[str, CommandMetadata]:
        return self._commands

    def get_categories(self) -> dict[str, list[str]]:
        return self._categories

    async def get_completer(self, menu_instance: Any):
        """Generates a dynamic prompt_toolkit NestedCompleter."""
        from prompt_toolkit.completion import NestedCompleter
        
        completer_dict = {}
        for name in self._commands:
            completer_dict[name] = None

        # Contextual sub-completions
        if menu_instance.current_guild:
            # For 'msg', we can suggest channel IDs as sub-options
            try:
                channels = await menu_instance.current_guild.get_channels()
                channel_ids = {c['id']: None for c in channels if c['type'] == 0}
                completer_dict["msg"] = channel_ids
                completer_dict["message"] = channel_ids
                completer_dict["fetch"] = {"select": None} # Hint for 'fetch select'
            except Exception:
                pass

        return NestedCompleter.from_nested_dict(completer_dict)

# Global registry for commands
cmd = CommandRegistry()
