import asyncio
import traceback
import logging
log = logging.getLogger(__name__)

async def wait(flag):
    """Often, we want to sequence multiple actions that need to happen
    after a single coro.

    Wait allows you to purely block on a coro completing whilst discarding the
    result, and allows this to happen multiple times.

    Parameters
    ----------

    flag : Coroutine
        The flag that we are waiting to terminate.    
    """
    fut = asyncio.ensure_future(flag)
    try:
        await fut
    except RuntimeError:
        log.debug(traceback.format_exc())
        pass
    return

async def multiple_waits(flags):
    """Same as :meth:`wait`, but for waiting on multiple coroutines.

    Parameters
    ----------

    flags : list
        A list of :class:`Coroutine` objects to wait for.
    """
    for flag in flags:
        await wait(flag)
    return
