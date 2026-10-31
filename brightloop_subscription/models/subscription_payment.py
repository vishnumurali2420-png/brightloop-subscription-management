# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class BrightloopPayment(models.Model):
    _name = 'brightloop.payment'
    _description = 'Subscription Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc, id desc'

    name = fields.Char(string="Payment Reference", required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    invoice_id = fields.Many2one('account.move', string="Invoice Number", required=True,
                                 domain="[('move_type', '=', 'out_invoice'), ('partner_id', '=', partner_id), ('payment_state', '!=', 'paid')]")
    subscription_id = fields.Many2one(related='invoice_id.subscription_id', string="Subscription", readonly=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('online', 'Online Payment')
    ], string="Payment Method", required=True, default='upi')
    amount = fields.Monetary(string="Payment Amount (₹)", required=True)
    currency_id = fields.Many2one(related='invoice_id.currency_id', readonly=True)
    payment_date = fields.Date(string="Payment Date", default=fields.Date.context_today, required=True)
    notes = fields.Text(string="Payment Note")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], string="Payment Status", default='draft', tracking=True)

    invoice_amount_total = fields.Monetary(related='invoice_id.amount_total', string="Invoice Total", readonly=True)
    invoice_amount_residual = fields.Monetary(related='invoice_id.amount_residual', string="Outstanding Balance", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('brightloop.payment') or _('New')
        return super().create(vals_list)

    @api.constrains('amount', 'invoice_id')
    def _check_payment_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Payment amount must be strictly greater than zero."))
            if rec.invoice_id and rec.amount > rec.invoice_id.amount_residual:
                raise ValidationError(_("Payment amount (₹%s) cannot exceed invoice outstanding balance (₹%s).") % (rec.amount, rec.invoice_id.amount_residual))

    def action_confirm_payment(self):
        """Confirm payment and register it in Odoo Accounting."""
        for rec in self:
            if rec.status == 'confirmed':
                continue
            if rec.invoice_id.state != 'posted':
                raise UserError(_("Invoice must be posted/confirmed before recording payment."))
            
            # Post payment against invoice using Odoo account.payment.register wizard logic
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': rec.partner_id.id,
                'amount': rec.amount,
                'currency_id': rec.currency_id.id,
                'date': rec.payment_date,
                'ref': f"Brightloop {rec.name} - {rec.notes or ''}",
            }
            # Find journal suitable for method
            journal = self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])], limit=1)
            if journal:
                payment_vals['journal_id'] = journal.id
                
            payment = self.env['account.payment'].create(payment_vals)
            payment.action_post()

            # Reconcile invoice line with payment line
            lines_to_reconcile = (rec.invoice_id.line_ids + payment.line_ids).filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable') and not l.reconciled
            )
            if len(lines_to_reconcile) > 1:
                lines_to_reconcile.reconcile()

            rec.status = 'confirmed'
            rec.message_post(body=_("Payment of ₹%s confirmed and reconciled via %s.") % (rec.amount, rec.payment_method))
