#!/usr/bin/env python3
"""
SpotEye Cloud Service - Web interface for Cloud Run deployment
Handles HTTP triggers from Cloud Scheduler for apartment monitoring
"""

import json
import logging
import os
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Import our monitoring system
from main import SpotEyeMonitor
from config import get_config

# Initialize FastAPI app
app = FastAPI(
    title="SpotEye Apartment Monitor",
    description="24/7 automated monitoring system for W|27 German student apartments",
    version="1.0.0"
)

# Configure logging for cloud environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.get("/")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        'status': 'healthy',
        'service': 'SpotEye Apartment Monitor',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }

@app.post("/monitor")
@app.get("/monitor")
async def trigger_monitoring(request: Request):
    """Main monitoring endpoint - triggered by Cloud Scheduler"""
    try:
        logger.info("=== SpotEye monitoring triggered ===")
        
        # Check for Cloud Scheduler headers
        scheduler_job = request.headers.get('X-CloudScheduler-JobName')
        if scheduler_job:
            logger.info(f"Triggered by Cloud Scheduler job: {scheduler_job}")
        
        # Initialize and run monitoring
        monitor = SpotEyeMonitor()
        monitor.run_once()
        
        # Get current statistics
        historical_data = monitor.storage.load_historical_data()
        apartments = historical_data.get('apartments', [])
        stats = monitor.storage.get_statistics(apartments)
        
        response_data = {
            'status': 'success',
            'message': 'Monitoring completed successfully',
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_apartments': stats['total'],
                'by_status': stats['by_status'],
                'last_check': historical_data.get('last_check', 'Never')
            }
        }
        
        logger.info(f"Monitoring completed - Total: {stats['total']}, "
                   f"Available: {stats['by_status'].get('available', 0)}, "
                   f"Soon: {stats['by_status'].get('soon', 0)}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Monitoring failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': f'Monitoring failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        )

@app.get("/status")
async def get_status():
    """Get current system status"""
    try:
        # Initialize monitor (but don't run)
        monitor = SpotEyeMonitor()
        
        # Load current data
        historical_data = monitor.storage.load_historical_data()
        apartments = historical_data.get('apartments', [])
        
        if apartments:
            stats = monitor.storage.get_statistics(apartments)
            
            # Filter for soon/available apartments
            soon_available = [
                apt for apt in apartments 
                if apt.get('availability') in ['soon', 'available']
            ]
            
            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'statistics': {
                    'total_apartments': stats['total'],
                    'by_status': stats['by_status'],
                    'by_type': stats['by_type'],
                    'price_stats': stats['price_stats'],
                    'last_check': historical_data.get('last_check', 'Never')
                },
                'soon_available': soon_available
            }
        else:
            return {
                'status': 'success',
                'message': 'No apartment data available yet',
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': f'Status check failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        )

@app.post("/test-email")
async def test_email():
    """Test email notification system"""
    try:
        monitor = SpotEyeMonitor()
        success = monitor.test_email()
        
        return {
            'status': 'success' if success else 'failed',
            'message': 'Email test completed',
            'result': success,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Email test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': f'Email test failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        )

if __name__ == '__main__':
    import uvicorn
    # For local development
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host='0.0.0.0', port=port) 