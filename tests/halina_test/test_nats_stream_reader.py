import datetime
import unittest
from contextlib import aclosing
from unittest.mock import patch

from serverish.base import MessengerReaderStopped

from halina.nats_stream_reader import read_all_records


class FakeReader:
    """Mimics serverish MsgReader: yields queued records, then reports end-of-data."""

    def __init__(self, records):
        self._records = list(records)
        self.last_seq = None
        self.opened = False
        self.closed = False

    async def open(self):
        self.opened = True

    async def close(self):
        self.closed = True

    async def read_next(self):
        if not self._records:
            raise MessengerReaderStopped
        data, meta = self._records.pop(0)
        self.last_seq = meta['nats']['seq']
        return data, meta


def _record(seq: int):
    return {"value": seq}, {"nats": {"seq": seq}}


class TestReadAllRecords(unittest.IsolatedAsyncioTestCase):
    _START = datetime.datetime(2026, 7, 22, 16, 0, tzinfo=datetime.timezone.utc)

    @patch('halina.nats_stream_reader.get_reader')
    async def test_yields_all_records_and_probes_stream_again(self, mock_get_reader):
        readers = [FakeReader([_record(1), _record(2)]), FakeReader([])]
        mock_get_reader.side_effect = readers

        collected = [data async for data, meta in read_all_records("test.stream", self._START)]

        self.assertEqual(collected, [{"value": 1}, {"value": 2}])
        self.assertTrue(all(r.opened and r.closed for r in readers))
        # main pass by start time, verification pass continues by sequence
        self.assertEqual(mock_get_reader.call_args_list[0].kwargs['deliver_policy'], 'by_start_time')
        self.assertEqual(mock_get_reader.call_args_list[0].kwargs['opt_start_time'], self._START)
        self.assertEqual(mock_get_reader.call_args_list[1].kwargs['deliver_policy'], 'by_start_sequence')
        self.assertEqual(mock_get_reader.call_args_list[1].kwargs['opt_start_seq'], 3)
        for call in mock_get_reader.call_args_list:
            self.assertTrue(call.kwargs['nowait'])

    @patch('halina.nats_stream_reader.get_reader')
    async def test_verification_pass_detects_premature_end(self, mock_get_reader):
        # server reported end-of-data after seq 1, but the verification pass still finds seq 2
        mock_get_reader.side_effect = [FakeReader([_record(1)]), FakeReader([_record(2)])]

        with self.assertLogs('nats_stream_reader', level='ERROR') as logs:
            collected = [data async for data, meta in read_all_records("test.stream", self._START)]

        # the late record is reported but not lost
        self.assertEqual(collected, [{"value": 1}, {"value": 2}])
        self.assertTrue(any("Verification pass" in message for message in logs.output))

    @patch('halina.nats_stream_reader.get_reader')
    async def test_no_error_logged_when_verification_pass_is_empty(self, mock_get_reader):
        mock_get_reader.side_effect = [FakeReader([_record(1)]), FakeReader([])]

        with self.assertNoLogs('nats_stream_reader', level='ERROR'):
            _ = [data async for data, meta in read_all_records("test.stream", self._START)]

    @patch('halina.nats_stream_reader.get_reader')
    async def test_empty_stream_verifies_from_start_time(self, mock_get_reader):
        readers = [FakeReader([]), FakeReader([])]
        mock_get_reader.side_effect = readers

        collected = [data async for data, meta in read_all_records("test.stream", self._START)]

        self.assertEqual(collected, [])
        # nothing was read, so the verification pass restarts from the same start time
        for call in mock_get_reader.call_args_list:
            self.assertEqual(call.kwargs['deliver_policy'], 'by_start_time')

    @patch('halina.nats_stream_reader.get_reader')
    async def test_early_break_skips_verification_and_closes_reader(self, mock_get_reader):
        reader = FakeReader([_record(1), _record(2)])
        mock_get_reader.side_effect = [reader]

        async with aclosing(read_all_records("test.stream", self._START)) as records:
            async for data, meta in records:
                break  # consumer decides the night is over

        self.assertTrue(reader.closed)
        self.assertEqual(mock_get_reader.call_count, 1, "verification pass must not run after an early break")


if __name__ == '__main__':
    unittest.main()
