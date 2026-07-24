import logging
from datetime import datetime
from typing import AsyncIterator, Optional, Tuple

from serverish.base import MessengerReaderStopped
from serverish.messenger import get_reader

logger = logging.getLogger(__name__.rsplit('.')[-1])

# Number of extra passes re-probing the stream after the server reported end-of-data.
VERIFICATION_PASSES = 1


async def read_all_records(stream: str, start_time: datetime,
                           verification_passes: int = VERIFICATION_PASSES) -> AsyncIterator[Tuple[dict, dict]]:
    """Yield every (data, meta) record currently available in `stream`, starting from `start_time`.

    Readers are created with `nowait=True`, so the end of data is confirmed by the NATS
    server instead of being emulated with a local read timeout. The old 2 s
    `wait_for(read_next(), 2)` hack cancelled serverish mid-fetch on every normal
    end-of-stream, which could both cut reading short on a slow broker and hang forever
    when the cancel got lost (issue #43).

    Because `nowait` end-of-data could in theory also trigger early (unknown server/client
    race paths), after the main pass the stream is probed again `verification_passes`
    times, continuing from the last consumed sequence number. HALina collects data during
    the day, when telescopes publish nothing, so a verification pass should never find
    anything. If it does, that is a premature end of the previous pass — an ERROR is
    logged, but the records are still yielded to keep the report complete.

    The generator owns the readers and always closes them; callers may stop iterating
    at any point (e.g. on reaching the end of the night in the data).
    """
    last_seq: Optional[int] = None
    records_read = 0
    for pass_no in range(1 + max(0, verification_passes)):
        if last_seq is None:
            reader = get_reader(stream, deliver_policy='by_start_time', opt_start_time=start_time, nowait=True)
        else:
            # continue exactly after the last consumed message
            reader = get_reader(stream, deliver_policy='by_start_sequence', opt_start_seq=last_seq + 1, nowait=True)
        read_in_pass = 0
        try:
            await reader.open()
            while True:
                try:
                    data, meta = await reader.read_next()
                except MessengerReaderStopped:
                    break
                read_in_pass += 1
                yield data, meta
        finally:
            if reader.last_seq is not None:
                last_seq = reader.last_seq
            await reader.close()
        records_read += read_in_pass
        if pass_no > 0 and read_in_pass > 0:
            logger.error(f"Verification pass {pass_no} read {read_in_pass} additional record(s) from {stream} "
                         f"after the server had reported end-of-data. Either the previous pass ended prematurely "
                         f"(issue #43) or new data was published during collection — verify the night report.")
    logger.info(f"Server confirmed end of data for {stream}: {records_read} record(s) read")
