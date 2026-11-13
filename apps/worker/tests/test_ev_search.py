import pytest

from worker.workflows.ev_search import (
    EVSearchInput,
    build_email_message,
    send_report_email,
)


def test_build_email_message_contains_report_and_recipient():
    message = build_email_message(
        "absender@example.com", "empfaenger@example.com", "Mein Bericht"
    )
    assert message["From"] == "absender@example.com"
    assert message["To"] == "empfaenger@example.com"
    assert "Elektroauto-Report" in message["Subject"]
    assert "Mein Bericht" in message.get_content()


def test_default_input_query():
    assert "Opel Corsa Electric" in EVSearchInput().query
    assert "Baujahr 2024" in EVSearchInput().query


async def test_send_report_email_uses_env_recipient_and_smtp(
    monkeypatch: pytest.MonkeyPatch,
):
    sent = {}

    async def fake_send(message, **kwargs):
        sent["message"] = message
        sent["kwargs"] = kwargs
        return None

    monkeypatch.setattr("aiosmtplib.send", fake_send)
    monkeypatch.setenv("SMTP_USERNAME", "absender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "geheim")
    monkeypatch.setenv("EV_REPORT_RECIPIENT", "empfaenger@example.com")

    recipient = await send_report_email("Bericht", None)

    assert recipient == "empfaenger@example.com"
    assert sent["message"]["To"] == "empfaenger@example.com"
    assert sent["kwargs"]["hostname"] == "smtp.1und1.de"
    assert sent["kwargs"]["start_tls"] is True
    assert sent["kwargs"]["username"] == "absender@example.com"
