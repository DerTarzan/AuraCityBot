import discord
import asyncio
import threading
from base.bot import AuraCityBot
from base.logger import AuraCityLogger

class AuraCity(AuraCityBot):
    def __init__(self):
        super().__init__()
        self.config.DEV_MODE = True
        self.logger = AuraCityLogger(self.__class__.__name__).get_logger()

    async def start_bot(self):
        try:
            self.load_cogs("base/cogs")
            await self.start(self.config.TOKEN)  # Start bot asynchronously
        except discord.LoginFailure:
            token = self.config.TOKEN
            if token is not None:
                if len(token) != 59:
                    self.logger.error("Invalid token length provided. Please provide a valid token.")
                    return
            else:
                self.logger.error("No token provided. Please provide a valid token.")
                return


async def main():
    aura_city = AuraCity()
    try:
        await aura_city.start_bot()
    except RuntimeError as err:
        # Handle runtime errors, such as closed event loops
        aura_city.logger.error(f"Runtime error occurred: {err}")
    except Exception as err:
        # Catch all other exceptions
        aura_city.logger.error(f"An error occurred: {err}")

    finally:
        # Perform any necessary cleanup here
        aura_city.logger.info("Shutting down bot and tasks...")


if __name__ == "__main__":
    # Global exception handler for threading issues
    def handle_thread_exceptions(args):
        aura_city_logger = AuraCityLogger("ThreadException", create_file_handler=False).get_logger()
        aura_city_logger.error(f"Unhandled exception in thread: {args.exc_type.__name__}: {args.exc_value}")


    threading.excepthook = handle_thread_exceptions  # Custom thread exception handler

    # Catch unhandled exceptions
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        AuraCityLogger("Main", create_file_handler=False).get_logger().info("Program terminated by user.")
    except RuntimeError as e:
        AuraCityLogger("Main", create_file_handler=False).get_logger().error(f"Unhandled runtime exception: {e}")
    except Exception as e:
        AuraCityLogger("Main", create_file_handler=False).get_logger().error(f"Unhandled exception occurred: {e}")
    finally:
        AuraCityLogger("Main", create_file_handler=False).get_logger().info("Exiting program...")