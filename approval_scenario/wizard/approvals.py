from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalWizard(models.TransientModel):
    _name = 'approval.wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Approval Wizard'

    manager_id = fields.Many2one('hr.employee', readonly=True)
    sale_order_id = fields.Many2one('sale.order', readonly=True)
    quotation_link = fields.Char(string='Quotation Link')

    # without template
    # def action_send_email(self):
    #     if self.manager_id:
    #         template_id = self.env.ref('approval_scenario.approval_request_to_manager')
    #         mail_values = {
    #             'email_from': self.env.user.employee_id.work_email,
    #             'email_to': self.env.user.employee_id.parent_id.work_email,
    #             'subject': 'New Approval Request has Recieved',
    #             'state': 'outgoing',
    #             'is_notification': True,
    #             'auto_delete': True,
    #         }
    #         mail = self.env['mail.mail'].sudo().create(mail_values)
    #         mail.send()
    #         for rec in self:
    #             template_id.send_mail(self.sale_order_id.id)
    #     else:
    #         raise UserError(_('User has no Manager!'))
    #     print(self.env.user.employee_id.work_email)
    #     print(self.env.user.employee_id.parent_id.work_email)


    # with template
    def action_send_email(self):
        if self.manager_id:
            self.sale_order_id.manager_id = self.manager_id.id
            template = self.env.ref('approval_scenario.approval_request_to_manager').id
            template_id = self.env['mail.template'].browse(template)
            template_id.send_mail(self.sale_order_id.id, force_send=True)
            # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            # self.quotation_link = '<a href="%s/web#id=%d&action=316&model=%s&view_type=%s&" style="background-color: #875A7B; padding: 10px 16px 10px 16px; text-decoration: none; color: #fff; border-radius: 20px; font-size:13px;">%s</a>' % (
            #     base_url, self.sale_order_id.id, 'sale.order', 'form', 'New Approval Request')
            # channel = self.env['mail.channel'].channel_get([self.env.user.employee_id.parent_id.address_home_id.id])
            # self.ensure_one()
            # channel_id = self.env['mail.channel'].browse(channel['id'])
            # sale_order = self.env['sale.order'].sudo().search([('id', '=', self.env.context.get('active_id'))])
            # print('sale_order', sale_order)
            # body_html = self.quotation_link
            # channel_id.message_post(
            #     body=body_html,
            #     message_type='notification',
            #     subtype_xmlid='mail.mt_comment',
            # )
        else:
            raise UserError(_('User has no Manager!'))
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.quotation_link = '<a href="%s/web#id=%d&action=316&model=%s&view_type=%s&" style="background-color: #875A7B; padding: 10px 16px 10px 16px; text-decoration: none; color: #fff; border-radius: 20px; font-size:13px;">%s</a>' % (
            base_url, self.sale_order_id.id, 'sale.order', 'form', 'New Approval Request')

        body_html = self.quotation_link
        channel = self.env['mail.channel'].sudo().channel_get(
            [self.env.user.employee_id.parent_id.user_id.partner_id.id])
        channel_id = self.env['mail.channel'].browse(channel["id"])
        channel_id.message_post(
            body=(body_html),
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

         # odoobot_id = self.env.ref('base.partner_root').id
        # channel = self.env['mail.channel'].sudo().search(
        #     [('name', '=', 'Approval Request'), ('channel_partner_ids', 'in', [(odoobot_id), (self.manager_id.address_home_id.id)])],
        #     limit=1)
        # if not channel:
        #     channel = self.env['mail.channel'].with_context(
        #         mail_create_nosubscribe=True).sudo().create({
        #         'channel_partner_ids': [(6, 0, odoobot_id), (6, 0, self.manager_id.address_home_id.id)],
        #         'public': 'private',
        #         'channel_type': 'channel',
        #         'name': f'Approval Request',
        #         'display_name': f'Approval Request'
        #     })
        # res = channel.sudo().message_post(
        #     body=body_html,
        #     author_id=odoobot_id,
        #     message_type="comment",
        #     subtype_xmlid="mail.mt_comment",
        # )

