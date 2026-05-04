"""
Payment Orchestrator - Centralized Payment Processing

Handles multiple payment providers (Stripe, OPay, PayPal, Flutterwave)
with unified interface and webhook handling.
"""

import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import stripe
import requests
from flask import request, jsonify, current_app


class PaymentProvider(Enum):
    STRIPE = "stripe"
    OPAY = "opay"
    PAYPAL = "paypal"
    FLUTTERWAVE = "flutterwave"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


@dataclass
class PaymentResult:
    success: bool
    transaction_id: Optional[str] = None
    reference: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    message: str = ""
    data: Optional[Dict[str, Any]] = None


class PaymentOrchestrator:
    """Central payment orchestrator for all payment providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._init_providers()
    
    def _init_providers(self):
        """Initialize payment providers"""
        # Initialize Stripe
        if self.config.get('stripe', {}).get('enabled'):
            stripe.api_key = self.config['stripe']['secret_key']
        
        # OPay configuration
        self.opay_config = self.config.get('opay', {})
        
        # PayPal configuration
        self.paypal_config = self.config.get('paypal', {})
        
        # Flutterwave configuration
        self.flutterwave_config = self.config.get('flutterwave', {})
    
    def create_payment(
        self,
        provider: PaymentProvider,
        amount: float,
        currency: str,
        metadata: Dict[str, Any],
        customer_email: str,
        return_url: str
    ) -> PaymentResult:
        """Create a payment intent with the specified provider"""
        
        if provider == PaymentProvider.STRIPE:
            return self._create_stripe_payment(amount, currency, metadata, customer_email, return_url)
        elif provider == PaymentProvider.OPAY:
            return self._create_opay_payment(amount, currency, metadata, customer_email, return_url)
        elif provider == PaymentProvider.PAYPAL:
            return self._create_paypal_payment(amount, currency, metadata, customer_email, return_url)
        elif provider == PaymentProvider.FLUTTERWAVE:
            return self._create_flutterwave_payment(amount, currency, metadata, customer_email, return_url)
        else:
            return PaymentResult(success=False, message=f"Unknown provider: {provider}")
    
    def _create_stripe_payment(
        self,
        amount: float,
        currency: str,
        metadata: Dict[str, Any],
        customer_email: str,
        return_url: str
    ) -> PaymentResult:
        """Create Stripe payment intent"""
        try:
            # Create or get customer
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(
                    email=customer_email,
                    metadata=metadata
                )
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                customer=customer.id,
                metadata=metadata,
                receipt_email=customer_email,
                return_url=return_url,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "always"
                }
            )
            
            return PaymentResult(
                success=True,
                transaction_id=intent.id,
                reference=intent.client_secret,
                status=PaymentStatus.PENDING,
                data={
                    "client_secret": intent.client_secret,
                    "publishable_key": self.config['stripe']['publishable_key']
                }
            )
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, message=str(e))
    
    def _create_opay_payment(
        self,
        amount: float,
        currency: str,
        metadata: Dict[str, Any],
        customer_email: str,
        return_url: str
    ) -> PaymentResult:
        """Create OPay payment order"""
        try:
            # Generate reference
            import uuid
            reference = f"OPAY_{uuid.uuid4().hex[:16]}"
            
            # Prepare payload
            payload = {
                "amount": str(amount),
                "currency": currency,
                "reference": reference,
                "country": "NG",
                "email": customer_email,
                "callbackUrl": return_url,
                "metadata": metadata,
                "products": [{
                    "name": metadata.get('item_name', 'Book Purchase'),
                    "quantity": 1,
                    "price": str(amount)
                }]
            }
            
            # Sign request
            signature = self._generate_opay_signature(payload)
            
            # Make API request
            response = requests.post(
                f"{self.opay_config['api_url']}/api/v1/orders",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.opay_config['merchant_id']}",
                    "Signature": signature,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return PaymentResult(
                    success=True,
                    transaction_id=data.get('orderNo'),
                    reference=reference,
                    status=PaymentStatus.PENDING,
                    data={
                        "checkout_url": data.get('cashierUrl'),
                        "order_no": data.get('orderNo')
                    }
                )
            else:
                return PaymentResult(success=False, message=response.text)
                
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _create_paypal_payment(
        self,
        amount: float,
        currency: str,
        metadata: Dict[str, Any],
        customer_email: str,
        return_url: str
    ) -> PaymentResult:
        """Create PayPal order"""
        try:
            # Get access token
            auth = requests.auth.HTTPBasicAuth(
                self.paypal_config['client_id'],
                self.paypal_config['client_secret']
            )
            
            token_response = requests.post(
                f"{self.paypal_config['api_url']}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=auth,
                timeout=30
            )
            
            if token_response.status_code != 200:
                return PaymentResult(success=False, message="Failed to get PayPal token")
            
            access_token = token_response.json().get('access_token')
            
            # Create order
            order_payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency,
                        "value": str(amount)
                    },
                    "description": metadata.get('item_name', 'Book Purchase'),
                    "custom_id": json.dumps(metadata)
                }],
                "payment_source": {
                    "paypal": {
                        "experience_context": {
                            "return_url": return_url,
                            "cancel_url": return_url,
                            "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED"
                        }
                    }
                }
            }
            
            order_response = requests.post(
                f"{self.paypal_config['api_url']}/v2/checkout/orders",
                json=order_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if order_response.status_code == 201:
                data = order_response.json()
                return PaymentResult(
                    success=True,
                    transaction_id=data['id'],
                    reference=data['id'],
                    status=PaymentStatus.PENDING,
                    data={
                        "approval_url": next(
                            (link['href'] for link in data['links'] if link['rel'] == 'approve'),
                            None
                        )
                    }
                )
            else:
                return PaymentResult(success=False, message=order_response.text)
                
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _create_flutterwave_payment(
        self,
        amount: float,
        currency: str,
        metadata: Dict[str, Any],
        customer_email: str,
        return_url: str
    ) -> PaymentResult:
        """Create Flutterwave payment"""
        try:
            import uuid
            reference = f"FLW_{uuid.uuid4().hex[:16]}"
            
            payload = {
                "tx_ref": reference,
                "amount": str(amount),
                "currency": currency,
                "redirect_url": return_url,
                "payment_options": "card,banktransfer,ussd",
                "customer": {
                    "email": customer_email,
                    "name": metadata.get('customer_name', 'Customer')
                },
                "customizations": {
                    "title": metadata.get('item_name', 'Book Purchase'),
                    "description": metadata.get('item_description', '')
                },
                "meta": metadata
            }
            
            response = requests.post(
                f"{self.flutterwave_config['api_url']}/payments",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.flutterwave_config['secret_key']}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return PaymentResult(
                        success=True,
                        transaction_id=data['data']['id'],
                        reference=reference,
                        status=PaymentStatus.PENDING,
                        data={
                            "checkout_url": data['data']['link']
                        }
                    )
            
            return PaymentResult(success=False, message=response.text)
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def verify_payment(
        self,
        provider: PaymentProvider,
        reference: str,
        transaction_id: Optional[str] = None
    ) -> PaymentResult:
        """Verify payment status with provider"""
        
        if provider == PaymentProvider.STRIPE:
            return self._verify_stripe_payment(reference)  # reference is client_secret
        elif provider == PaymentProvider.OPAY:
            return self._verify_opay_payment(transaction_id)
        elif provider == PaymentProvider.PAYPAL:
            return self._verify_paypal_payment(transaction_id)
        elif provider == PaymentProvider.FLUTTERWAVE:
            return self._verify_flutterwave_payment(transaction_id)
        
        return PaymentResult(success=False, message=f"Unknown provider: {provider}")
    
    def _verify_stripe_payment(self, payment_intent_id: str) -> PaymentResult:
        """Verify Stripe payment intent"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                return PaymentResult(
                    success=True,
                    transaction_id=intent.id,
                    status=PaymentStatus.COMPLETED,
                    data=intent.to_dict()
                )
            elif intent.status == 'requires_payment_method':
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.FAILED,
                    message="Payment requires payment method"
                )
            else:
                return PaymentResult(
                    success=False,
                    status=PaymentStatus.PENDING,
                    message=f"Payment status: {intent.status}"
                )
                
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, message=str(e))
    
    def _verify_opay_payment(self, order_no: str) -> PaymentResult:
        """Verify OPay payment"""
        try:
            signature = self._generate_opay_signature({"orderNo": order_no})
            
            response = requests.get(
                f"{self.opay_config['api_url']}/api/v1/orders/{order_no}",
                headers={
                    "Authorization": f"Bearer {self.opay_config['merchant_id']}",
                    "Signature": signature
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'SUCCESS':
                    return PaymentResult(
                        success=True,
                        transaction_id=order_no,
                        status=PaymentStatus.COMPLETED,
                        data=data
                    )
                else:
                    return PaymentResult(
                        success=False,
                        status=PaymentStatus.FAILED,
                        message=data.get('message', 'Payment failed')
                    )
            
            return PaymentResult(success=False, message="Verification failed")
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _verify_paypal_payment(self, order_id: str) -> PaymentResult:
        """Verify PayPal payment"""
        try:
            # Get access token
            auth = requests.auth.HTTPBasicAuth(
                self.paypal_config['client_id'],
                self.paypal_config['client_secret']
            )
            
            token_response = requests.post(
                f"{self.paypal_config['api_url']}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=auth,
                timeout=30
            )
            
            if token_response.status_code != 200:
                return PaymentResult(success=False, message="Failed to get PayPal token")
            
            access_token = token_response.json().get('access_token')
            
            # Get order details
            response = requests.get(
                f"{self.paypal_config['api_url']}/v2/checkout/orders/{order_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'COMPLETED':
                    return PaymentResult(
                        success=True,
                        transaction_id=order_id,
                        status=PaymentStatus.COMPLETED,
                        data=data
                    )
                elif data['status'] == 'APPROVED':
                    return PaymentResult(
                        success=False,
                        status=PaymentStatus.PENDING,
                        message="Payment approved but not captured"
                    )
                else:
                    return PaymentResult(
                        success=False,
                        status=PaymentStatus.FAILED,
                        message=f"Payment status: {data['status']}"
                    )
            
            return PaymentResult(success=False, message="Verification failed")
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _verify_flutterwave_payment(self, transaction_id: str) -> PaymentResult:
        """Verify Flutterwave payment"""
        try:
            response = requests.get(
                f"{self.flutterwave_config['api_url']}/transactions/{transaction_id}/verify",
                headers={
                    "Authorization": f"Bearer {self.flutterwave_config['secret_key']}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    tx_data = data.get('data', {})
                    if tx_data.get('status') == 'successful':
                        return PaymentResult(
                            success=True,
                            transaction_id=transaction_id,
                            status=PaymentStatus.COMPLETED,
                            data=tx_data
                        )
                    else:
                        return PaymentResult(
                            success=False,
                            status=PaymentStatus.FAILED,
                            message=f"Payment status: {tx_data.get('status')}"
                        )
            
            return PaymentResult(success=False, message="Verification failed")
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def handle_webhook(self, provider: PaymentProvider, payload: bytes, signature: str) -> PaymentResult:
        """Handle webhook from payment provider"""
        
        if provider == PaymentProvider.STRIPE:
            return self._handle_stripe_webhook(payload, signature)
        elif provider == PaymentProvider.OPAY:
            return self._handle_opay_webhook(payload, signature)
        elif provider == PaymentProvider.PAYPAL:
            return self._handle_paypal_webhook(payload, signature)
        elif provider == PaymentProvider.FLUTTERWAVE:
            return self._handle_flutterwave_webhook(payload, signature)
        
        return PaymentResult(success=False, message=f"Unknown provider: {provider}")
    
    def _handle_stripe_webhook(self, payload: bytes, signature: str) -> PaymentResult:
        """Handle Stripe webhook"""
        try:
            webhook_secret = self.config['stripe']['webhook_secret']
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
            
            if event.type == 'payment_intent.succeeded':
                payment_intent = event.data.object
                return PaymentResult(
                    success=True,
                    transaction_id=payment_intent.id,
                    status=PaymentStatus.COMPLETED,
                    data=payment_intent.to_dict()
                )
            elif event.type == 'payment_intent.payment_failed':
                payment_intent = event.data.object
                return PaymentResult(
                    success=False,
                    transaction_id=payment_intent.id,
                    status=PaymentStatus.FAILED,
                    message=payment_intent.last_payment_error.get('message', 'Payment failed')
                )
            
            return PaymentResult(success=True, message="Webhook received but no action taken")
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _handle_opay_webhook(self, payload: bytes, signature: str) -> PaymentResult:
        """Handle OPay webhook"""
        try:
            # Verify signature
            expected_signature = self._generate_opay_signature(json.loads(payload.decode()))
            if not hmac.compare_digest(signature, expected_signature):
                return PaymentResult(success=False, message="Invalid signature")
            
            data = json.loads(payload)
            
            if data.get('event') == 'order.success':
                return PaymentResult(
                    success=True,
                    transaction_id=data.get('orderNo'),
                    status=PaymentStatus.COMPLETED,
                    data=data
                )
            elif data.get('event') == 'order.failed':
                return PaymentResult(
                    success=False,
                    transaction_id=data.get('orderNo'),
                    status=PaymentStatus.FAILED,
                    message=data.get('message', 'Payment failed')
                )
            
            return PaymentResult(success=True, message="Webhook received but no action taken")
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _handle_paypal_webhook(self, payload: bytes, signature: str) -> PaymentResult:
        """Handle PayPal webhook"""
        try:
            # Verify webhook signature
            verification = {
                "auth_algo": request.headers.get('PAYPAL-AUTH-ALGO'),
                "cert_url": request.headers.get('PAYPAL-CERT-URL'),
                "transmission_id": request.headers.get('PAYPAL-TRANSMISSION-ID'),
                "transmission_sig": request.headers.get('PAYPAL-TRANSMISSION-SIG'),
                "transmission_time": request.headers.get('PAYPAL-TRANSMISSION-TIME'),
                "webhook_id": self.paypal_config['webhook_id']
            }
            
            # Verify webhook (simplified - implement full verification in production)
            data = json.loads(payload)
            
            if data.get('event_type') == 'CHECKOUT.ORDER.APPROVED':
                return PaymentResult(
                    success=True,
                    transaction_id=data['resource']['id'],
                    status=PaymentStatus.PENDING,
                    data=data
                )
            elif data.get('event_type') == 'PAYMENT.CAPTURE.COMPLETED':
                return PaymentResult(
                    success=True,
                    transaction_id=data['resource']['supplementary_data']['related_ids']['order_id'],
                    status=PaymentStatus.COMPLETED,
                    data=data
                )
            
            return PaymentResult(success=True, message="Webhook received but no action taken")
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _handle_flutterwave_webhook(self, payload: bytes, signature: str) -> PaymentResult:
        """Handle Flutterwave webhook"""
        try:
            # Verify signature
            expected_signature = hmac.new(
                self.flutterwave_config['webhook_secret'].encode(),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return PaymentResult(success=False, message="Invalid signature")
            
            data = json.loads(payload)
            
            if data.get('event') == 'charge.completed':
                if data['data']['status'] == 'successful':
                    return PaymentResult(
                        success=True,
                        transaction_id=data['data']['id'],
                        status=PaymentStatus.COMPLETED,
                        data=data
                    )
                else:
                    return PaymentResult(
                        success=False,
                        transaction_id=data['data']['id'],
                        status=PaymentStatus.FAILED,
                        message=data['data'].get('processor_response', 'Payment failed')
                    )
            
            return PaymentResult(success=True, message="Webhook received but no action taken")
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _generate_opay_signature(self, payload: Dict[str, Any]) -> str:
        """Generate OPay request signature"""
        sorted_keys = sorted(payload.keys())
        sign_str = "&".join([f"{k}={payload[k]}" for k in sorted_keys if payload[k]])
        sign_str += f"&key={self.opay_config['secret_key']}"
        return hashlib.sha256(sign_str.encode()).hexdigest()
    
    def refund_payment(
        self,
        provider: PaymentProvider,
        transaction_id: str,
        amount: Optional[float] = None,
        reason: Optional[str] = None
    ) -> PaymentResult:
        """Refund a payment"""
        
        if provider == PaymentProvider.STRIPE:
            return self._refund_stripe_payment(transaction_id, amount, reason)
        elif provider == PaymentProvider.OPAY:
            return self._refund_opay_payment(transaction_id, amount, reason)
        elif provider == PaymentProvider.PAYPAL:
            return self._refund_paypal_payment(transaction_id, amount, reason)
        elif provider == PaymentProvider.FLUTTERWAVE:
            return self._refund_flutterwave_payment(transaction_id, amount, reason)
        
        return PaymentResult(success=False, message=f"Unknown provider: {provider}")
    
    def _refund_stripe_payment(self, payment_intent_id: str, amount: Optional[float], reason: Optional[str]) -> PaymentResult:
        """Refund Stripe payment"""
        try:
            refund_params = {
                "payment_intent": payment_intent_id,
                "reason": reason or "requested_by_customer"
            }
            
            if amount:
                refund_params["amount"] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            
            return PaymentResult(
                success=True,
                transaction_id=refund.id,
                status=PaymentStatus.REFUNDED,
                data=refund.to_dict()
            )
            
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, message=str(e))
    
    def _refund_opay_payment(self, order_no: str, amount: Optional[float], reason: Optional[str]) -> PaymentResult:
        """Refund OPay payment"""
        try:
            payload = {"orderNo": order_no}
            if amount:
                payload["amount"] = str(amount)
            if reason:
                payload["reason"] = reason
            
            signature = self._generate_opay_signature(payload)
            
            response = requests.post(
                f"{self.opay_config['api_url']}/api/v1/orders/{order_no}/refund",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.opay_config['merchant_id']}",
                    "Signature": signature
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'SUCCESS':
                    return PaymentResult(
                        success=True,
                        transaction_id=data.get('refundId'),
                        status=PaymentStatus.REFUNDED,
                        data=data
                    )
            
            return PaymentResult(success=False, message=response.text)
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _refund_paypal_payment(self, capture_id: str, amount: Optional[float], reason: Optional[str]) -> PaymentResult:
        """Refund PayPal payment"""
        try:
            # Get access token
            auth = requests.auth.HTTPBasicAuth(
                self.paypal_config['client_id'],
                self.paypal_config['client_secret']
            )
            
            token_response = requests.post(
                f"{self.paypal_config['api_url']}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=auth,
                timeout=30
            )
            
            if token_response.status_code != 200:
                return PaymentResult(success=False, message="Failed to get PayPal token")
            
            access_token = token_response.json().get('access_token')
            
            refund_payload = {}
            if amount:
                refund_payload["amount"] = {
                    "currency_code": "USD",
                    "value": str(amount)
                }
            
            response = requests.post(
                f"{self.paypal_config['api_url']}/v2/payments/captures/{capture_id}/refund",
                json=refund_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return PaymentResult(
                    success=True,
                    transaction_id=data['id'],
                    status=PaymentStatus.REFUNDED,
                    data=data
                )
            
            return PaymentResult(success=False, message=response.text)
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))
    
    def _refund_flutterwave_payment(self, transaction_id: str, amount: Optional[float], reason: Optional[str]) -> PaymentResult:
        """Refund Flutterwave payment"""
        try:
            refund_payload = {}
            if amount:
                refund_payload["amount"] = amount
            
            response = requests.post(
                f"{self.flutterwave_config['api_url']}/transactions/{transaction_id}/refund",
                json=refund_payload,
                headers={
                    "Authorization": f"Bearer {self.flutterwave_config['secret_key']}"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return PaymentResult(
                        success=True,
                        transaction_id=data['data']['id'],
                        status=PaymentStatus.REFUNDED,
                        data=data
                    )
            
            return PaymentResult(success=False, message=response.text)
            
        except Exception as e:
            return PaymentResult(success=False, message=str(e))


# Singleton instance
_payment_orchestrator = None


def get_payment_orchestrator(config: Dict[str, Any] = None) -> PaymentOrchestrator:
    """Get or create payment orchestrator singleton"""
    global _payment_orchestrator
    if _payment_orchestrator is None:
        if config is None:
            raise ValueError("Config required for initializing payment orchestrator")
        _payment_orchestrator = PaymentOrchestrator(config)
    return _payment_orchestrator
