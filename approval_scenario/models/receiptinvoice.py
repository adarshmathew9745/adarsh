from odoo import api, models, fields, _
from lxml import etree, html
import json


class ResUsersInherit(models.Model):
    _inherit = "res.users"

    approval_limit = fields.Float(string="Approval Limit")


class HrEmployeeInherit(models.Model):
    _inherit = "hr.employee"

    def _visit_domain(self):
        domain = []
        data = self.env['res.users'].search([])
        for user_id in data:
            if user_id.has_group('sales_team.group_sale_salesman_all_leads'):
                domain.append(user_id.employee_id.id)
        return [('id', 'in', domain)]

    parent_id = fields.Many2one('hr.employee', default=lambda self: self.env.user, domain=_visit_domain)


class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('pending', 'Pending For Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('sale', 'Sale Order')])
    manager_id = fields.Many2one('hr.employee', tracking=True, readonly=True)
    limit = fields.Float(string="Approval Limits", compute='compute_approval_limit')
    total = fields.Float(string="Approval Limit")
    partner_invoice_id = fields.Many2one('res.partner', required=False)
    partner_shipping_id = fields.Many2one('res.partner', required=False)
    quotation_link = fields.Char(string='Quotation Link')
    testbool = fields.Boolean(string='test bool', compute='compute_pending_approval', readonly=False)
    test_bool_second = fields.Boolean(string='test approve', compute='compute_approve_reject', readonly=False)
    button_second = fields.Boolean(string='button', compute='compute_button', readonly=True)
    test_field = fields.Char(string="Test Field")




    def write(self, vals):
        res = super(SaleOrderInherit, self).write(vals)
        if self.state =='approved':
            fields_changed = {}
            for field_name in vals:
                field_value = vals[field_name]
                if self[field_name] != field_value:
                    fields_changed[field_name] = self[field_name]
            if fields_changed:
                self.write({'state': 'draft'})
        return res

    # def write(self, vals):
    #     if vals and vals.get('state') not in ['sale', 'approved']:
    #         vals['state'] = 'draft'
    #     res = super(SaleOrderInherit, self).write(vals)
    #     return res

    def _create_request_approve(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        activity_vals = {
            'activity_type_id': activity_type.id,
            'user_id': self.env.user.employee_id.parent_id.user_id.id,
            'res_id': self.id,
            'res_model_id': self.env.ref('sale.model_sale_order').id,
            'date_deadline': fields.Date.today(),
            'summary': 'Quotation activity',
            'note': 'Quotation Approve Request',
            'automated': True
        }
        self.env['mail.activity'].sudo().create(activity_vals)

    # def _create_activity_approval(self):
    #     activity_type = self.env.ref('mail.mail_activity_data_todo')
    #     activity = self.env['mail.activity'].create({
    #         'activity_type_id': activity_type.id,
    #         'summary': 'Scheduled Activity Description',
    #         'note': 'Additional information or instructions',
    #         'user_id': self.env.user.employee_id.parent_id.user_id.id,
    #         'res_id': self.id,
    #         'res_model_id': self.env['ir.model']._get(self._name).id,
    #         'date_deadline': fields.Date.today(),
    #     })
    #     self.env['mail.activity'].sudo().create(activity)
    #
    # def _create_activity_reject(self):
    #     activity_type = self.env.ref('mail.mail_activity_data_todo')
    #     activity = self.env['mail.activity'].create({
    #         'activity_type_id': activity_type.id,
    #         'summary': 'Scheduled Activity Description',
    #         'note': 'Additional information or instructions',
    #         'user_id': self.env.user.employee_id.parent_id.user_id.id,
    #         'res_id': self.id,
    #         'res_model_id': self.env['ir.model']._get(self._name).id,
    #         'date_deadline': fields.Date.today(),
    #     })
    #     self.env['mail.activity'].sudo().create(activity)

    def submit_for_approval(self):
        if self.env.user.approval_limit > self.amount_total:
            self.state = 'approved'
            if not self.quotation_link:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                self.quotation_link = '%s/web#id=%d&action=316&model=%s&view_type=%s' % (
                    base_url, self.id, 'sale.order', 'form')
                # self.quotation_link = '<a href="%s/web#id=%d&action=316&model=%s"></a>' % (
                #     base_url, self.id, self._name)
                print(self._name)
        else:
            self._create_request_approve()
            self.state = 'pending'
            if not self.quotation_link:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                self.quotation_link = '%s/web#id=%d&action=316&model=%s&view_type=%s' % (
                    base_url, self.id, 'sale.order', 'form')
                # self.quotation_link = '<a href="%s/web#id=%d&action=316&model=%s"></a>' % (
                #     base_url, self.id, self._name)
                print(self._name)
            msg = _(
                "Quotation : %(created)s Send To Manager: %(date)s",
                created=self.name,
                date=self.env.user.employee_id.parent_id.name,
            )
            self.message_post(body=msg)
            return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'approval.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_manager_id': self.env.user.employee_id.parent_id.id,
                                'default_sale_order_id': self.id},
                    }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrderInherit, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                            submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                modifiers = json.loads(node.get("modifiers"))
                if 'readonly' not in modifiers:
                    modifiers['readonly'] = ['|', ['state', '=', 'pending'], ['state', '=', 'sale']]
                else:
                    if type(modifiers['readonly']) != bool:
                        modifiers['readonly'].insert(0, '|')
                        modifiers['readonly'] += ['|', ['state', '=', 'pending'], ['state', '=', 'sale']]
                node.set("modifiers", json.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res

    @api.depends('manager_id')
    def compute_approval_limit(self):
        for rec in self:
            if rec.manager_id:
                rec.limit = rec.manager_id.user_id.approval_limit
            elif rec.user_id:
                rec.limit = rec.user_id.approval_limit
            else:
                rec.limit = 0

    @api.model
    def create(self, vals):
        if not vals.get('note'):
            vals['note'] = 'New Order'
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.order.quotation') or _('New')
        res = super(SaleOrderInherit, self).create(vals)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.quotation_link = '<a href="%s/web#id=%d&action=316&model=%s&view_type=%s" ></a>' % (
            base_url, self.id, 'sale.order', 'form')
        # self.quotation_link = '<a href="%s/web#id=%d&action=316&model=%s"></a>' % (
        #     base_url, self.id, self._name)
        print(self._name)
        msg = _(
            "Created by: %(created)s <br/>Created date: %(date)s",
            created=self.env.user.name,
            date=res.date_order,
        )
        res.manager_id = self.env.user.employee_id.parent_id.id
        res.message_post(body=msg)
        return res

    def _submit_for_approve_create_schedule(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        activity_vals = {
            'activity_type_id': activity_type.id,
            'user_id': self.user_id.id,
            'res_id': self.id,
            'res_model_id': self.env.ref('sale.model_sale_order').id,
            'date_deadline': fields.Date.today(),
            'summary': 'Quotation activity',
            'note': 'Quotation Approved',
            'automated': True
        }
        self.env['mail.activity'].sudo().create(activity_vals)

    def submit_for_approve(self):
        self._submit_for_approve_create_schedule()
        return {'type': 'ir.actions.act_window',
                'res_model': 'approve.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_sale_order_id': self.id,
                    'default_manager_id': self.env.user.employee_id.parent_id.id,
                    'default_sale_person': self.user_id.id,
                },
                }
    def _submit_for_reject_create_schedule(self):
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        activity_vals = {
            'activity_type_id': activity_type.id,
            'user_id': self.user_id.id,
            'res_id': self.id,
            'res_model_id': self.env.ref('sale.model_sale_order').id,
            'date_deadline': fields.Date.today(),
            'summary': 'Quotation activity',
            'note': 'Quotation Rejected',
            'automated': True
        }
        self.env['mail.activity'].sudo().create(activity_vals)

    def submit_for_reject(self):
        self._submit_for_reject_create_schedule()
        self.state = 'draft'
        return {'type': 'ir.actions.act_window',
                'res_model': 'reject.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_sale_order_id': self.id,
                            'default_manager_id': self.env.user.employee_id.parent_id.id,
                            'default_sale_person': self.user_id.id,
                            },
                }

    def create_sale_order(self):
        self.action_confirm()
        # self.state = 'sale'
        full_mail = 'Sale order created:', self.name
        mail_values = {
            'email_from': self.env.user.employee_id.work_email,
            'email_to': self.create_uid.employee_id.work_email,
            'subject': 'Sale Order Created',
            'body_html': full_mail,
            'state': 'outgoing',
            'is_notification': True,
            'auto_delete': True,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()

    def set_to_draft(self):
        if self.state == 'rejected' or self.state == 'sale':
            self.state = 'draft'

    @api.depends('user_id')
    def compute_pending_approval(self):
        for rec in self:
            if self.env.user.id == rec.manager_id.user_id.id:
                if self.amount_total > self.env.user.approval_limit:
                    self.testbool = False
                else:
                    self.testbool = True
            else:
                self.testbool = True

    @api.depends('user_id')
    def compute_button(self):
        if self.state == 'sale':
            self.button_second = True
        else:
            self.button_second = False

    @api.depends('user_id')
    def compute_approve_reject(self):
        for rec in self:
            if (self.env.user.has_group(
                    'sales_team.group_sale_salesman_all_leads') or self.env.user.has_group(
                'sales_team.group_sale_manager')) and self.amount_total < self.env.user.approval_limit and (
                    self.state == 'draft' or self.state == 'pending'):
                self.test_bool_second = True
            else:
                rec.test_bool_second = False

