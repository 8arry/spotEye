#!/usr/bin/env python3
"""
SpotEye Cloud Service - 24/7 Continuous Monitoring
Runs continuous apartment monitoring as a background service
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Import our monitoring system
from main import SpotEyeMonitor
from config import get_config

# Global variables for managing the monitoring task
monitor_instance = None
monitoring_task = None
is_monitoring_active = False

# Configure logging for cloud environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def continuous_monitoring():
    """Background task for continuous apartment monitoring"""
    global monitor_instance, is_monitoring_active
    
    logger.info("Starting 24/7 continuous monitoring...")
    
    # Initialize monitor instance
    monitor_instance = SpotEyeMonitor()
    config = get_config()
    interval_minutes = config['monitoring']['check_interval']
    interval_seconds = interval_minutes * 60
    
    is_monitoring_active = True
    
    while is_monitoring_active:
        try:
            logger.info("=== Running apartment monitoring check ===")
            monitor_instance.run_once()
            logger.info(f"Monitoring check completed. Next check in {interval_minutes} minutes.")
            
            # Wait for next check using asyncio.sleep (non-blocking)
            await asyncio.sleep(interval_seconds)
            
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
            logger.info(f"Retrying in {interval_minutes} minutes...")
            await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to handle startup and shutdown"""
    global monitoring_task
    
    # Startup: Start the continuous monitoring task
    logger.info("SpotEye service starting up...")
    monitoring_task = asyncio.create_task(continuous_monitoring())
    
    yield
    
    # Shutdown: Stop the monitoring task
    logger.info("SpotEye service shutting down...")
    global is_monitoring_active
    is_monitoring_active = False
    if monitoring_task:
        monitoring_task.cancel()
        try:
            await monitoring_task
        except asyncio.CancelledError:
            pass


# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="SpotEye Apartment Monitor",
    description="24/7 continuous monitoring system for W|27 German student apartments",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def health_check():
    """Health check endpoint for Cloud Run"""
    global is_monitoring_active, monitor_instance
    
    status = "active" if is_monitoring_active else "inactive"
    
    return {
        'status': 'healthy',
        'service': 'SpotEye Apartment Monitor',
        'monitoring_status': status,
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'mode': '24/7 Continuous Monitoring'
    }


@app.post("/monitor")
@app.get("/monitor")
async def trigger_manual_monitoring(request: Request):
    """Manual monitoring trigger endpoint (for testing purposes)"""
    global monitor_instance
    
    try:
        logger.info("=== Manual monitoring trigger ===")
        
        # Use existing monitor instance or create new one
        if not monitor_instance:
            monitor_instance = SpotEyeMonitor()
        
        monitor_instance.run_once()
        
        # Get current statistics
        historical_data = monitor_instance.storage.load_historical_data()
        apartments = historical_data.get('apartments', [])
        stats = monitor_instance.storage.get_statistics(apartments)
        
        response_data = {
            'status': 'success',
            'message': 'Manual monitoring completed successfully',
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_apartments': stats['total'],
                'by_status': stats['by_status'],
                'last_check': historical_data.get('last_check', 'Never')
            }
        }
        
        logger.info(f"Manual monitoring completed - Total: {stats['total']}, "
                   f"Available: {stats['by_status'].get('available', 0)}, "
                   f"Soon: {stats['by_status'].get('soon', 0)}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Manual monitoring failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': f'Manual monitoring failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        )


@app.get("/status")
async def get_status():
    """Get current system status and apartment data"""
    global is_monitoring_active, monitor_instance
    
    try:
        # Use existing monitor instance or create new one
        if not monitor_instance:
            monitor_instance = SpotEyeMonitor()
        
        # Load current data
        historical_data = monitor_instance.storage.load_historical_data()
        apartments = historical_data.get('apartments', [])
        
        config = get_config()
        interval_minutes = config['monitoring']['check_interval']
        
        if apartments:
            stats = monitor_instance.storage.get_statistics(apartments)
            
            # Filter for soon/available apartments
            soon_available = [
                apt for apt in apartments 
                if apt.get('availability') in ['soon', 'available']
            ]
            
            return {
                'status': 'success',
                'monitoring_status': 'active' if is_monitoring_active else 'inactive',
                'monitoring_interval_minutes': interval_minutes,
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
                'monitoring_status': 'active' if is_monitoring_active else 'inactive',
                'monitoring_interval_minutes': interval_minutes,
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
    global monitor_instance
    
    try:
        if not monitor_instance:
            monitor_instance = SpotEyeMonitor()
            
        success = monitor_instance.test_email()
        
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