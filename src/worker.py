"""
Lambda handler for SQS worker
Imports from channelwright module
"""
from channelwright.worker import lambda_handler

# Export for Lambda
__all__ = ['lambda_handler']
