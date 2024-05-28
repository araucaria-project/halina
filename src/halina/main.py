import asyncio
import logging
import signal
import sys


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('main')


async def main_coroutine():
    # todo tutaj wstawić servisy
    # try:
    #     await s1.start()
    #     await s1.join()
    # finally:
    #     await s1.stop()

    pass


def main(argv=None):
    if argv is None:
        argv = sys.argv

    coro = main_coroutine()

    try:
        loop = asyncio.get_running_loop()
        logger.warning("WARNING! Async loop is run before the main method is called")
    except RuntimeError:
        loop = asyncio.new_event_loop()

    def ask_exit():
        raise KeyboardInterrupt
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
    retcode = main(sys.argv)
    sys.exit(retcode)
