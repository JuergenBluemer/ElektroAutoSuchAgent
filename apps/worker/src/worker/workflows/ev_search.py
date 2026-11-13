import os
from datetime import UTC, datetime
from email.message import EmailMessage

import aiosmtplib
import mistralai.workflows as workflows
from mistralai.client.models.textchunk import TextChunk
from mistralai.client.models.websearchtool import WebSearchTool
from mistralai.workflows.plugins.mistralai import Agent, Runner
from pydantic import BaseModel, Field

DEFAULT_QUERY = (
    "Gebrauchte Elektroautos ab Baujahr 2024 in Deutschland: Opel Corsa Electric, "
    "Peugeot e-208, Renault 5 E-Tech und Citroën ë-C3. Suche aktuelle Angebote, "
    "Preise, Preisentwicklungen und Marktlage für diese Modelle."
)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.1und1.de")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))


class EVSearchInput(BaseModel):
    query: str = Field(default=DEFAULT_QUERY)
    recipient: str | None = None
    dry_run: bool = False


class EVSearchOutput(BaseModel):
    report: str
    recipient: str | None = None
    sent: bool = False


async def run_web_research(query: str) -> str:
    agent = Agent(
        name="ev-news-researcher",
        model="mistral-medium-latest",
        instructions=(
            "Du bist ein Recherche-Assistent für Elektroautos. Suche im Web nach "
            "aktuellen (nicht älter als 14 Tage) gebrauchten Fahrzeugangeboten "
            "und Marktdaten zu den genannten Elektroauto-Modellen. Antworte auf "
            "Deutsch mit einer strukturierten Übersicht pro Modell: Preis, "
            "Baujahr/Kilometerstand der Angebote, Bezugsquelle und die "
            "Quellen-URL."
        ),
        tools=[WebSearchTool()],
    )
    result = await Runner.run(agent=agent, inputs=query, max_turns=10)
    return "\n\n".join(
        chunk.text for chunk in result if isinstance(chunk, TextChunk) and chunk.text
    )


@workflows.activity(name="research-ev-news")
async def research_ev_news(query: str) -> str:
    return await run_web_research(query)


def build_email_message(sender: str, recipient: str, report: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = (
        f"Elektroauto-Report – {datetime.now(UTC).strftime('%d.%m.%Y')}"
    )
    message.set_content(report)
    return message


@workflows.activity(name="send-report-email")
async def send_report_email(report: str, recipient: str | None) -> str:
    sender = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    to = recipient or os.environ["EV_REPORT_RECIPIENT"]
    message = build_email_message(sender, to, report)
    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=sender,
        password=password,
        start_tls=True,
    )
    return to


@workflows.workflow.define(
    name="ev-news-search",
    workflow_display_name="ElektroAuto Such-Agent",
    workflow_description=(
        "Recherchiert per Websuche aktuelle Elektroauto-News, Tests und Angebote "
        "und versendet das Ergebnis als E-Mail-Bericht."
    ),
)
class EVNewsSearchWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: EVSearchInput) -> EVSearchOutput:
        report = await research_ev_news(input.query)
        recipient = None
        sent = False
        if not input.dry_run:
            recipient = await send_report_email(report, input.recipient)
            sent = True
        return EVSearchOutput(report=report, recipient=recipient, sent=sent)
