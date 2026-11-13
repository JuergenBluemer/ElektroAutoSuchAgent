# ElektroAutoSuchAgent

Ein Mistral-Workflow-Worker, der regelmäßig per Websuche nach aktuellen Elektroauto-News, Tests und Angeboten recherchiert und das Ergebnis als E-Mail-Bericht versendet.

## Workflow

`ev-news-search` (Anzeigename: *ElektroAuto Such-Agent*)

1. **research-ev-news** – ein Mistral-Agent mit aktiviertem `web_search` recherchiert aktuelle (max. 14 Tage alte) Nachrichten, Tests und Angebote zu Elektroautos in Deutschland.
2. **send-report-email** – versendet die Zusammenfassung per SMTP (IONOS, `smtp.1und1.de`) als E-Mail.

Eingabe (optional konfigurierbar):

```json
{
  "query": "Gebrauchte Elektroautos ab Baujahr 2024: Opel Corsa Electric, Peugeot e-208, Renault 5 E-Tech, Citroën ë-C3",
  "recipient": null,
  "dry_run": false
}
```

- `query` – Suchbegriff/-thema für die Recherche
- `recipient` – abweichende Empfängeradresse; `null` verwendet die Umgebungsvariable `EV_REPORT_RECIPIENT`
- `dry_run` – wenn `true`, wird nur recherchiert und der Bericht als Ergebnis zurückgegeben, ohne E-Mail zu versenden

## Umgebungsvariablen (Workspace-Secrets im Deployment)

| Variable | Bedeutung |
|---|---|
| `SMTP_USERNAME` | IONOS-E-Mail-Adresse (Absender) |
| `SMTP_PASSWORD` | SMTP-Passwort |
| `EV_REPORT_RECIPIENT` | Standard-Empfänger des Berichts |
| `SMTP_HOST` | optional, Standard `smtp.1und1.de` |
| `SMTP_PORT` | optional, Standard `587` |

## Lokale Entwicklung

```bash
uv sync
uv run pytest
uv run python -m worker.entrypoints.worker
```

## Deployment

Managed Deployment mit Dockerfile `deploy/docker/Dockerfile.worker` und Build-Kontext im Repository-Root. Der Zeitplan (2× pro Woche) wird als Workflow-Schedule in Mistral Studio eingerichtet.
