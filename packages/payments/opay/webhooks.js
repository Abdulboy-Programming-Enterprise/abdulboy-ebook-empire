// =============================================================================
// OPAY WEBHOOK HANDLERS
// =============================================================================
// Handles OPay webhook events for payment processing
// =============================================================================

const crypto = require('crypto');

// Webhook event handlers mapping
const webhookHandlers = {
  /**
   * Handle successful order
   */
  'order.success': async (event, db) => {
    const order = event.data;
    
    console.log(`OPay order succeeded: ${order.orderNo}`);
    
    // Update payment status in database
    await db.payments.update({
      where: { opay_order_no: order.orderNo },
      data: {
        status: 'completed',
        paid_at: new Date(),
        updated_at: new Date(),
        opay_transaction_id: order.transactionId,
        opay_response: JSON.stringify(order),
      },
    });
    
    // Get payment details
    const payment = await db.payments.findFirst({
      where: { opay_order_no: order.orderNo },
      include: { user: true },
    });
    
    if (!payment) {
      console.error(`Payment not found: ${order.orderNo}`);
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
  },
  
  /**
   * Handle failed order
   */
  'order.failed': async (event, db) => {
    const order = event.data;
    
    console.log(`OPay order failed: ${order.orderNo} - ${order.failReason}`);
    
    await db.payments.update({
      where: { opay_order_no: order.orderNo },
      data: {
        status: 'failed',
        error_message: order.failReason,
        updated_at: new Date(),
      },
    });
    
    // Send failure notification
    await sendPaymentFailureNotification(order, db);
  },
  
  /**
   * Handle pending order
   */
  'order.pending': async (event, db) => {
    const order = event.data;
    
    console.log(`OPay order pending: ${order.orderNo}`);
    
    await db.payments.update({
      where: { opay_order_no: order.orderNo },
      data: {
        status: 'pending',
        updated_at: new Date(),
      },
    });
  },
  
  /**
   * Handle successful refund
   */
  'refund.success': async (event, db) => {
    const refund = event.data;
    
    console.log(`OPay refund successful: ${refund.refundId}`);
    
    await db.payments.update({
      where: { opay_order_no: refund.orderNo },
      data: {
        status: 'refunded',
        refunded_at: new Date(),
        updated_at: new Date(),
      },
    });
    
    // Revoke access if needed
    const payment = await db.payments.findFirst({
      where: { opay_order_no: refund.orderNo },
    });
    
    if (payment && payment.type === 'book') {
      await revokeBookAccess(payment.user_id, payment.item_id, db);
    } else if (payment && payment.type === 'subscription') {
      await cancelSubscription(payment.user_id, db);
    }
  },
};

/**
 * Handle book purchase
 */
async function handleBookPurchase(payment, db) {
  await db.userBooks.create({
    data: {
      user_id: payment.user_id,
      book_id: payment.item_id,
      payment_id: payment.id,
      purchased_at: new Date(),
      access_count: 0,
    },
  });
  
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
  const plan = await db.subscriptionPlans.findUnique({
    where: { id: payment.item_id },
  });
  
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
  console.log(`Sending OPay confirmation email for payment ${payment.id}`);
}

/**
 * Send payment failure notification
 */
async function sendPaymentFailureNotification(order, db) {
  console.log(`OPay payment failed notification for order ${order.orderNo}`);
}

/**
 * Award points for purchase
 */
async function awardPurchasePoints(userId, amount, db) {
  const points = Math.floor(amount * 0.5); // 0.5 points per Naira
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
 * Verify OPay webhook signature
 */
function verifySignature(payload, signature, privateKey) {
  const expected = crypto
    .createHmac('sha256', privateKey)
    .update(JSON.stringify(payload))
    .digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

/**
 * Main webhook handler
 */
async function handleOpayWebhook(request, db) {
  const signature = request.headers['opay-signature'];
  const privateKey = process.env.OPAY_SECRET_KEY;
  
  let payload;
  try {
    payload = typeof request.body === 'string' 
      ? JSON.parse(request.body) 
      : request.body;
  } catch (err) {
    console.error(`Failed to parse OPay webhook payload: ${err.message}`);
    return { error: 'Invalid payload', status: 400 };
  }
  
  // Verify signature
  if (!verifySignature(payload, signature, privateKey)) {
    console.error('OPay webhook signature verification failed');
    return { error: 'Invalid signature', status: 401 };
  }
  
  const eventType = payload.eventType || payload.event;
  const handler = webhookHandlers[eventType];
  
  if (handler) {
    try {
      await handler(payload, db);
      return { success: true, status: 200 };
    } catch (err) {
      console.error(`OPay webhook handler error for ${eventType}:`, err);
      return { error: 'Handler error', status: 500 };
    }
  } else {
    console.log(`Unhandled OPay event type: ${eventType}`);
    return { success: true, status: 200 };
  }
}

module.exports = {
  handleOpayWebhook,
  webhookHandlers,
  verifySignature,
};
