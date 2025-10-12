#!/bin/bash

# Test the API Gateway endpoint
API_ENDPOINT="https://zyat7qafdb.execute-api.us-east-1.amazonaws.com"

echo "Testing API Gateway endpoint..."
echo "Endpoint: $API_ENDPOINT"
echo ""

# Send a test request (this will fail signature verification, but should get a response)
curl -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"type": 1}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -v

echo ""
echo "If you see a 401 error with 'Invalid request signature', the Lambda is working!"
echo "If you see a timeout or 502/503 error, there's a Lambda configuration issue."
