from typing import Optional, Union
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from veus.console.registry import cmd
from veus.console.colors import Colors

@cmd.register(name="create-channel", category="Management", description="Mass create channels", aliases=["cc"])
async def create_channel(ctx, name: str, amount: Union[int, str] = 1, type_str: str = "text"):
    if not ctx.current_guild:
        ctx.logger.error("No guild selected.")
        return
        
    try:
        amount_int = int(amount)
        # Map type string to Discord IDs: 0=text, 2=voice, 4=category
        type_map = {"text": 0, "voice": 2, "category": 4}
        
        # Support both named types and raw numeric type IDs
        if type_str.isdigit():
            ctype = int(type_str)
        else:
            ctype = type_map.get(type_str.lower(), 0)
        
        ctx.logger.info(f"Creating {amount_int} channel(s) (Type: {ctype}) named '{name}'...")
        await ctx.current_guild.create_channels(name, ctype, amount_int)
        ctx.logger.success("Channel creation tasks dispatched.")
    except ValueError:
        ctx.logger.error(f"Invalid amount: {amount}")
    except Exception as e:
        ctx.logger.error(f"Failed to create channels: {e}")

@cmd.register(name="delete-channels", category="Management", description="Mass delete channels", aliases=["dc"])
async def delete_channels(ctx, pattern: str = "select"):
    if not ctx.current_guild:
        ctx.logger.error("No guild selected.")
        return
        
    channels = await ctx.current_guild.get_channels()
    
    if pattern == "select":
        choices = [Choice(c['id'], c['name']) for c in channels]
        selected = await inquirer.fuzzy(
            message="Select channels to delete (Use TAB to multi-select):",
            choices=choices,
            multiselect=True
        ).execute_async()
        
        if not selected:
            return
            
        ctx.logger.warn(f"Deleting {len(selected)} channels...")
        await ctx.current_guild.delete_channels(selected)
        ctx.logger.success("Channels deleted.")
    else:
        # Pattern match (e.g. all channels starting with 'test-')
        to_delete = [c['id'] for c in channels if pattern in c['name']]
        if not to_delete:
            ctx.logger.warn(f"No channels matched pattern: {pattern}")
            return
            
        confirm = await inquirer.confirm(message=f"Delete {len(to_delete)} channels matching '{pattern}'?").execute_async()
        if confirm:
            await ctx.current_guild.delete_channels(to_delete)
            ctx.logger.success(f"Deleted {len(to_delete)} channels.")

@cmd.register(name="server-config", category="Management", description="Update server settings", aliases=["sc"])
async def server_config(ctx, name: Optional[str] = None, icon: Optional[str] = None, banner: Optional[str] = None, desc: Optional[str] = None):
    if not ctx.current_guild:
        ctx.logger.error("No guild selected.")
        return
        
    if not any([name, icon, banner, desc]):
        ctx.logger.warn("No settings provided. Use help to see usage.")
        return

    ctx.logger.info("Updating server settings...")
    success = await ctx.current_guild.update_guild(
        name=name,
        icon=icon,
        banner=banner,
        description=desc
    )
    
    if success:
        ctx.logger.success("Server settings updated successfully.")
    else:
        ctx.logger.error("Failed to update server settings. Check permissions and file paths.")

@cmd.register(name="webhook", category="Management", description="Manage and send via webhooks")
async def webhook(ctx, action: str = "list", target: Optional[str] = None, *, content: Optional[str] = None):
    if not ctx.current_guild and action != "send":
        ctx.logger.error("No guild selected. (except for 'send' if you have the URL)")
        return
        
    if action == "list":
        webhooks = await ctx.current_guild.get_webhooks()
        if not webhooks:
            ctx.logger.warn("No webhooks found in this guild.")
            return
        print(f"\n{Colors.FG_BLUE}Webhooks in {ctx.current_guild.name}:{Colors.RESET}")
        for w in webhooks:
            print(f" {Colors.FG_CYAN}{w['id']}{Colors.RESET} | {Colors.FG_WHITE}{w['name']}{Colors.RESET} (Channel: {w['channel_id']})")
        print("")

    elif action == "create":
        name = target or await inquirer.text(message="Enter webhook name:").execute_async()
        channels = await ctx.current_guild.get_channels()
        choices = [Choice(c['id'], c['name']) for c in channels if c['type'] == 0]
        cid = await inquirer.fuzzy(message="Select Channel for webhook:", choices=choices).execute_async()
        if not cid or not name: return
        
        res = await ctx.current_guild.create_webhook(cid, name)
        if res:
            ctx.logger.success(f"Webhook created: {res['name']} ({res['id']})")
            print(f" URL: {res['url']}")
        else:
            ctx.logger.error("Failed to create webhook.")

    elif action == "delete":
        wid = target
        if not wid:
            webhooks = await ctx.current_guild.get_webhooks()
            choices = [Choice(w['id'], f"{w['name']} ({w['id']})") for w in webhooks]
            wid = await inquirer.fuzzy(message="Select Webhook to delete:", choices=choices).execute_async()
            if not wid: return
            
        if await ctx.current_guild.delete_webhook(wid):
            ctx.logger.success("Webhook deleted.")
        else:
            ctx.logger.error("Failed to delete webhook.")

    elif action == "send":
        # target can be webhook ID or URL
        url = target
        if not url:
            webhooks = await ctx.current_guild.get_webhooks()
            choices = [Choice(w['url'], f"{w['name']}") for w in webhooks]
            url = await inquirer.fuzzy(message="Select Webhook to send from:", choices=choices).execute_async()
            if not url: return

        if not content:
            content = await inquirer.text(message="Message content:").execute_async()
        if not content: return

        # Handling sending (Webhooks don't need token if we have URL, but our RQ uses token)
        # We'll use a direct request if it's a full URL
        if url.startswith("http"):
            _, status = await ctx.rq.api.post(url, {"content": content}, use_base_url=False)
        else:
            # Assume ID, try to find URL in guild webhooks
            webhooks = await ctx.current_guild.get_webhooks()
            found = next((w for w in webhooks if w['id'] == url), None)
            if found:
                _, status = await ctx.rq.api.post(found['url'], {"content": content}, use_base_url=False)
            else:
                ctx.logger.error(f"Webhook ID {url} not found.")
                return

        if status in [200, 204]:
            ctx.logger.success("Webhook message sent.")
        else:
            ctx.logger.error(f"Failed to send (Status: {status})")
    else:
        ctx.logger.error(f"Unknown action: {action}. Use list, create, delete, send.")
