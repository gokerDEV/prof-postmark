"""
FastAPI application for Prof. Postmark.

Clean, focused API with proper error handling and security.
"""

import logging
from fastapi import FastAPI, HTTPException, Request, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional

from ..core.configuration import config
from .webhook_handler import WebhookHandler


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Prof. Postmark",
    description="Async Email Feedback System with AI Analysis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize webhook handler
webhook_handler = WebhookHandler()


def verify_webhook_token(token: Optional[str] = Query(None)) -> str:
    """
    Verify webhook authentication token.
    
    Args:
        token: Token from query parameter
        
    Returns:
        str: Verified token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not token or token != config.security.WEBHOOK_SECRET_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing webhook token"
        )
    return token


@app.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "message": "Prof. Postmark is running!",
        "status": "healthy",
        "version": "2.0.0"
    }


@app.get("/health")
async def detailed_health_check():
    """Detailed health check with system information."""
    return {
        "status": "healthy",
        "service": "Prof. Postmark",
        "version": "2.0.0",
        "ai_model": config.ai_service.VISION_MODEL_NAME,
        "features": [
            "email_parsing",
            "ai_analysis", 
            "image_processing",
            "webhook_security",
            "personalized_responses"
        ]
    }


@app.post("/webhook")
async def process_email_webhook(
    request: Request,
    token: str = Depends(verify_webhook_token)
):
    """
    Process incoming email webhooks from Postmark.
    
    Complete Email-to-AI-to-Email Workflow:
    1. Security validation (webhook token)
    2. Email parsing and cleaning
    3. PING/PONG health check handling
    4. Attachment validation (size, type)
    5. AI analysis (GPT-4o with vision)
    6. Personalized email response
    
    Security: Requires valid token parameter for authentication.
    Usage: POST /webhook?token=your-secret-token
    """
    try:
        # Parse webhook data
        webhook_data = await request.json()
        logger.info(f"📧 Received webhook from: {webhook_data.get('From', 'unknown')}")
        
        # Process through webhook handler
        result = await webhook_handler.process_webhook(webhook_data)
        
        # Return appropriate response
        if result["status"] == "success":
            return JSONResponse(content=result, status_code=200)
        elif result["status"] == "partial_success":
            return JSONResponse(content=result, status_code=202)  # Accepted
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"💥 Webhook endpoint error: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Webhook processing failed: {str(e)}"
            },
            status_code=500
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"💥 Unhandled exception: {str(exc)}")
    return JSONResponse(
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "detail": str(exc)
        },
        status_code=500
    ) 