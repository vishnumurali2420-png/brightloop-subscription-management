# Brightloop - Smart Subscription Management System for Odoo

A production-ready subscription and recurring billing automation module natively engineered for Odoo 17 / 16.

## 🚀 Key Features
1. **Subscription Lifecycle**: Draft → Quotation → Confirmed → Active → Paused → Closed / Expired.
2. **Product Variants & Pricing**: Seamless integration with Odoo `product.template` and variants.
3. **Flexible Billing Scheduler**: Daily, Weekly, Monthly, and Yearly intervals with automated duplicate billing safeguards.
4. **Discount & Coupon Engine**: Tiered percentage / fixed discounts with threshold checks and auto-expiry.
5. **Payment Reconciliation**: UPI, Card, Cash, Bank Transfer recording and matching against invoices.
6. **Customer Portal**: Self-service portal for customers to pause, resume, cancel, and review invoices.
7. **Executive Dashboard**: Real-time MRR, ARR, Overdue Invoices, and Subscription distribution analytics.

## 🛠️ Installation & Setup
1. Clone or copy `brightloop_subscription` to your Odoo `custom_addons` path:
   ```bash
   git clone https://github.com/brightloop/brightloop-subscription-management.git
   ```
2. Update your `odoo.conf` file:
   ```ini
   addons_path = /opt/odoo/addons,/path/to/custom_addons
   ```
3. Restart the Odoo service and activate Developer Mode in Web UI.
4. Go to **Apps** -> **Update Apps List**, search for `Brightloop Subscription Management`, and click **Install**.
