import asyncio
import os
from typing import Optional, Union
from prompt_toolkit import print_formatted_text, ANSI
from veus.console.registry import cmd
from veus.console.colors import Colors

# Discord Permission Bits (Simplified for auditing)
PERMS = {
    "ADMINISTRATOR": 1 << 8,
    "MANAGE_GUILD": 1 << 5,
    "MANAGE_ROLES": 1 << 28,
    "MANAGE_CHANNELS": 1 << 4,
    "MANAGE_WEBHOOKS": 1 << 29,
    "MANAGE_SERVER": 1 << 5, # Duplicate of MANAGE_GUILD
    "KICK_MEMBERS": 1 << 1,
    "BAN_MEMBERS": 1 << 2,
    "MENTION_EVERYONE": 1 << 17
}

@cmd.register(name="audit", category="Management", description="Audit guild permissions", aliases=["security", "audit-guild"])
async def audit_guild(ctx):
    """Audit dangerous permissions and roles in the current context."""
    if not ctx.current_guild:
        ctx.logger.error("No guild selected.")
        return

    ctx.logger.info(f"Auditing security for {Colors.FG_CYAN}{ctx.current_guild.name}{Colors.RESET}...")
    roles = await ctx.current_guild.get_roles()
    
    # Industrial Header
    header = f"{Colors.FG_RED}○{Colors.RESET} {Colors.FG_WHITE}SECURITY AUDIT REPORT{Colors.RESET}"
    print_formatted_text(ANSI(f"\n {header}"))
    print_formatted_text(ANSI(f" {Colors.FG_WHITE}──────────────────────────────────────────{Colors.RESET}"))

    vulnerabilities = 0
    for role in roles:
        role_name = role['name']
        perms_int = int(role['permissions'])
        
        found_critical = []
        for name, bit in PERMS.items():
            if perms_int & bit:
                found_critical.append(name)
        
        if found_critical:
            vulnerabilities += 1
            color = Colors.FG_RED if "ADMINISTRATOR" in found_critical else Colors.FG_YELLOW
            print_formatted_text(ANSI(f" {color}[!]{Colors.RESET} {Colors.FG_WHITE}{role_name.ljust(20)}{Colors.RESET}"))
            for p in found_critical:
                print_formatted_text(ANSI(f"     {Colors.FG_CYAN}◌{Colors.RESET} {p}"))

    if vulnerabilities == 0:
        ctx.logger.success("No critical privilege escalations detected in roles.")
    else:
        print_formatted_text(ANSI(f" {Colors.FG_WHITE}──────────────────────────────────────────{Colors.RESET}"))
        ctx.logger.warn(f"Found {vulnerabilities} roles with elevated permissions.")
    print("")

@cmd.register(name="rip-media", category="Messaging", description="Mass download media from channel", aliases=["rip", "exfiltrate"])
async def rip_media(ctx, channel_id: Optional[str] = None, amount: int = 50, exts: str = "jpg,png,gif,mp4"):
    """Download all media attachments from a channel's recent history."""
    cid = channel_id or ctx.last_channel_id
    if not cid:
        ctx.logger.error("No channel ID provided or focused.")
        return

    allowed_exts = [e.strip().lower() for e in exts.split(",")]
    ctx.logger.info(f"Scanning {amount} messages for media ({exts})...")
    
    messages, status = await ctx.rq.api.get(f"channels/{cid}/messages?limit={amount}")
    if status != 200:
        ctx.logger.error("Failed to fetch messages.")
        return

    download_tasks = []
    base_dir = f"downloads/{ctx.current_guild.name if ctx.current_guild else 'NoGuild'}/{cid}"
    
    for msg in messages:
        for attachment in msg.get("attachments", []):
            url = attachment['url']
            filename = attachment['filename']
            ext = filename.split(".")[-1].lower() if "." in filename else ""
            
            if ext in allowed_exts or not allowed_exts:
                dest = os.path.join(base_dir, f"{msg['id']}_{filename}")
                download_tasks.append((url, dest))

    if not download_tasks:
        ctx.logger.warn("No matching media found in history.")
        return

    ctx.logger.info(f"Exfiltrating {len(download_tasks)} files to {base_dir}...")
    results = await ctx.rq.mass_download(download_tasks)
    
    success_count = sum(1 for r in results if r)
    ctx.logger.success(f"Operation complete. {success_count}/{len(download_tasks)} files secured.")
