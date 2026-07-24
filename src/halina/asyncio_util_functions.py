import asyncio
import logging
from contextlib import suppress
from typing import Awaitable, Iterable

logger = logging.getLogger(__name__.rsplit('.')[-1])


async def wait_for_psce(fut, timeout):
    """
    Meaning: psce - prevent silent cancel error \n
    This is a changed method 'wait_for()' from library 'asyncio' that prevents 'CancelledError' from being ignored
    while the internal task is finished. \n
    Description of the problem: the base method 'wait_for()' also works in such a way that when the inner task
    is finished or there is no place for it to stop, function 'wait_for()' will return the result even if the inner
    task is canceled, so the 'CancelledError' will not be propagated higher. This method prevents this situation.

    :param fut: future oc coroutine
    :param timeout: timeout, czn be float or int number
    """
    task = asyncio.ensure_future(fut)
    try:
        return await asyncio.shield(asyncio.wait_for(task, timeout=timeout))
    except asyncio.CancelledError:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        raise


async def gather_with_hard_deadline(coros: Iterable[Awaitable], timeout: float,
                                    grace: float = 30.0, what: str = "tasks") -> bool:
    """Run coroutines concurrently like `asyncio.gather(return_exceptions=True)`,
    but guarantee to return within roughly `timeout` + `grace` seconds.

    Unlike `asyncio.wait_for`, this never awaits a cancelled task indefinitely: after
    `timeout` the tasks are cancelled and given `grace` seconds to finish; whatever still
    runs afterwards is abandoned with an ERROR log instead of blocking the caller forever.
    A lost cancellation hung the email rapport service for days (issue #43) — this is the
    safety belt against any such hang in the future.

    :param coros: coroutines to run concurrently
    :param timeout: seconds after which the coroutines are cancelled
    :param grace: seconds to wait for the cancelled coroutines to finish
    :param what: label used in log messages
    :return: True if all coroutines completed within `timeout`, False otherwise
    """
    task = asyncio.ensure_future(asyncio.gather(*coros, return_exceptions=True))
    _, pending = await asyncio.wait({task}, timeout=timeout)
    if not pending:
        return True
    logger.error(f"{what} did not finish within {timeout}s — cancelling")
    task.cancel()
    _, still_pending = await asyncio.wait({task}, timeout=grace)
    if still_pending:
        logger.error(f"{what} ignored cancellation for {grace}s — abandoning still-running tasks")
    return False

