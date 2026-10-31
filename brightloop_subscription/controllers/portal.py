# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class BrightloopCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'subscription_count' in counters:
            values['subscription_count'] = request.env['brightloop.subscription'].search_count([
                ('partner_id', '=', partner.id)
            ])
        return values

    @http.route(['/my/subscriptions', '/my/subscriptions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_subscriptions(self, page=1, **kw):
        partner = request.env.user.partner_id
        sub_obj = request.env['brightloop.subscription']
        domain = [('partner_id', '=', partner.id)]
        
        subscription_count = sub_obj.search_count(domain)
        pager = portal_pager(
            url="/my/subscriptions",
            total=subscription_count,
            page=page,
            step=10
        )
        subscriptions = sub_obj.search(domain, order="id desc", limit=10, offset=pager['offset'])
        
        return request.render("brightloop_subscription.portal_my_subscriptions", {
            'subscriptions': subscriptions,
            'page_name': 'subscription',
            'pager': pager,
        })

    @http.route(['/my/subscription/<int:sub_id>'], type='http', auth="user", website=True)
    def portal_my_subscription_detail(self, sub_id, **kw):
        subscription = request.env['brightloop.subscription'].browse(sub_id)
        # Ensure security check
        if subscription.partner_id.id != request.env.user.partner_id.id:
            return request.redirect('/my')
        return request.render("brightloop_subscription.portal_my_subscription_detail", {
            'subscription': subscription,
            'page_name': 'subscription',
        })

    @http.route(['/my/subscription/<int:sub_id>/pause'], type='http', auth="user", website=True)
    def portal_pause_subscription(self, sub_id, **kw):
        sub = request.env['brightloop.subscription'].browse(sub_id)
        if sub.partner_id.id == request.env.user.partner_id.id and sub.plan_id.allow_pause:
            sub.action_pause()
        return request.redirect(f'/my/subscription/{sub_id}')

    @http.route(['/my/subscription/<int:sub_id>/resume'], type='http', auth="user", website=True)
    def portal_resume_subscription(self, sub_id, **kw):
        sub = request.env['brightloop.subscription'].browse(sub_id)
        if sub.partner_id.id == request.env.user.partner_id.id:
            sub.action_resume()
        return request.redirect(f'/my/subscription/{sub_id}')

    @http.route(['/my/subscription/<int:sub_id>/cancel'], type='http', auth="user", website=True)
    def portal_cancel_subscription(self, sub_id, **kw):
        sub = request.env['brightloop.subscription'].browse(sub_id)
        if sub.partner_id.id == request.env.user.partner_id.id and sub.plan_id.allow_early_cancellation:
            sub.action_close()
        return request.redirect(f'/my/subscription/{sub_id}')
