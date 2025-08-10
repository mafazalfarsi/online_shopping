# Thawani Pay Integration Setup Guide

This guide will help you set up Thawani Pay integration in your Django e-commerce website.

## Prerequisites

1. **Thawani Pay Account**: You need to register for a Thawani Pay merchant account at [Thawani Technologies](https://thawani.om/)
2. **Test Credentials**: Get your test API keys from the Thawani dashboard
3. **Python Environment**: Make sure you have Python 3.8+ installed

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Thawani Pay Credentials

Edit the `shop/thawani_service.py` file and replace the test credentials with your actual Thawani Pay credentials:

```python
# Replace these with your actual Thawani Pay credentials
self.secret_key = "your_actual_secret_key_here"
self.publishable_key = "your_actual_publishable_key_here"
```

### 3. Update Settings

The `BASE_URL` in `mysite/settings.py` is already configured for local development. For production, update it to your domain:

```python
BASE_URL = 'https://yourdomain.com'  # For production
```

## Configuration

### Test Environment

For testing, the integration uses Thawani's UAT (User Acceptance Testing) environment:

- **Base URL**: `https://uatcheckout.thawani.om/api/v1`
- **Test Cards**: Use the test card numbers provided by Thawani
- **Test Mode**: All transactions are simulated

### Production Environment

For production, you'll need to:

1. **Update Base URL**: Change to production URL in `thawani_service.py`
2. **Use Production Keys**: Replace test keys with production keys
3. **Configure Webhooks**: Set up webhook endpoints for payment notifications
4. **SSL Certificate**: Ensure your site has a valid SSL certificate

## How It Works

### 1. Payment Flow

1. **User selects Thawani Pay** on the payment page
2. **Customer information** is collected (name, phone, email, address)
3. **Checkout session** is created with Thawani Pay
4. **User is redirected** to Thawani's secure payment page
5. **Payment processing** happens on Thawani's servers
6. **Success/Cancel** redirects back to your site
7. **Order is created** in your database upon successful payment

### 2. API Endpoints

- `POST /thawani/create-session/` - Creates a payment session
- `GET /thawani/success/` - Handles successful payments
- `GET /thawani/cancel/` - Handles cancelled payments
- `POST /thawani/webhook/` - Receives payment notifications (production)

### 3. Database Integration

The integration automatically:
- Creates orders in your database
- Stores payment method as "Thawani Pay"
- Handles order items and totals
- Manages session data

## Testing

### 1. Test the Integration

1. Add items to your cart
2. Go to checkout
3. Select "Thawani Pay" as payment method
4. Fill in customer information
5. Click "Place Order"
6. You'll be redirected to Thawani's test payment page

### 2. Test Cards

Use these test card numbers provided by Thawani:
- **Visa**: 4111 1111 1111 1111
- **Mastercard**: 5555 5555 5555 4444
- **Expiry**: Any future date
- **CVV**: Any 3 digits

### 3. Test Scenarios

- **Successful Payment**: Complete payment with valid test card
- **Failed Payment**: Use invalid card details
- **Cancelled Payment**: Cancel payment on Thawani's page
- **Network Error**: Test with poor internet connection

## Security Considerations

### 1. API Key Security

- Never commit API keys to version control
- Use environment variables for production
- Rotate keys regularly
- Monitor API usage

### 2. Webhook Security

- Verify webhook signatures
- Use HTTPS in production
- Validate webhook data
- Handle webhook failures gracefully

### 3. Data Protection

- Encrypt sensitive customer data
- Follow GDPR compliance
- Implement proper session management
- Use HTTPS for all communications

## Troubleshooting

### Common Issues

1. **"Invalid API Key" Error**
   - Check your API credentials
   - Ensure you're using the correct environment (test/production)

2. **"Session Creation Failed"**
   - Verify your BASE_URL setting
   - Check network connectivity
   - Validate request payload

3. **"Payment Verification Failed"**
   - Check session ID validity
   - Verify webhook configuration
   - Review payment status

### Debug Mode

Enable debug logging by adding to `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'shop.thawani_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Production Deployment

### 1. Environment Variables

Set these environment variables:

```bash
export THAWANI_SECRET_KEY="your_production_secret_key"
export THAWANI_PUBLISHABLE_KEY="your_production_publishable_key"
export BASE_URL="https://yourdomain.com"
```

### 2. Webhook Configuration

In your Thawani dashboard, configure webhooks:

- **URL**: `https://yourdomain.com/thawani/webhook/`
- **Events**: `checkout.session.completed`, `checkout.session.expired`

### 3. SSL Certificate

Ensure your domain has a valid SSL certificate for secure payment processing.

## Support

For issues with:
- **Thawani Pay API**: Contact Thawani Technologies support
- **Integration Code**: Check the code comments and this guide
- **Django Setup**: Refer to Django documentation

## API Documentation

For detailed API documentation, visit:
[Thawani E-commerce API Documentation](https://thawani-technologies.stoplight.io/docs/thawani-ecommerce-api/5534c91789a48-thawani-e-commerce-api)

## License

This integration is provided as-is for educational and development purposes. For production use, ensure compliance with Thawani Pay's terms of service and local regulations. 