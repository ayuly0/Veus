import asyncio
import sys
from veus.console.logger import Logger
from veus.console.menu import Menu

async def main():
    logger = Logger(debug=True)
    menu = Menu(logger)
    
    try:
        await menu.start()
    except KeyboardInterrupt:
        logger.info("Exiting Veus...")
    except Exception as e:
        logger.error(f"Critical error: {e}", fatal=True)
    finally:
        if menu.rq:
            await menu.rq.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)