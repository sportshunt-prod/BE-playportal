import razorpay
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class RazorpayManager:
    """
    Manager class for Razorpay operations.
    Handles order creation and payment verification.
    """
    
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    def create_order(self, amount, order_id, notes=None):
        """
        Create a Razorpay order.
        
        Args:
            amount (int): Amount in paise (1 INR = 100 paise)
            order_id (str): Unique order ID from our Order model
            notes (dict): Additional metadata (tournament, category, team info)
        
        Returns:
            dict: Razorpay order response with 'id', 'amount', 'currency'
            
        Raises:
            Exception: If Razorpay API fails
        """
        try:
            order_payload = {
                'amount': amount,  # In paise
                'currency': 'INR',
                'receipt': order_id,
                'notes': notes or {}
            }
            
            order = self.client.order.create(data=order_payload)
            logger.info(f"Razorpay order created: {order['id']} for order_id: {order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {str(e)}")
            raise
    
    def verify_payment_signature(self, order_id, payment_id, signature):
        """
        Verify payment signature from Razorpay using SDK utility.
        
        Delegates to Razorpay SDK to ensure compatibility with upstream changes.
        Uses HMAC-SHA256 under the hood (single source of truth).
        
        Args:
            order_id (str): Razorpay order ID
            payment_id (str): Razorpay payment ID
            signature (str): Razorpay signature from frontend
        
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            # Use Razorpay SDK utility for verification (matches SDK version)
            is_valid = self.client.utility.verify_payment_signature(
                {
                    'razorpay_order_id': order_id,
                    'razorpay_payment_id': payment_id,
                    'razorpay_signature': signature
                }
            )
            
            if is_valid:
                logger.info(f"Payment signature verified")
            else:
                logger.warning(f"Invalid payment signature")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return False
    
    def verify_webhook_signature(self, webhook_body, webhook_signature):
        """
        Verify Razorpay webhook signature.
        
        Args:
            webhook_body (bytes): Raw webhook request body
            webhook_signature (str): Signature from X-Razorpay-Signature header
        
        Returns:
            bool: True if signature is valid
        """
        try:
            is_valid = self.client.utility.verify_webhook_signature(
                webhook_body,
                webhook_signature,
                settings.RAZORPAY_WEBHOOK_SECRET
            )
            return is_valid
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False


# Singleton instance
razorpay_manager = RazorpayManager()
