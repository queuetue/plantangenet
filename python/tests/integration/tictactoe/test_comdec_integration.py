"""
Integration tests for comdec (output/codec) system in TicTacToe.
"""
import os
import json
import tempfile
from io import StringIO
from unittest.mock import Mock
import pytest
from plantangenet.comdec.comdec import SnapshotterComdec, LoggerComdec, StreamingComdec
from examples.tictactoe.stats import TicTacToeStats


class TestComdecIntegration:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.skip(reason="Legacy tictactoe integration test - skipping as requested.")
    @pytest.mark.asyncio
    async def test_snapshot_comdec(self):
        stats = TicTacToeStats()
        snapshot_file = os.path.join(self.temp_dir, "snapshot.json")
        snapshot_comdec = SnapshotterComdec(
            filepath=snapshot_file, format="json")
        stats.add_comdec(snapshot_comdec)
        stats.record_game_result("alice", "bob", "alice")
        stats.record_game_result("bob", "alice", "bob")
        await stats.output_all()
        assert os.path.exists(snapshot_file)
        with open(snapshot_file, 'r') as f:
            data = json.load(f)
            assert "stats" in data
            assert "total_games" in data["stats"]
            assert data["stats"]["total_games"] == 2

    @pytest.mark.skip(reason="Legacy tictactoe integration test - skipping as requested.")
    @pytest.mark.asyncio
    async def test_logger_comdec(self):
        stats = TicTacToeStats()
        log_stream = StringIO()
        logger_comdec = LoggerComdec(log_stream=log_stream)
        stats.add_comdec(logger_comdec)
        stats.record_game_result("alice", "bob", "alice")
        await stats.output_all()
        log_output = log_stream.getvalue()
        assert "stats" in log_output.lower()
        assert "total_games" in log_output.lower()

    @pytest.mark.skip(reason="Legacy tictactoe integration test - skipping as requested.")
    @pytest.mark.asyncio
    async def test_streaming_comdec(self):
        stats = TicTacToeStats()
        mock_stream = Mock()
        streaming_comdec = StreamingComdec(stream_handler=mock_stream)
        stats.add_comdec(streaming_comdec)
        stats.record_game_result("alice", "bob", "alice")
        await stats.output_all()
        mock_stream.assert_called()

    @pytest.mark.skip(reason="Multiple comdecs integration not implemented in current codebase")
    @pytest.mark.asyncio
    async def test_multiple_comdecs(self):
        stats = TicTacToeStats()
        snapshot_file = os.path.join(self.temp_dir, "multi_snapshot.json")
        snapshot_comdec = SnapshotterComdec(filepath=snapshot_file)
        log_stream = StringIO()
        logger_comdec = LoggerComdec(log_stream=log_stream)
        mock_stream = Mock()
        streaming_comdec = StreamingComdec(stream_handler=mock_stream)
        stats.add_comdec(snapshot_comdec)
        stats.add_comdec(logger_comdec)
        stats.add_comdec(streaming_comdec)
        stats.record_game_result("alice", "bob", "alice")
        await stats.output_all()
        assert os.path.exists(snapshot_file)
        assert len(log_stream.getvalue()) > 0
        mock_stream.assert_called()
