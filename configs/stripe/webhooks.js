// =============================================================================
// STRIPE WEBHOOK CONFIGURATION
// =============================================================================

module.exports = {
  // Webhook Handlers
  handlers: {
    'payment_intent.succeeded': async (event, stripe, db) => {
      const paymentIntent = event.data.object;
      
      // Update payment in database
      await db.payment.update({
        where: { stripePaymentIntentId: paymentIntent.id },
        data: {
          status: 'completed',
          paidAt: new Date(),
        },
      });
      
      // Grant access to purchased item
      const payment = await db.payment.findFirst({
        where: { stripePaymentIntentId: paymentIntent.id },
      });
      
      if (payment?.itemType === 'book') {
        await db.userBook.create({
          data: {
            userId: payment.userId,
            bookId: payment.itemId,
            paymentId: payment.id,
            purchasedAt: new Date(),
          },
        });
      } else if (payment?.itemType === 'subscription') {
        await db.userSubscription.create({
          data: {
            userId: payment.userId,
            planId: payment.itemId,
            paymentId: payment.id,
            status: 'active',
            startDate: new Date(),
            endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
          },
        });
      }
    },
    
    'payment_intent.payment_failed': async (event, stripe, db) => {
      const paymentIntent = event.data.object;
      
      await db.payment.update({
        where: { stripePaymentIntentId: paymentIntent.id },
        data: {
          status: 'failed',
          errorMessage: paymentIntent.last_payment_error?.message,
        },
      });
    },
    
    'charge.refunded': async (event, stripe, db) => {
      const charge = event.data.object;
      
      await db.payment.update({
        where: { stripeChargeId: charge.id },
        data: {
          status: 'refunded',
          refundedAt: new Date(),
        },
      });
    },
  },
};
