# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta

class BrightloopDashboard(models.Model):
    _name = 'brightloop.dashboard'
    _description = 'Brightloop Dashboard Statistics Provider'

    @api.model
    def get_dashboard_metrics(self, filter_range='all'):
        """Calculate live metrics from database tables for KPI cards and charts."""
        today = fields.Date.context_today(self)
        
        # Base domains
        partner_count = self.env['res.partner'].search_count([('customer_rank', '>', 0)])
        active_subs = self.env['brightloop.subscription'].search([('status', '=', 'active')])
        active_subs_count = len(active_subs)
        
        # Calculate MRR (Monthly Recurring Revenue)
        mrr = 0.0
        for sub in active_subs:
            freq = sub.plan_id.billing_frequency
            amount = sub.amount_total
            if freq == 'daily':
                mrr += amount * 30
            elif freq == 'weekly':
                mrr += amount * 4.33
            elif freq == 'monthly':
                mrr += amount
            elif freq == 'yearly':
                mrr += amount / 12.0
                
        # Total Revenue (Paid Invoices)
        posted_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('subscription_id', '!=', False),
            ('state', '=', 'posted')
        ])
        total_revenue = sum(inv.amount_total for inv in posted_invoices if inv.payment_state == 'paid')
        outstanding_payments = sum(inv.amount_residual for inv in posted_invoices)
        
        # Overdue invoices
        overdue_invoices = self.env['account.move'].search_count([
            ('move_type', '=', 'out_invoice'),
            ('subscription_id', '!=', False),
            ('is_overdue', '=', True)
        ])
        
        # Expiring in 14 days
        expiring_subs_count = self.env['brightloop.subscription'].search_count([
            ('status', '=', 'active'),
            ('expiry_date', '>=', today),
            ('expiry_date', '<=', today + relativedelta(days=14))
        ])
        
        # Total Payments Received
        total_payments = self.env['brightloop.payment'].search([('status', '=', 'confirmed')])
        total_payment_amount = sum(p.amount for p in total_payments)

        # Plan Distribution data
        plans = self.env['brightloop.subscription.plan'].search([])
        plan_dist = []
        for plan in plans:
            c = self.env['brightloop.subscription'].search_count([('plan_id', '=', plan.id), ('status', '=', 'active')])
            plan_dist.append({'name': plan.name, 'count': c})

        return {
            'total_customers': partner_count,
            'active_subscriptions': active_subs_count,
            'total_revenue': round(total_revenue, 2),
            'mrr': round(mrr, 2),
            'outstanding_payments': round(outstanding_payments, 2),
            'overdue_invoices': overdue_invoices,
            'expiring_subscriptions': expiring_subs_count,
            'total_payments_received': round(total_payment_amount, 2),
            'plan_distribution': plan_dist
        }
