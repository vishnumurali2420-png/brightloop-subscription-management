# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    subscription_id = fields.Many2one('brightloop.subscription', string="Related Subscription", index=True)
    subscription_payment_ids = fields.One2many('brightloop.payment', 'invoice_id', string="Recorded Payments")

    is_overdue = fields.Boolean(string="Is Overdue", compute="_compute_is_overdue", store=True)

    @api.depends('invoice_date_due', 'payment_state', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for move in self:
            if move.state == 'posted' and move.payment_state in ['not_paid', 'partial'] and move.invoice_date_due and move.invoice_date_due < today:
                move.is_overdue = True
            else:
                move.is_overdue = False
