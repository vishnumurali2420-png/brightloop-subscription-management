# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BrightloopDiscount(models.Model):
    _name = 'brightloop.discount'
    _description = 'Brightloop Discount & Coupon Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Discount Name", required=True)
    code = fields.Char(string="Coupon Code", unique=True, tracking=True)
    discount_type = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (₹)')
    ], string="Discount Type", required=True, default='percentage')
    discount_value = fields.Float(string="Discount Value", required=True, tracking=True)
    min_purchase_amount = fields.Float(string="Minimum Purchase Amount (₹)", default=0.0)
    min_quantity = fields.Integer(string="Minimum Quantity", default=1)
    start_date = fields.Date(string="Start Date", default=fields.Date.context_today)
    expiry_date = fields.Date(string="Expiry Date")
    max_usage_count = fields.Integer(string="Max Usage Count", default=0, help="0 means unlimited usage.")
    usage_count = fields.Integer(string="Current Usage Count", default=0, readonly=True)
    applicable_product_ids = fields.Many2many(
        'product.product', string="Applicable Products",
        help="Leave empty if applicable to all products."
    )
    applicable_subscription_ids = fields.Many2many(
        'brightloop.subscription', string="Applicable Subscriptions",
        help="Leave empty if applicable to all subscriptions."
    )
    active = fields.Boolean(string="Active", default=True)

    @api.constrains('discount_value', 'discount_type')
    def _check_discount_value(self):
        for rec in self:
            if rec.discount_value <= 0:
                raise ValidationError(_("Discount value must be greater than zero."))
            if rec.discount_type == 'percentage' and rec.discount_value > 100:
                raise ValidationError(_("Percentage discount cannot exceed 100%."))

    @api.constrains('start_date', 'expiry_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.expiry_date and rec.expiry_date < rec.start_date:
                raise ValidationError(_("Discount Expiry Date cannot be earlier than Start Date."))

    def is_eligible(self, sub_total, quantity=1, product_id=None, subscription_id=None):
        self.ensure_one()
        today = fields.Date.context_today(self)
        if not self.active:
            return False, _("Discount is inactive.")
        if self.start_date and today < self.start_date:
            return False, _("Discount has not started yet.")
        if self.expiry_date and today > self.expiry_date:
            return False, _("Discount has expired.")
        if self.max_usage_count > 0 and self.usage_count >= self.max_usage_count:
            return False, _("Discount usage limit has been reached.")
        if sub_total < self.min_purchase_amount:
            return False, _("Subtotal does not meet minimum purchase amount of ₹%s.") % self.min_purchase_amount
        if quantity < self.min_quantity:
            return False, _("Quantity does not meet minimum quantity of %s.") % self.min_quantity
        if self.applicable_product_ids and product_id and product_id.id not in self.applicable_product_ids.ids:
            return False, _("Discount is not applicable to product: %s") % product_id.name
        if self.applicable_subscription_ids and subscription_id and subscription_id.id not in self.applicable_subscription_ids.ids:
            return False, _("Discount is not applicable to this subscription.")
        return True, "Eligible"
