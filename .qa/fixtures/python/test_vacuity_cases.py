"""Fixtures for the G3 self-test. Each function is labelled with the finding it
must produce. If G3 stops flagging one of these, G3 has regressed."""
import pytest
from unittest.mock import Mock


def test_no_assertion_at_all():          # expect: NO_ASSERTION
    result = 2 + 2
    print(result)


def test_only_mock_assertions():         # expect: MOCK_ONLY
    m = Mock()
    m.save()
    m.save.assert_called_once()


def test_tautology():                    # expect: TAUTOLOGY
    x = compute()
    assert x == x


@pytest.mark.skip(reason="flaky")
def test_skipped():                      # expect: SKIPPED (and NO_ASSERTION)
    pass


def test_genuinely_fine():               # expect: no finding
    assert compute() == 4


def compute():
    return 4
