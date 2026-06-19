"""Delivery layer: always write a digest file; optionally push by email."""

import datetime
import os
import pathlib
import smtplib
from email.mime.text import MIMEText


def deliver(digest_md, out_dir="digests"):
    path = pathlib.Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    fname = path / f"digest-{datetime.date.today().isoformat()}.md"
    fname.write_text(digest_md, encoding="utf-8")

    if os.getenv("SMTP_HOST") and os.getenv("DIGEST_TO"):
        try:
            _send_email(digest_md)
        except Exception as exc:  # don't let email failure break the run
            print(f"[notify] email push failed: {exc}")
    return str(fname)


def _send_email(digest_md):
    msg = MIMEText(digest_md, "plain", "utf-8")
    msg["Subject"] = f"AI Research Digest — {datetime.date.today().isoformat()}"
    msg["From"] = os.environ.get("SMTP_FROM", os.environ["DIGEST_TO"])
    msg["To"] = os.environ["DIGEST_TO"]

    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        if os.getenv("SMTP_USER"):
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        server.send_message(msg)
