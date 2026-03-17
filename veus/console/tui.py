import asyncio
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI, to_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout

from veus.console.colors import Colors
from prompt_toolkit.lexers import Lexer

class SimpleAnsiLexer(Lexer):
    """Simple lexer that converts lines containing ANSI codes into formatted text."""
    def lex_document(self, document):
        def get_line(lineno):
            return to_formatted_text(ANSI(document.lines[lineno]))
        return get_line

class ChatTUI:
    """Interactive TUI for real-time Discord messaging with scrolling and replies."""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.channel_id = ctx.last_channel_id
        self.channel_name = ctx.last_channel_name or "Unknown Channel"
        self.messages = []
        self.app: Optional[Application] = None
        
        # UI Elements
        self.history_area = TextArea(
            read_only=True,
            scrollbar=True,
            wrap_lines=True,
            lexer=SimpleAnsiLexer(),
            text="Syncing session history..."
        )
        
        self.input_field = TextArea(
            height=1,
            prompt=" » ",
            multiline=False,
            wrap_lines=False,
        )
        
        # State
        self._running = True
        self._auto_scroll = True

    def _format_messages(self):
        """Format the history buffer for the TUI."""
        output = []
        for m in self.messages:
            author = m.get('author', 'Unknown')
            content = m.get('content', '')
            
            # Handle reply context (quoted format as requested)
            reply_to = m.get('reply_to')
            if reply_to:
                ref_author = reply_to.get('author', 'Unknown')
                ref_content = reply_to.get('content', '')
                # Quoted style: "> author: content"
                output.append(f" {Colors.FG_WHITE}> {ref_author}: {ref_content}{Colors.RESET}")
            
            output.append(f"{Colors.FG_CYAN}{author}:{Colors.RESET} {content}")
        return "\n".join(output)

    def _update_history_ui(self):
        """Update the history area and scroll to bottom if auto-scroll is on."""
        formatted_text = self._format_messages()
        self.history_area.text = formatted_text
        
        if self._auto_scroll:
            # Move cursor to the very end to force scrolling to bottom
            self.history_area.buffer.cursor_position = len(formatted_text)

    async def _handle_message(self, data):
        """Gateway handler for live TUI updates across all users."""
        if data.get('channel_id') == self.channel_id:
            author = data['author']['username']
            content = data.get('content', '')
            mid = data['id']
            
            # Check for referenced message (Discord Reply)
            ref_msg = None
            ref = data.get('referenced_message')
            if ref and isinstance(ref, dict):
                ref_msg = {
                    'author': ref.get('author', {}).get('username', 'Unknown'),
                    'content': ref.get('content', '')
                }
            
            msg_obj = {
                'id': mid,
                'author': author,
                'content': content,
                'reply_to': ref_msg
            }
            
            self.messages.append(msg_obj)
            
            # Update UI immediately
            self._update_history_ui()
            
            # Force immediate redraw of the UI
            if self.app:
                self.app.invalidate()

    async def run(self):
        """Launch the full-screen interactive TUI."""
        if not self.channel_id:
            self.ctx.logger.error("No channel focused for TUI.")
            return

        kb = KeyBindings()

        @kb.add('c-c')
        @kb.add('c-q')
        def _exit(event):
            self._running = False
            event.app.exit()

        @kb.add('enter')
        def _send(event):
            content = self.input_field.text.strip()
            if not content: return
            
            # Send message via API
            # Note: For strict Discord replies we'd need a message ID to reply to.
            # For now, we allow the "> " style for visual quotes as requested.
            asyncio.create_task(self.ctx.rq.api.post(
                f"channels/{self.channel_id}/messages", 
                {"content": content}, 
                silent=True
            ))
            
            self.input_field.text = ""
            self._auto_scroll = True
            self._update_history_ui()

        # Keyboard Navigation for History
        @kb.add('pageup')
        def _page_up(event):
            self._auto_scroll = False
            self.history_area.buffer.cursor_up(count=10)

        @kb.add('pagedown')
        def _page_down(event):
            self.history_area.buffer.cursor_down(count=10)
            if self.history_area.buffer.document.is_cursor_at_the_end:
                self._auto_scroll = True

        @kb.add('up')
        def _up(event):
            self._auto_scroll = False
            self.history_area.buffer.cursor_up()

        @kb.add('down')
        def _down(event):
            self.history_area.buffer.cursor_down()
            if self.history_area.buffer.document.is_cursor_at_the_end:
                self._auto_scroll = True

        # UI Layout Structure
        root_container = HSplit([
            # Static Header
            Window(height=1, content=FormattedTextControl(
                ANSI(f" {Colors.FG_MAGENTA}◌{Colors.RESET} {Colors.FG_WHITE}VEUS CHAT{Colors.RESET} {Colors.FG_CYAN}·{Colors.RESET} {Colors.FG_WHITE}#{self.channel_name}{Colors.RESET}")
            ), align=WindowAlign.CENTER, style="bg:#1a1a1a"),
            
            # Scrollable History Area
            self.history_area,
            
            # Divider
            Window(height=1, char="─", style="fg:#333333"),
            
            # Input Field
            self.input_field,
            
            # Help / Copy Note
            Window(height=1, content=FormattedTextControl(
                ANSI(f" {Colors.FG_YELLOW}ℹ{Colors.RESET} {Colors.FG_WHITE}Note: Mouse selection disabled. Use {Colors.FG_CYAN}Shift + Select{Colors.FG_WHITE} to copy text.{Colors.RESET}")
            ), style="bg:#1a1a1a")
        ])

        # Gateway Integration
        self.ctx.gateway.on("MESSAGE_CREATE", self._handle_message)
        
        # Load Recent History on startup
        history, status = await self.ctx.rq.api.get(f"channels/{self.channel_id}/messages?limit=50")
        if status == 200:
            for m in reversed(history):
                ref_msg = None
                ref = m.get('referenced_message')
                if ref and isinstance(ref, dict):
                    ref_msg = {
                        'author': ref.get('author', {}).get('username', 'Unknown'),
                        'content': ref.get('content', '')
                    }
                
                self.messages.append({
                    'id': m['id'],
                    'author': m['author']['username'],
                    'content': m['content'],
                    'reply_to': ref_msg
                })
            self._update_history_ui()

        self.app = Application(
            layout=Layout(root_container, focused_element=self.input_field),
            key_bindings=kb,
            mouse_support=False,
            full_screen=True,
        )

        try:
            await self.app.run_async()
        finally:
            # Cleanup listener on exit
            if self._handle_message in self.ctx.gateway._event_handlers.get("MESSAGE_CREATE", []):
                self.ctx.gateway._event_handlers["MESSAGE_CREATE"].remove(self._handle_message)
