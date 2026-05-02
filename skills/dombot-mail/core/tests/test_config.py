from dombot_mail.config import MailSettings


def test_mail_settings_from_env_minimal(monkeypatch):
    monkeypatch.setenv("DOMBOT_MAIL_IMAP_HOST", "imap.test.com")
    monkeypatch.setenv("DOMBOT_MAIL_SMTP_HOST", "smtp.test.com")
    monkeypatch.setenv("DOMBOT_MAIL_USER", "user@test.com")
    monkeypatch.setenv("DOMBOT_MAIL_PASSWORD", "secret")

    settings = MailSettings.from_env()

    assert settings.imap_host == "imap.test.com"
    assert settings.smtp_host == "smtp.test.com"
    assert settings.user == "user@test.com"
    assert settings.password == "secret"
