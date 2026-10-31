# -*- coding: utf-8 -*-
{
    'name': 'Brightloop Subscription Management System',
    'version': '17.0.1.0.0',
    'category': 'Sales/Subscriptions',
    'summary': 'Automated Recurring Billing, Subscription Lifecycle & Customer Portal for Brightloop Software',
    'description': """
Brightloop Smart Subscription Management System
================================================
Automate complete subscription business lifecycle inside Odoo:
- Role-based security (Admin, Staff, Customer Portal)
- Product & Variant pricing engine
- Flexible Subscription Plans (Daily, Weekly, Monthly, Yearly)
- Automated Quotation-to-Subscription workflow
- Recurring Invoice Generation with duplicate prevention
- Discount & Coupon Management (Percentage / Fixed, limits, auto-expiry)
- Payment Tracking & Multi-method reconciliation
- Customer Self-Service Portal (renew, pause, cancel, invoices)
- Real-time Analytics Dashboard & KPI tracking (MRR, ARR, Overdue)
- Cron automated renewal alerts and billing schedulers
    """,
    'author': 'Brightloop Software / Engineering Team',
    'website': 'https://www.brightloopsoftware.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'product',
        'account',
        'portal',
        'web',
    ],
    'data': [
        'security/brightloop_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/product_views.xml',
        'views/subscription_plan_views.xml',
        'views/subscription_views.xml',
        'views/quotation_template_views.xml',
        'views/discount_views.xml',
        'views/payment_views.xml',
        'views/invoice_views.xml',
        'views/dashboard_views.xml',
        'views/portal_templates.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'brightloop_subscription/static/src/scss/brightloop_dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
