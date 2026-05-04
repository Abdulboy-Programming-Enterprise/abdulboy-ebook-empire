// =============================================================================
// STRIPE WEBHOOK HANDLERS
// =============================================================================
// Handles Stripe webhook events for payment processing
// =============================================================================

const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

// Webhook event handlers mapping
const webhookHandlers = {
  /**
   * Handle successful payment intent
   */
  'payment_intent.succeeded': async (event, db) => {
    const paymentIntent = event.data.object;
    
    console.log(`Payment succeeded: ${paymentIntent.id}`);
    
    // Update payment status in database
    await db.payments.update({
      where: { stripe_payment_intent_id: paymentIntent.id },
      data: {
        status: 'completed',
        paid_at: new Date(),
        updated_at: new Date(),
      },
    });
    
    // Get payment details
    const payment = await db.payments.findFirst({
      where: { stripe_payment_intent_id: paymentIntent.id },
      include: { user: true },
    });
    
    if (!payment) {
      console.error(`Payment not found: ${paymentIntent.id}`);
      return;
    }
    
    // Handle based on payment type
    switch (payment.type) {
      case 'book':
        await handleBookPurchase(payment, db);
        break;
      case 'subscription':
        await handleSubscriptionPurchase(payment, db);
        break;
      case 'custom_booking':
        await handleCustomBookingPurchase(payment, db);
        break;
    }
    
    // Send confirmation email
    await sendPaymentConfirmationEmail(payment, db);
    
    // Award points for purchase
    await awardPurchasePoints(payment.user_id, payment.amount, db);
    
    // Trigger analytics event
    await trackPaymentEvent('payment_successful', payment);
  },
  
  /**
   * Handle failed payment intent
   */
  'payment_intent.payment_failed': async (event, db) => {
    const paymentIntent = event.data.object;
    const error = paymentIntent.last_payment_error;
    
    console.log(`Payment failed: ${paymentIntent.id} - ${error?.message}`);
    
    await db.payments.update({
      where: { stripe_payment_intent_id: paymentIntent.id },
      data: {
        status: 'failed',
        error_message: error?.message,
        updated_at: new Date(),
      },
    });
    
    // Send failure notification
    await sendPaymentFailureNotification(paymentIntent, error, db);
    
    // Track failed payment analytics
    await trackPaymentEvent('payment_failed', paymentIntent, error);
  },
  
  /**
   * Handle refunded charge
   */
  'charge.refunded': async (event, db) => {
    const charge = event.data.object;
    
    console.log(`Charge refunded: ${charge.id}`);
    
    await db.payments.update({
      where: { stripe_charge_id: charge.id },
      data: {
        status: 'refunded',
        refunded_at: new Date(),
        updated_at: new Date(),
      },
    });
    
    // Revoke access if needed
    const payment = await db.payments.findFirst({
      where: { stripe_charge_id: charge.id },
    });
    
    if (payment && payment.type === 'book') {
      await revokeBookAccess(payment.user_id, payment.item_id, db);
    } else if (payment && payment.type === 'subscription') {
      await cancelSubscription(payment.user_id, db);
    }
  },
  
  /**
   * Handle successful subscription creation
   */
  'customer.subscription.created': async (event, db) => {
    const subscription = event.data.object;
    
    console.log(`Subscription created: ${subscription.id}`);
    
    await db.subscriptions.upsert({
      where: { stripe_subscription_id: subscription.id },
      update: {
        status: subscription.status,
        current_period_start: new Date(subscription.current_period_start * 1000),
        current_period_end: new Date(subscription.current_period_end * 1000),
        updated_at: new Date(),
      },
      create: {
        stripe_subscription_id: subscription.id,
        stripe_customer_id: subscription.customer,
        user_id: subscription.metadata.user_id,
        plan_id: subscription.metadata.plan_id,
        status: subscription.status,
        current_period_start: new Date(subscription.current_period_start * 1000),
        current_period_end: new Date(subscription.current_period_end * 1000),
        created_at: new Date(),
        updated_at: new Date(),
      },
    });
    
    // Update user's subscription status
    await db.users.update({
      where: { id: subscription.metadata.user_id },
      data: {
        subscription_status: subscription.metadata.plan_id === 'premium' ? 'premium' : 'basic',
        subscription_started_at: new Date(),
        subscription_ends_at: new Date(subscription.current_period_end * 1000),
        updated_at: new Date(),
      },
    });
    
    // Send welcome email
    await sendSubscriptionWelcomeEmail(subscription.metadata.user_id, db);
  },
  
  /**
   * Handle subscription update (renewal, plan change)
   */
  'customer.subscription.updated': async (event, db) => {
    const subscription = event.data.object;
    
    console.log(`Subscription updated: ${subscription.id}`);
    
    await db.subscriptions.update({
      where: { stripe_subscription_id: subscription.id },
      data: {
        status: subscription.status,
        current_period_start: new Date(subscription.current_period_start * 1000),
        current_period_end: new Date(subscription.current_period_end * 1000),
        cancel_at_period_end: subscription.cancel_at_period_end,
        updated_at: new Date(),
      },
    });
    
    // Update user's subscription end date if cancelled
    if (subscription.cancel_at_period_end) {
      await db.users.update({
        where: { id: subscription.metadata.user_id },
        data: {
          subscription_ends_at: new Date(subscription.current_period_end * 1000),
          updated_at: new Date(),
        },
      });
    }
  },
  
  /**
   * Handle subscription deletion/cancellation
   */
  'customer.subscription.deleted': async (event, db) => {
    const subscription = event.data.object;
    
    console.log(`Subscription deleted: ${subscription.id}`);
    
    await db.subscriptions.update({
      where: { stripe_subscription_id: subscription.id },
      data: {
        status: 'cancelled',
        cancelled_at: new Date(),
        updated_at: new Date(),
      },
    });
    
    await db.users.update({
      where: { id: subscription.metadata.user_id },
      data: {
        subscription_status: 'cancelled',
        subscription_ends_at: new Date(),
        updated_at: new Date(),
      },
    });
    
    // Send cancellation confirmation
    await sendSubscriptionCancellationEmail(subscription.metadata.user_id, db);
  },
  
  /**
   * Handle successful invoice payment
   */
  'invoice.payment_succeeded': async (event, db) => {
    const invoice = event.data.object;
    
    console.log(`Invoice payment succeeded: ${invoice.id}`);
    
    // Record payment
    await db.payments.create({
      data: {
        stripe_invoice_id: invoice.id,
        stripe_customer_id: invoice.customer,
        amount: invoice.amount_paid / 100,
        currency: invoice.currency,
        status: 'completed',
        type: 'subscription_renewal',
        paid_at: new Date(),
        created_at: new Date(),
      },
    });
  },
  
  /**
   * Handle failed invoice payment
   */
  'invoice.payment_failed': async (event, db) => {
    const invoice = event.data.object;
    
    console.log(`Invoice payment failed: ${invoice.id}`);
    
    // Send payment failure notification
    await sendPaymentFailureNotification(invoice, null, db);
    
    // Retry logic could be implemented here
  },
};

/**
 * Handle book purchase after successful payment
 */
async function handleBookPurchase(payment, db) {
  // Add book to user's library
  await db.userBooks.create({
    data: {
      user_id: payment.user_id,
      book_id: payment.item_id,
      payment_id: payment.id,
      purchased_at: new Date(),
      access_count: 0,
    },
  });
  
  // Increment book download count
  await db.books.update({
    where: { id: payment.item_id },
    data: {
      downloads_count: { increment: 1 },
    },
  });
}

/**
 * Handle subscription purchase
 */
async function handleSubscriptionPurchase(payment, db) {
  // Create subscription record
  await db.subscriptions.create({
    data: {
      user_id: payment.user_id,
      plan_id: payment.item_id,
      payment_id: payment.id,
      status: 'active',
      start_date: new Date(),
      end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      auto_renew: true,
      created_at: new Date(),
    },
  });
  
  // Update user subscription status
  const plan = await db.subscriptionPlans.findUnique({
    where: { id: payment.item_id },
  });
  
  await db.users.update({
    where: { id: payment.user_id },
    data: {
      subscription_status: plan.name.toLowerCase(),
      subscription_started_at: new Date(),
      subscription_ends_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    },
  });
}

/**
 * Handle custom booking purchase
 */
async function handleCustomBookingPurchase(payment, db) {
  await db.bookings.update({
    where: { id: payment.item_id },
    data: {
      status: 'accepted',
      payment_id: payment.id,
      accepted_at: new Date(),
      updated_at: new Date(),
    },
  });
}

/**
 * Send payment confirmation email
 */
async function sendPaymentConfirmationEmail(payment, db) {
  // Implementation would use email service
  console.log(`Sending confirmation email for payment ${payment.id}`);
}

/**
 * Send payment failure notification
 */
async function sendPaymentFailureNotification(paymentIntent, error, db) {
  console.log(`Payment failed notification for ${paymentIntent.id}`);
}

/**
 * Send subscription welcome email
 */
async function sendSubscriptionWelcomeEmail(userId, db) {
  console.log(`Sending subscription welcome email to user ${userId}`);
}

/**
 * Send subscription cancellation email
 */
async function sendSubscriptionCancellationEmail(userId, db) {
  console.log(`Sending cancellation email to user ${userId}`);
}

/**
 * Award points for purchase
 */
async function awardPurchasePoints(userId, amount, db) {
  const points = Math.floor(amount * 10); // 10 points per dollar
  await db.users.update({
    where: { id: userId },
    data: {
      total_points: { increment: points },
    },
  });
}

/**
 * Revoke book access on refund
 */
async function revokeBookAccess(userId, bookId, db) {
  await db.userBooks.deleteMany({
    where: {
      user_id: userId,
      book_id: bookId,
    },
  });
}

/**
 * Cancel subscription on refund
 */
async function cancelSubscription(userId, db) {
  await db.subscriptions.updateMany({
    where: {
      user_id: userId,
      status: 'active',
    },
    data: {
      status: 'cancelled',
      cancelled_at: new Date(),
    },
  });
  
  await db.users.update({
    where: { id: userId },
    data: {
      subscription_status: 'cancelled',
    },
  });
}

/**
 * Track payment event for analytics
 */
async function trackPaymentEvent(eventName, data, error = null) {
  // Implementation would send to analytics service
  console.log(`Tracking payment event: ${eventName}`, { data, error });
}

/**
 * Main webhook handler
 */
async function handleStripeWebhook(request, db) {
  const sig = request.headers['stripe-signature'];
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  
  let event;
  
  try {
    event = stripe.webhooks.constructEvent(
      request.rawBody,
      sig,
      webhookSecret
    );
  } catch (err) {
    console.error(`Webhook signature verification failed: ${err.message}`);
    return { error: 'Invalid signature', status: 400 };
  }
  
  const handler = webhookHandlers[event.type];
  
  if (handler) {
    try {
      await handler(event, db);
      return { success: true, status: 200 };
    } catch (err) {
      console.error(`Webhook handler error for ${event.type}:`, err);
      return { error: 'Handler error', status: 500 };
    }
  } else {
    console.log(`Unhandled event type: ${event.type}`);
    return { success: true, status: 200 };
  }
}

module.exports = {
  handleStripeWebhook,
  webhookHandlers,
};
