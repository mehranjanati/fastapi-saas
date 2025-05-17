# FastAPI and n8n Integration Guide

This document explains how to integrate n8n workflows with your FastAPI application for advanced workflow automation.

## Overview

n8n is a workflow automation tool that allows you to connect various services and automate tasks without writing code. Our integration provides bidirectional communication between your FastAPI application and n8n:

1. **FastAPI → n8n**: Trigger workflows from your API
2. **n8n → FastAPI**: Receive data from n8n workflows via webhooks

## Setup

### Requirements

- FastAPI application
- n8n instance (self-hosted or cloud)
- Network connectivity between services

### Environment Variables

Configure these environment variables:

```
N8N_BASE_URL=http://localhost:5678  # URL of your n8n instance
N8N_API_KEY=your_api_key            # Optional API key for n8n
```

## Using the Integration

### Triggering Workflows from FastAPI

Use the workflow integration to trigger n8n workflows:

```python
from workflow_integration import trigger_workflow

# Somewhere in your API endpoint
result = await trigger_workflow(
    workflow_id="your-workflow-id", 
    data={"order_id": "12345", "status": "completed"}
)
```

### Creating Webhook Endpoints

The integration provides pre-configured webhook endpoints for n8n to call:

1. **General Webhook**: `/workflow/webhook` - Receives webhook data with event type and payload
2. **Tagged Webhooks**: `/workflow/webhook/{workflow_tag}` - Routes webhooks based on tags

## Workflow Templates

We provide several n8n workflow templates to get you started:

### Order Processing

This workflow handles order processing and sends notifications to customers:

1. Import the template from `n8n_templates/order_processing_workflow.json`
2. Configure the webhook node to connect to your FastAPI application
3. Adjust environment variables for your specific deployment

### Notification Workflow

A workflow to send notifications via multiple channels:

1. Import from `n8n_templates/notification_workflow.json`
2. Configure notification channels (email, SMS, etc.)
3. Connect to your FastAPI application via webhooks

## Security Considerations

### Authentication

For production environments, implement proper authentication:

1. Enable API key for n8n webhooks
2. Add JWT validation for webhook endpoints
3. Implement signature verification for n8n requests

### Environment Configuration

For production:
1. Use HTTPS for all communications
2. Restrict IP access to n8n if possible
3. Use environment-specific credentials

## Testing

Test the integration using the provided test script:

```bash
python test_n8n_integration.py --api-url http://localhost:8000 --workflow-id your-workflow-id
```

Options:
- `--test-type`: Choose "trigger", "webhook", or "all"
- `--count`: Number of test iterations to run

## Troubleshooting

Common issues:

1. **Connection Errors**: Check network connectivity between FastAPI and n8n
2. **Authentication Failures**: Verify API keys and credentials
3. **Workflow Not Found**: Double-check workflow IDs and ensure workflows are active

## Advanced Usage

### Custom Workflow Logic

Implement custom workflow logic by extending the `workflow_integration.py` module:

```python
# Add to workflow_integration.py
async def process_custom_workflow(data: Dict[str, Any]):
    # Your custom processing logic
    return {"status": "processed", "data": processed_data}
```

### Error Handling

To improve error handling for workflow operations:

1. Implement retry mechanisms for failed workflows
2. Create error queues for failed operations
3. Set up monitoring for workflow execution

### Scaling Considerations

For high-volume applications:

1. Implement rate limiting for workflow triggers
2. Use background tasks for asynchronous workflow operations
3. Consider webhook batching for high-frequency events 