import asyncio
import json
import logging
import os
import signal
import sys
import platform

from configuration import GlobalConfig
from halina.email_rapport_service import EmailRapportService
from halina.nats_connection_service import NatsConnectionService

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('main')


def get_setting(name: str, settings: dict):
    if name in settings:
        return settings.get(name, None)
    env = os.getenv(name)
    if env is not None:
        return env
    return None


def set_single_setting(name: str, settings: dict, type_str: bool = True):
    setting = get_setting(name, settings)
    if setting is not None:
        try:
            if not type_str:
                setting = json.loads(setting)
            GlobalConfig.set(name, setting)
        except ValueError:
            logger.warning(f"Can not cast arg: {name}. Variable {name} not set")


def read_configuration(**kwargs):
    set_single_setting(GlobalConfig.NATS_PORT, kwargs, False)
    set_single_setting(GlobalConfig.NATS_HOST, kwargs)
    set_single_setting(GlobalConfig.TELESCOPE_NAMES, kwargs, False)
    set_single_setting(GlobalConfig.TIMEZONE, kwargs, False)
    set_single_setting(GlobalConfig.EMAILS_TO, kwargs, False)
    set_single_setting(GlobalConfig.EMAIL_APP_PASSWORD, kwargs)
    set_single_setting(GlobalConfig.FROM_EMAIL, kwargs)
    set_single_setting(GlobalConfig.FROM_EMAIL_USER, kwargs)
    set_single_setting(GlobalConfig.SMTP_HOST, kwargs)
    set_single_setting(GlobalConfig.SMTP_PORT, kwargs, False)
    set_single_setting(GlobalConfig.SEND_AT, kwargs, False)


async def main_coroutine():
    # Nats connection service
    nats_connection_handler_service = NatsConnectionService()
    email_rapport_service = EmailRapportService()

    services = [nats_connection_handler_service,
                email_rapport_service]
    try:
        # start all services one by one
        for s in services:
            await s.start()

        # wait for all services finished work or will be canceled. Order doesn't matter.
        for s in services:
            await s.join()
    finally:
        # stop all services one by one
        for s in services:
            await s.stop()


def main(**kwargs):
    if not kwargs:
        kwargs = dict(arg.split('=') for arg in sys.argv[0:] if len(arg.split('=')) == 2)
    read_configuration(**kwargs)
    coro = main_coroutine()

    try:
        loop = asyncio.get_running_loop()
        logger.warning("WARNING! Async loop is run before the main method is called")
    except RuntimeError:
        loop = asyncio.new_event_loop()

    def ask_exit():
        raise KeyboardInterrupt

    if platform.system() == 'Windows':
        def windows_sigint_handler(signum, frame):
            ask_exit()
            loop.call_soon_threadsafe(loop.stop)

        signal.signal(signal.SIGINT, windows_sigint_handler)
    else:
        loop.add_signal_handler(signal.SIGINT, ask_exit)

    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            # make sure if all task is finished (router task and every other in this loop)
            all_tasks = asyncio.all_tasks(loop)
            for task in all_tasks:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*all_tasks, return_exceptions=True))
            if not asyncio.all_tasks(loop):
                logger.info('All task in loop is finished')
            else:
                logger.error('Some of the tasks in current loop is still running')
                raise RuntimeError

            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
    return 0


if __name__ == '__main__':
    retcode = main()
    sys.exit(retcode)
