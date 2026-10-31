# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_subscription_product = fields.Boolean(string="Is Subscription Product", default=False)
    subscription_plan_ids = fields.One2many(
        'brightloop.subscription.plan', 'product_id', string="Available Plans"
    )

    @api.constrains('list_price', 'standard_price')
    def _check_non_negative_prices(self):
        for rec in self:
            if rec.list_price < 0 or rec.standard_price < 0:
                raise ValidationError(_("Sales price and cost price cannot be negative."))
