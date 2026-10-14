# spotEye

A small 24/7 monitoring service that watches a student-apartment booking page and sends an
email as soon as an apartment's availability changes.

## How it works

1. **Scrape** – a headless Chrome (Selenium) loads the booking page and extracts apartment entries.
2. **Detect changes** – current results are compared with the stored history (JSON) to find new,
   removed or status-changed apartments.
3. **Notify** – changes are sent as an HTML email via SMTP, with available/soon apartments highlighted.
4. **Run continuously** – a FastAPI service runs the check in a background asyncio task every few
   minutes, packaged with Docker and deployed to Google Cloud Run via Cloud Build.

```
scraper.py        Selenium scraper
storage.py        history storage + change detection
notification.py   HTML email notifications
main.py           SpotEyeMonitor orchestration (run once / continuous / test email)
cloud_service.py  FastAPI service with background monitoring loop
cloudbuild.yaml   build → push → deploy to Cloud Run
```

## Run locally

```bash
pip install -r requirements.txt
export SMTP_USER=... SMTP_PASSWORD=... RECIPIENT_EMAIL=...
python main.py --once         # single check
python main.py --continuous   # keep monitoring
python main.py --test-email   # send a test notification
python main.py --status       # show stored data and status
```

## Deploy

```bash
gcloud builds submit --config cloudbuild.yaml
```

Set `ENABLE_CONTINUOUS_MONITORING=true` on the Cloud Run service to start the background loop.

## Tech

Python · Selenium · FastAPI · asyncio · Docker · Google Cloud Run · Cloud Build
