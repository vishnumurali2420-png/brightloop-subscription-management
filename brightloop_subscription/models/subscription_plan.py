# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SubscriptionPlan(models.Model):
    _name = 'brightloop.subscription.plan'
    _description = 'Brightloop Subscription Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Plan Name", required=True, tracking=True)
    product_id = fields.Many2one(
        'product.product', string="Related Product", required=True,
        domain="[('is_subscription_product', '=', True)]", tracking=True
    )
    price = fields.Float(string="Subscription Price (₹)", required=True, tracking=True)
    billing_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string="Billing Frequency", required=True, default='monthly', tracking=True)
    billing_interval = fields.Integer(string="Billing Interval", default=1, required=True,
                                      help="Repeat billing every N days/weeks/months/years.")
    min_quantity = fields.Integer(string="Minimum Quantity", default=1, required=True)
    start_date = fields.Date(string="Plan Start Date", default=fields.Date.context_today)
    end_date = fields.Date(string="Plan End Date")
    auto_renewal = fields.Boolean(string="Automatic Renewal", default=True)
    allow_early_cancellation = fields.Boolean(string="Early Cancellation Permission", default=True)
    allow_pause = fields.Boolean(string="Pause Permission", default=True)
    auto_close_on_end = fields.Boolean(string="Auto Close on End Date", default=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string="Plan Status", default='draft', tracking=True)
    description = fields.Text(string="Plan Description / Features")

    @api.constrains('price', 'min_quantity')
    def _check_values(self):
        for plan in self:
            if plan.price < 0:
                raise ValidationError(_("Subscription price cannot be negative."))
            if plan.min_quantity < 1:
                raise ValidationError(_("Minimum quantity must be at least 1."))

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for plan in self:
            if plan.start_date and plan.end_date and plan.end_date < plan.start_date:
                raise ValidationError(_("Plan End Date cannot be earlier than Start Date."))

    def action_activate(self):
        self.write({'status': 'active'})

    def action_archive(self):
        self.write({'status': 'archived'})
