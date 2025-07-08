from unittest import mock

import debug_tools.debug_gmail as dg


def test_run_success():
    fake_service = mock.MagicMock()
    fake_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": ["INBOX"]
    }
    labels = dg.run(get_service=lambda: fake_service)
    assert labels == {"labels": ["INBOX"]}


def test_run_failure_returns_none():
    assert dg.run(get_service=lambda: None) is None
