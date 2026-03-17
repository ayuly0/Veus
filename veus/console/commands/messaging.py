from typing import Optional, Union
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from prompt_toolkit import print_formatted_text, ANSI
from veus.console.registry import cmd
from veus.console.colors import Colors
from veus.console.tui import ChatTUI

@cmd.register(name="message", category="Messaging", description="Send a message", aliases=["msg", "send"])
async def message(ctx, target: str = "focus", content: str = "", amount: Union[int, str] = 1):
    if not ctx.current_guild and target == "all":
        ctx.logger.error("'all' broadcast is only available within a guild context.")
        return

    # Senior Interactivity: If no target, prompt for channel
    if target == "focus" and not ctx.last_channel_id:
        if not ctx.current_guild:
            ctx.logger.error("No guild selected. Use 'sv' first.")
            return
            
        channels = await ctx.current_guild.get_channels()
        choices = [Choice(c['id'], c['name']) for c in channels if c['type'] == 0]
        target = await inquirer.fuzzy(message="Select Channel:", choices=choices).execute_async()
        if not target: return
        
        # Update focus context
        ctx.last_channel_id = target
        for c in choices:
            if c.value == target:
                ctx.last_channel_name = c.name
                break

    target_ids = []
    if target == "focus":
        target_ids = [ctx.last_channel_id]
    elif target == "all":
        channels = await ctx.current_guild.get_channels()
        target_ids = [c['id'] for c in channels if c['type'] == 0]
    elif "," in target:
        target_ids = [tid.strip() for tid in target.split(",")]
    else:
        target_ids = [target]

    if not content:
        content = await inquirer.text(message="Message content:").execute_async()
    
    if not content: return

    try:
        amt_int = int(amount)
    except ValueError:
        ctx.logger.error(f"Invalid amount: {amount}")
        return

    import asyncio
    payloads = [{"content": content} for _ in range(amt_int)]
    tasks = [ctx.rq.mass_post(f"channels/{tid}/messages", payloads) for tid in target_ids]
    
    with ctx.logger.yaspin(text=f"dispatching {amt_int} msg(s) to {len(target_ids)} chan(s)...", color="magenta"):
        await asyncio.gather(*tasks)
    
    ctx.logger.success("sent")

@cmd.register(name="embed", category="Messaging", description="Send a JSON embed (Bot only)")
async def send_embed(ctx, channel_id: str, json_data: str):
    import json
    try:
        payload = json.loads(json_data)
    except Exception as e:
        ctx.logger.error(f"Invalid JSON: {e}")
        return

    if channel_id == "focus":
        channel_id = getattr(ctx, "last_channel_id", None)
        if not channel_id:
            ctx.logger.error("No focus channel.")
            return

    _, status = await ctx.rq.api.post(f"channels/{channel_id}/messages", payload)
    if status == 200:
        ctx.logger.success("Embed sent.")
    else:
        ctx.logger.error(f"Failed to send embed (Status: {status})")

@cmd.register(name="direct", category="Messaging", description="Direct Message a user", aliases=["dm", "priv"])
async def direct(ctx, recipient_id: str, content: str, amount: Union[int, str] = 1):
    if not ctx.user: return
    try:
        amt_int = int(amount)
        await ctx.user.send_dm(recipient_id, content, amt_int)
        ctx.logger.success(f"Sent {amt_int} DM(s) to {recipient_id}")
    except ValueError:
        ctx.logger.error(f"Invalid amount: {amount}")
    except Exception as e:
        ctx.logger.error(f"DM failed: {e}")

@cmd.register(name="dms", category="Messaging", description="List and focus DM conversations")
async def dms(ctx):
    if not ctx.user: return
    
    with ctx.logger.yaspin(text="Fetching conversations..."):
        channels = await ctx.user.get_dms()
        
    if not channels:
        ctx.logger.warn("No active DM conversations found.")
        return
        
    choices = []
    for c in channels:
        # Resolve name: Group name > Recipient list
        name = c.get('name')
        if not name and 'recipients' in c:
            name = ", ".join([r['username'] for r in c['recipients']])
        choices.append(Choice(c['id'], name or f"Unknown DM ({c['id']})"))
        
    selected_id = await inquirer.fuzzy(message="Select DM Conversation:", choices=choices).execute_async()
    if selected_id:
        ctx.last_channel_id = selected_id
        for c in choices:
            if c.value == selected_id:
                ctx.last_channel_name = f"DM:{c.name}"
                break
        ctx.current_guild = None # Clear guild context if we focus a DM
        ctx.logger.success(f"Focused on conversation: {ctx.last_channel_name}")

async def _resolve_message_id(ctx, message_id: str) -> str:
    """Helper to resolve 4-digit suffix to full Snowflake with collision handling."""
    if len(message_id) != 4 or not ctx.last_messages:
        return message_id
        
    matches = ctx.last_messages.get(message_id, [])
    if not matches:
        return message_id
    
    if len(matches) == 1:
        return matches[0]["id"]
        
    # Collision! Show disambiguation menu
    ctx.logger.warn(f"Ambiguous ID '{message_id}' detected ({len(matches)} matches)")
    choices = []
    for m in matches:
        label = f"[{message_id}] {m['author']}: \"{m['content'][:30]}...\""
        choices.append(Choice(m["id"], label))
        
    selected = await inquirer.select(
        message=f"Select the correct message for '{message_id}':",
        choices=choices,
        pointer="▶"
    ).execute_async()
    
    return selected or message_id

@cmd.register(name="fetch", category="Messaging", description="Get recent messages from current channel", aliases=["history", "ls"])
async def fetch(ctx, limit_or_cmd: str = "10", message_id: Optional[str] = None, direction: str = "before"):
    query_params = {}
    
    # 1. Handle Selection
    if limit_or_cmd.lower() == "select":
        ctx.last_channel_id = None
        limit_or_cmd = "10"

    channel_id = getattr(ctx, "last_channel_id", None)
    if not channel_id:
        if ctx.current_guild:
            # Guild Flow
            channels = await ctx.current_guild.get_channels()
            choices = [Choice(c['id'], c['name']) for c in channels if c['type'] == 0]
        elif ctx.user:
            # DM Flow
            ctx.logger.info("No guild focused. Opening DM selection...")
            dms = await ctx.user.get_dms()
            choices = []
            for d in dms:
                name = d.get('name') or ", ".join([r['username'] for r in d.get('recipients', [])])
                choices.append(Choice(d['id'], f"DM: {name}"))
        else:
            ctx.logger.error("No active session or guild context.")
            return

        if not choices:
            ctx.logger.warn("No channels available to fetch from.")
            return

        channel_id = await inquirer.fuzzy(message="Select Channel to fetch:", choices=choices).execute_async()
        if not channel_id: return
        ctx.last_channel_id = channel_id
        for c in choices:
            if c.value == channel_id:
                ctx.last_channel_name = c.name
                break

    # 2. Parse Commands & Windowing
    limit = 10
    try:
        if limit_or_cmd.lower() == "older":
            if not ctx.last_oldest_id:
                ctx.logger.error("No previous fetch found. Fetching latest instead.")
            else:
                query_params["before"] = ctx.last_oldest_id
            limit = int(message_id) if message_id and message_id.isdigit() else 10
        elif limit_or_cmd.lower() == "newer":
            if not ctx.last_newest_id:
                ctx.logger.error("No previous fetch found. Fetching latest instead.")
            else:
                query_params["after"] = ctx.last_newest_id
            limit = int(message_id) if message_id and message_id.isdigit() else 10
        elif limit_or_cmd.isdigit():
            limit = int(limit_or_cmd)
            # If a second arg is provided, it's an ID
            if message_id:
                resolved_id = await _resolve_message_id(ctx, message_id)
                query_params[direction.lower()] = resolved_id
        else:
            # Case: fetch <id> [limit] [direction]
            resolved_id = await _resolve_message_id(ctx, limit_or_cmd)
            query_params[direction.lower()] = resolved_id
            limit = int(message_id) if message_id and message_id.isdigit() else 10
    except Exception:
        limit = 10

    query_params["limit"] = limit
    url = f"channels/{channel_id}/messages?" + "&".join([f"{k}={v}" for k,v in query_params.items()])
    
    data, status = await ctx.rq.api.get(url)
    if status == 200:
        if not data:
            ctx.logger.info("No more messages in this direction.")
            return

        ctx.last_messages = {} # Reset
        # Discord returns newest-first for before, but let's always show chronologically
        sorted_data = sorted(data, key=lambda x: int(x['id']))
        
        # Track window for pagination
        ctx.last_oldest_id = sorted_data[0]['id']
        ctx.last_newest_id = sorted_data[-1]['id']

        # Legacy industrial header
        header = f"{Colors.FG_MAGENTA}○{Colors.RESET} {Colors.FG_WHITE}MESSAGE WINDOW ({len(data)}){Colors.RESET}"
        print_formatted_text(ANSI(f"\n {header}"))
        for m in sorted_data:
            author = m['author']['username']
            content = m['content']
            mid = m['id']
            suffix = mid[-4:]
            
            if suffix not in ctx.last_messages:
                ctx.last_messages[suffix] = []
            ctx.last_messages[suffix].append({"id": mid, "author": author, "content": content})
            
            ref = m.get('message_reference', {})
            ref_str = ""
            if ref and ref.get('message_id'):
                ref_id = ref.get('message_id')
                ref_str = f"{Colors.FG_YELLOW}RE:{ref_id[-4:]} {Colors.RESET}"
            
            # Attachments
            attach_str = ""
            if m.get('attachments'):
                attach_str = " ".join([f"{Colors.FG_GREEN}[{a['url']}]{Colors.RESET}" for a in m['attachments']])
            
            print_formatted_text(ANSI(f" {Colors.FG_CYAN}{suffix}{Colors.RESET} | {ref_str}{Colors.FG_WHITE}{author}{Colors.RESET}: {content} {attach_str}"))
        print_formatted_text(ANSI(""))
    else:
        ctx.logger.error(f"Failed to fetch messages (Status: {status})")

@cmd.register(name="reply", category="Messaging", description="Reply to a message", aliases=["re"])
async def reply(ctx, message_id: str, content: str):
    channel_id = getattr(ctx, "last_channel_id", None)
    if not channel_id:
        ctx.logger.error("No channel active. Use 'fetch' or 'message' first.")
        return
    
    full_id = await _resolve_message_id(ctx, message_id)

    payload = {
        "content": content,
        "message_reference": {"message_id": full_id}
    }
    data, status = await ctx.rq.api.post(f"channels/{channel_id}/messages", payload)
    if status == 200:
        ctx.logger.success("Reply sent.")
    else:
        ctx.logger.error(f"Failed to send reply (Status: {status})")

@cmd.register(name="inspect", category="Messaging", description="View details of a specific message", aliases=["view", "v", "show"])
async def inspect(ctx, message_id: str):
    channel_id = getattr(ctx, "last_channel_id", None)
    if not channel_id:
        ctx.logger.error("No channel active.")
        return

    full_id = await _resolve_message_id(ctx, message_id)

    # Try direct retrieval first
    data, status = await ctx.rq.api.get(f"channels/{channel_id}/messages/{full_id}")
    
    # Fallback: Some tokens/channels prefer 'around' query for single message inspection
    if status == 403 or status == 404:
        data_list, status = await ctx.rq.api.get(f"channels/{channel_id}/messages?around={full_id}&limit=1")
        if status == 200 and data_list:
            data = data_list[0]
        else:
            ctx.logger.error(f"Message inaccessibile (Status: {status})")
            return

    if status == 200:
        author = data['author']['username']
        content = data.get('content', '{No Content}')
        ts = data['timestamp']
        
        # Legacy industrial header
        hdr = f"{Colors.FG_MAGENTA}○{Colors.RESET} {Colors.FG_WHITE}INSPECT {full_id}{Colors.RESET}"
        print_formatted_text(ANSI(f"\n {hdr}"))
        print_formatted_text(ANSI(f"   {Colors.FG_CYAN}Author:{Colors.RESET}   {author}"))
        print_formatted_text(ANSI(f"   {Colors.FG_CYAN}Time:{Colors.RESET}     {ts}"))
        
        ref = data.get('message_reference', {})
        if ref and ref.get('message_id'):
            print_formatted_text(ANSI(f"   {Colors.FG_YELLOW}Reply to:{Colors.RESET}  {ref.get('message_id')}"))
            
        # Attachments in inspect
        if data.get('attachments'):
            print_formatted_text(ANSI(f"   {Colors.FG_GREEN}Attachments:{Colors.RESET}"))
            for a in data['attachments']:
                print_formatted_text(ANSI(f"     - {a['url']}"))
            
        print_formatted_text(ANSI(f"\n   {Colors.FG_WHITE}{content}{Colors.RESET}\n"))
    else:
        ctx.logger.error(f"Inaccessible: Received status {status}")

@cmd.register(name="clear-self", category="Messaging", description="Delete your last own messages", aliases=["cs", "purge-me"])
async def clear_self(ctx, amount: Union[int, str] = 10):
    channel_id = getattr(ctx, "last_channel_id", None)
    if not channel_id:
        ctx.logger.error("No channel active. Use 'fetch' or 'message' first.")
        return

    try:
        limit = int(amount)
    except ValueError:
        ctx.logger.error(f"Invalid amount: {amount}")
        return

    if not ctx.user or not ctx.user.id:
        ctx.logger.error("User ID not initialized.")
        return

    with ctx.logger.yaspin(text=f"Purging {limit} of your messages...", color="magenta"):
        # We need to fetch enough messages to find 'limit' of ours
        # Discord limit is usually 100 per fetch
        fetched = 0
        deleted = 0
        before_id = None
        
        while deleted < limit and fetched < 500: # Safety cap
            url = f"channels/{channel_id}/messages?limit=100"
            if before_id:
                url += f"&before={before_id}"
            
            messages, status = await ctx.rq.api.get(url)
            if status != 200 or not messages:
                break
            
            before_id = messages[-1]['id']
            fetched += len(messages)
            
            my_messages = [m['id'] for m in messages if m['author']['id'] == ctx.user.id]
            
            for mid in my_messages:
                if deleted >= limit:
                    break
                _, d_status = await ctx.rq.api.delete(f"channels/{channel_id}/messages/{mid}")
                if d_status in (200, 204):
                    deleted += 1
                elif d_status == 429: # Rate limit
                    await asyncio.sleep(1) # Simple backoff
                
            if len(messages) < 100:
                break

    ctx.logger.success(f"Cleared {deleted} message(s).")

@cmd.register(name="chat", category="Messaging", description="Enter interactive TUI chat mode", aliases=["tui"])
async def chat_mode(ctx):
    """Switch to a live, fullscreen interactive chat TUI."""
    if not ctx.last_channel_id:
        ctx.logger.error("No channel focused. Use 'select' or 'fetch' first.")
        return
        
    tui = ChatTUI(ctx)
    await tui.run()
