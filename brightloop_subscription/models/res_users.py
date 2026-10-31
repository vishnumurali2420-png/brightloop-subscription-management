# -*- coding: utf-8 -*-
import re
from odoo import models, api, _
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.constrains('password')
    def _check_password_complexity(self):
        for user in self:
            if not user.password:
                continue
            pwd = user.password
            # Criteria: > 8 chars, uppercase, lowercase, special char
            if len(pwd) <= 8:
                raise ValidationError(_("Password must be strictly more than 8 characters in length."))
            if not re.search(r'[A-Z]', pwd):
                raise ValidationError(_("Password must contain at least one uppercase letter."))
            if not re.search(r'[a-z]', pwd):
                raise ValidationError(_("Password must contain at least one lowercase letter."))
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd):
                raise ValidationError(_("Password must contain at least one special character (!@#$%^&* etc.)."))
