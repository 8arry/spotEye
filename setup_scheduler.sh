#!/bin/bash
# Setup Cloud Scheduler for SpotEye monitoring

# Configuration
PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_URL="https://spoteye-monitor-your-hash-uc.a.run.app"
SCHEDULE="*/3 * * * *"  # Every 3 minutes
JOB_NAME="spoteye-monitoring-trigger"

echo "Setting up Cloud Scheduler for SpotEye monitoring..."

# Create the Cloud Scheduler job
gcloud scheduler jobs create http $JOB_NAME \
    --schedule="$SCHEDULE" \
    --uri="$SERVICE_URL/monitor" \
    --http-method=POST \
    --location=$REGION \
    --description="Trigger SpotEye apartment monitoring every 3 minutes"

echo "Cloud Scheduler job '$JOB_NAME' created successfully!"
echo "Schedule: $SCHEDULE (every 3 minutes)"
echo "Target URL: $SERVICE_URL/monitor"
echo ""
echo "To run immediately for testing:"
echo "gcloud scheduler jobs run $JOB_NAME --location=$REGION"
echo ""
echo "To view job status:"
echo "gcloud scheduler jobs describe $JOB_NAME --location=$REGION"
