// =============================================================================
// OPAY WEBHOOK CONFIGURATION
// =============================================================================

module.exports = {
  // Webhook Handlers
  handlers: {
    'order.success': async (event, db) => {
      const order = event.data;
      
      console.log(`OPay order success: ${order.orderNo}`);
      
      // Update payment in database
      await db.payment.update({
        where: { opayOrderNo: order.orderNo },
        data: {
          status: 'completed',
          paidAt: new Date(),
          opayTransactionId: order.transactionId,
        },
      });
      
      // Grant access to purchased item
      const payment = await db.payment.findFirst({
        where: { opayOrderNo: order.orderNo },
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
    
    'order.failed': async (event, db) => {
      const order = event.data;
      
      await db.payment.update({
        where: { opayOrderNo: order.orderNo },
        data: {
          status: 'failed',
          errorMessage: order.failReason,
        },
      });
    },
    
    'refund.success': async (event, db) => {
      const refund = event.data;
      
      await db.payment.update({
        where: { opayOrderNo: refund.orderNo },
        data: {
          status: 'refunded',
          refundedAt: new Date(),
        },
      });
    },
  },
  
  // Signature Verification
  verifySignature: (payload, signature, privateKey) => {
    const crypto = require('crypto');
    const expected = crypto
      .createHmac('sha256', privateKey)
      .update(JSON.stringify(payload))
      .digest('hex');
    return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
  },
};
