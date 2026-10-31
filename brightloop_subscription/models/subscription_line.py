# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SubscriptionLine(models.Model):
    _name = 'brightloop.subscription.line'
    _description = 'Subscription Product Line'

    subscription_id = fields.Many2one('brightloop.subscription', string="Subscription", ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    description = fields.Text(string="Description")
    quantity = fields.Float(string="Quantity", default=1.0, required=True)
    unit_price = fields.Float(string="Unit Price (₹)", required=True)
    tax_ids = fields.Many2many('account.tax', string="Taxes")
    subtotal = fields.Monetary(string="Subtotal", compute="_compute_line_amounts", store=True)
    tax_amount = fields.Monetary(string="Tax Amount", compute="_compute_line_amounts", store=True)
    total_amount = fields.Monetary(string="Total Amount", compute="_compute_line_amounts", store=True)
    currency_id = fields.Many2one(related='subscription_id.currency_id', readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.display_name
            self.unit_price = self.product_id.lst_price
            self.tax_ids = self.product_id.taxes_id

    @api.depends('quantity', 'unit_price', 'tax_ids')
    def _compute_line_amounts(self):
        for line in self:
            price = line.unit_price * line.quantity
            taxes = line.tax_ids.compute_all(line.unit_price, line.currency_id, line.quantity, product=line.product_id)
            line.subtotal = taxes['total_excluded']
            line.tax_amount = sum(t['amount'] for t in taxes['taxes'])
            line.total_amount = taxes['total_included']

    @api.constrains('quantity', 'unit_price')
    def _check_qty_price(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("Line quantity must be greater than zero."))
            if line.unit_price < 0:
                raise ValidationError(_("Line unit price cannot be negative."))
