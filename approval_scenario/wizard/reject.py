from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'Reject Wizard'

    manager_id = fields.Many2one('hr.employee', readonly=True)
    reason = fields.Text(string="Reject Reason", required=True)
    sale_order_id = fields.Many2one('sale.order', readonly=True)
    sale_person = fields.Many2one('res.users', string='Sale Person', readonly=True)

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
    #             template_id.send_mail(rec.id)
    #     else:
    #         raise UserError(_('User has no Manager!'))
    #     print(self.env.user.employee_id.work_email)
    #     print(self.env.user.employee_id.parent_id.work_email)
    # with template
    # def _create_activity_reject(self):
    #     activity_type = self.env.ref('mail.mail_activity_data_todo')
    #     activity_vals = {
    #         'activity_type_id': activity_type.id,
    #         'user_id': self.env.user.employee_id.parent_id.user_id.id,
    #         'res_id': self.id,
    #         'res_model_id': self.env.ref('sale.model_sale_order').id,
    #         'date_deadline': fields.Date.today(),
    #         'summary': 'Quotation activity',
    #         'note': 'Quotation Rejected',
    #         'automated': True
    #     }
    #     self.env['mail.activity'].sudo().create(activity_vals)

    def action_reject(self):
        if self.sale_order_id.state:
            # self._create_activity_reject()
            self.sale_order_id.state = 'rejected'
            full_mail = 'Quotation Rejected! reason:', self.reason
            mail_values = {
                'email_from': self.env.user.employee_id.work_email,
                'email_to': self.create_uid.employee_id.work_email,
                'subject': 'Quotation Rejected',
                'body_html': full_mail,
                'state': 'outgoing',
                'is_notification': True,
                'auto_delete': True,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()
            body_html = "Quotation Rejected !!"
            channel = self.env['mail.channel'].sudo().channel_get(
                [self.sale_order_id.user_id.partner_id.id])
            channel_id = self.env['mail.channel'].browse(channel["id"])
            channel_id.message_post(
                body=(body_html),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
            # odoobot_id = self.env.user.employee_id.parent_id.id
            # channel = self.env['mail.channel'].sudo().search(
            #     [('name', '=', 'Reject Notification'),
            #      ('channel_partner_ids', 'in', [(odoobot_id), (self.sale_order_id.create_uid.id)])],
            #     limit=1)
            # if not channel:
            #     channel = self.env['mail.channel'].with_context(
            #         mail_create_nosubscribe=True).sudo().create({
            #         'channel_partner_ids': [(6, 0, odoobot_id), (6, 0, self.sale_order_id.create_uid.id)],
            #         'public': 'private',
            #         'channel_type': 'channel',
            #         'name': f'Reject Notification',
            #         'display_name': f'Reject Notification',
            #     })
            # channel.sudo().message_post(
            #     body=body_html,
            #     author_id=odoobot_id,
            #     message_type="comment",
            #     subtype_xmlid="mail.mt_comment",
            # )
