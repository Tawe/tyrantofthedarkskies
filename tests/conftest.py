"""Pytest fixtures for MUD server tests (optional; tests also run with unittest)."""

import pytest

from tests.test_helpers import (
    MockPlayer,
    MockRoom,
    MockGame,
    MockRuntimeState,
    make_mock_items,
    make_runtime_with_corpse,
)


@pytest.fixture
def mock_player():
    return MockPlayer()


@pytest.fixture
def mock_room():
    return MockRoom()


@pytest.fixture
def mock_items():
    return make_mock_items()


@pytest.fixture
def mock_game(mock_room, mock_items):
    return MockGame(rooms={"room_1": mock_room}, items=mock_items)


@pytest.fixture
def mock_runtime_with_corpse(mock_room):
    return make_runtime_with_corpse(mock_room.room_id)
