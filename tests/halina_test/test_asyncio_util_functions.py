import asyncio
import unittest

from halina.asyncio_util_functions import gather_with_hard_deadline


class TestGatherWithHardDeadline(unittest.IsolatedAsyncioTestCase):

    async def test_returns_true_when_all_finish_in_time(self):
        async def quick():
            await asyncio.sleep(0)

        result = await gather_with_hard_deadline([quick(), quick()], timeout=1)
        self.assertTrue(result)

    async def test_cancels_hanging_task_and_returns_false(self):
        cancelled = asyncio.Event()

        async def hanging():
            try:
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        result = await gather_with_hard_deadline([hanging()], timeout=0.05, grace=1)
        self.assertFalse(result)
        self.assertTrue(cancelled.is_set(), "hanging task should have been cancelled")

    async def test_returns_even_when_task_ignores_cancellation(self):
        release = asyncio.Event()

        async def unkillable():
            try:
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                pass  # swallow the cancellation — simulates the lost-cancel hang from issue #43
            await release.wait()

        with self.assertLogs('asyncio_util_functions', level='ERROR') as logs:
            result = await gather_with_hard_deadline([unkillable()], timeout=0.05, grace=0.05,
                                                     what="Test collection")
        self.assertFalse(result)
        self.assertTrue(any("ignored cancellation" in message for message in logs.output))
        release.set()  # let the abandoned task finish so the test loop closes cleanly
        await asyncio.sleep(0.01)


if __name__ == '__main__':
    unittest.main()
