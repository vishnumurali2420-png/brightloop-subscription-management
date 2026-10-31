# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class BrightloopSubscription(models.Model):
    _name = 'brightloop.subscription'
    _description = 'Brightloop Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Subscription Number", required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    plan_id = fields.Many2one('brightloop.subscription.plan', string="Selected Plan", required=True, tracking=True)
    user_id = fields.Many2one('res.users', string="Account Manager / Staff", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string="Currency", related='company_id.currency_id', readonly=True)

    start_date = fields.Date(string="Start Date", default=fields.Date.context_today, required=True, tracking=True)
    expiry_date = fields.Date(string="Expiry Date", tracking=True)
    next_billing_date = fields.Date(string="Next Billing Date", tracking=True)
    payment_terms_id = fields.Many2one('account.payment.term', string="Payment Terms")

    status = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('expired', 'Expired'),
    ], string="Status", default='draft', required=True, tracking=True)

    line_ids = fields.One2many('brightloop.subscription.line', 'subscription_id', string="Product Lines")
    invoice_ids = fields.One2many('account.move', 'subscription_id', string="Invoices", readonly=True)
    discount_id = fields.Many2one('brightloop.discount', string="Applied Discount", tracking=True)

    amount_untaxed = fields.Monetary(string="Untaxed Amount", compute="_compute_totals", store=True)
    amount_tax = fields.Monetary(string="Taxes", compute="_compute_totals", store=True)
    amount_discount = fields.Monetary(string="Discount Amount", compute="_compute_totals", store=True)
    amount_total = fields.Monetary(string="Total Amount", compute="_compute_totals", store=True)

    invoice_count = fields.Integer(string="Invoice Count", compute="_compute_invoice_count")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('brightloop.subscription') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.subtotal', 'line_ids.tax_amount', 'discount_id')
    def _compute_totals(self):
        for sub in self:
            subtotal = sum(line.subtotal for line in sub.line_ids)
            tax = sum(line.tax_amount for line in sub.line_ids)
            disc = 0.0
            if sub.discount_id:
                eligible, msg = sub.discount_id.is_eligible(subtotal, subscription_id=sub)
                if eligible:
                    if sub.discount_id.discount_type == 'percentage':
                        disc = (subtotal * sub.discount_id.discount_value) / 100.0
                    else:
                        disc = min(sub.discount_id.discount_value, subtotal)
            sub.amount_untaxed = subtotal
            sub.amount_tax = tax
            sub.amount_discount = disc
            sub.amount_total = max(0.0, subtotal - disc + tax)

    def _compute_invoice_count(self):
        for sub in self:
            sub.invoice_count = len(sub.invoice_ids)

    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id:
            if not self.line_ids and self.plan_id.product_id:
                self.line_ids = [(0, 0, {
                    'product_id': self.plan_id.product_id.id,
                    'description': self.plan_id.name,
                    'quantity': self.plan_id.min_quantity or 1,
                    'unit_price': self.plan_id.price,
                })]
            # Set default next billing date to start date
            if not self.next_billing_date:
                self.next_billing_date = self.start_date

    def action_to_quotation(self):
        self.write({'status': 'quotation'})

    def action_confirm(self):
        self.write({'status': 'confirmed'})

    def action_activate(self):
        for sub in self:
            if not sub.line_ids:
                raise ValidationError(_("Cannot activate subscription without product lines."))
            if not sub.next_billing_date:
                sub.next_billing_date = sub.start_date
            sub.status = 'active'
            sub.message_post(body=_("Subscription activated. Recurring billing scheduled."))

    def action_pause(self):
        for sub in self:
            if not sub.plan_id.allow_pause:
                raise UserError(_("The selected plan does not allow pausing."))
            sub.status = 'paused'
            sub.message_post(body=_("Subscription has been paused."))

    def action_resume(self):
        for sub in self:
            sub.status = 'active'
            sub.message_post(body=_("Subscription resumed."))

    def action_close(self):
        for sub in self:
            if sub.status in ['draft', 'quotation'] or sub.plan_id.allow_early_cancellation:
                sub.status = 'closed'
                sub.message_post(body=_("Subscription cancelled / closed."))
            else:
                raise UserError(_("Early cancellation is restricted for this plan."))

    def action_renew(self):
        for sub in self:
            freq = sub.plan_id.billing_frequency
            interval = sub.plan_id.billing_interval or 1
            cur_expiry = sub.expiry_date or fields.Date.context_today(sub)
            if freq == 'daily':
                new_expiry = cur_expiry + relativedelta(days=interval)
            elif freq == 'weekly':
                new_expiry = cur_expiry + relativedelta(weeks=interval)
            elif freq == 'monthly':
                new_expiry = cur_expiry + relativedelta(months=interval)
            elif freq == 'yearly':
                new_expiry = cur_expiry + relativedelta(years=interval)
            else:
                new_expiry = cur_expiry + relativedelta(months=1)
            sub.expiry_date = new_expiry
            sub.status = 'active'
            sub.message_post(body=_("Subscription renewed until %s.") % new_expiry)

    def _calculate_next_billing_date(self, current_date):
        self.ensure_one()
        freq = self.plan_id.billing_frequency
        interval = self.plan_id.billing_interval or 1
        if freq == 'daily':
            return current_date + relativedelta(days=interval)
        elif freq == 'weekly':
            return current_date + relativedelta(weeks=interval)
        elif freq == 'monthly':
            return current_date + relativedelta(months=interval)
        elif freq == 'yearly':
            return current_date + relativedelta(years=interval)
        return current_date + relativedelta(months=1)

    def generate_recurring_invoice(self):
        """Generate invoice for the current billing period and increment next_billing_date."""
        self.ensure_one()
        if self.status != 'active':
            raise UserError(_("Invoices can only be generated for active subscriptions."))

        billing_date = self.next_billing_date or fields.Date.context_today(self)
        
        # Check duplicate invoice prevention for same billing period
        existing = self.env['account.move'].search([
            ('subscription_id', '=', self.id),
            ('invoice_date', '=', billing_date),
            ('state', '!=', 'cancel')
        ], limit=1)
        if existing:
            raise UserError(_("Invoice already exists for this subscription on billing date %s (Invoice: %s).") % (billing_date, existing.name))

        # Check discount eligibility
        discount_amount = 0.0
        if self.discount_id:
            subtotal = sum(l.subtotal for l in self.line_ids)
            eligible, msg = self.discount_id.is_eligible(subtotal, subscription_id=self)
            if eligible:
                if self.discount_id.discount_type == 'percentage':
                    discount_amount = (subtotal * self.discount_id.discount_value) / 100.0
                else:
                    discount_amount = min(self.discount_id.discount_value, subtotal)
                self.discount_id.usage_count += 1
            else:
                self.message_post(body=_("Discount %s could not be applied: %s") % (self.discount_id.name, msg))

        # Build invoice lines
        invoice_lines = []
        for line in self.line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': f"{line.description} (Billing Period starting {billing_date})",
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'tax_ids': [(6, 0, line.tax_ids.ids)],
            }))

        # If discount exists, add discount line as a negative item
        if discount_amount > 0:
            disc_prod = self.env.ref('brightloop_subscription.product_subscription_discount', raise_if_not_found=False)
            invoice_lines.append((0, 0, {
                'product_id': disc_prod.id if disc_prod else False,
                'name': _("Discount: %s") % self.discount_id.name,
                'quantity': 1,
                'price_unit': -discount_amount,
            }))

        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': billing_date,
            'subscription_id': self.id,
            'invoice_payment_term_id': self.payment_terms_id.id if self.payment_terms_id else False,
            'invoice_line_ids': invoice_lines,
        }
        invoice = self.env['account.move'].create(move_vals)
        
        # Advance next billing date
        self.next_billing_date = self._calculate_next_billing_date(billing_date)
        
        # Check if subscription reaches expiry
        if self.expiry_date and self.next_billing_date > self.expiry_date:
            if self.plan_id.auto_renewal:
                self.action_renew()
            else:
                self.status = 'expired'
                self.message_post(body=_("Subscription reached expiry date and auto-renewal is off. Marked Expired."))

        return invoice

    @api.model
    def cron_generate_recurring_invoices(self):
        """Cron job: Automated recurring invoice generation."""
        today = fields.Date.context_today(self)
        due_subscriptions = self.search([
            ('status', '=', 'active'),
            ('next_billing_date', '<=', today)
        ])
        for sub in due_subscriptions:
            try:
                sub.generate_recurring_invoice()
            except Exception as e:
                sub.message_post(body=_("Cron Automated Billing Failed: %s") % str(e))

    @api.model
    def cron_check_expiries_and_reminders(self):
        """Cron job: Send renewal alerts 7 days before expiry and handle auto-closure."""
        today = fields.Date.context_today(self)
        reminder_target = today + relativedelta(days=7)
        expiring_soon = self.search([
            ('status', '=', 'active'),
            ('expiry_date', '=', reminder_target)
        ])
        template = self.env.ref('brightloop_subscription.mail_template_subscription_renewal_reminder', raise_if_not_found=False)
        for sub in expiring_soon:
            if template:
                template.send_mail(sub.id, force_send=True)
            sub.message_post(body=_("Upcoming renewal reminder sent to %s.") % sub.partner_id.email)

        # Check expired subscriptions
        expired_subs = self.search([
            ('status', '=', 'active'),
            ('expiry_date', '<', today)
        ])
        for sub in expired_subs:
            if sub.plan_id.auto_renewal:
                sub.action_renew()
            else:
                sub.write({'status': 'expired'})
                sub.message_post(body=_("Subscription has expired."))
