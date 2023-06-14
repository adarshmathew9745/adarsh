# -*- coding: utf-8 -*-

from odoo import http, _
import werkzeug.utils
import json
from odoo.http import request, Response
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv import expression
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
PPG = 10  # Record List Per Page


class ServiceRequest(http.Controller):

    def get_search_domain_service_registration(self, search, attrib_values):
        domain = []
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike', srch), ('date', 'ilike', srch),
                    ('state', 'ilike', srch)
                ]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]
        return domain

    def check_access_role(self, student):
        user = request.env.user.partner_id
        if student.partner_id.id != user.id:
            parent_list = []
            for parent in student.parent_ids:
                parent_list.append(parent.user_id.partner_id.id)
            if user.id in parent_list:
                return True
            else:
                return False
        else:
            return True

    def get_student(self, student_id=None, **kw):

        partner = request.env.user.partner_id
        student = request.env['op.student'].sudo().browse(student_id)
        return student

    def _parent_prepare_portal_layout_values_services(self, student_id=None):
        val = {'registartion_count': ''}
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        registartion_count = request.env['student.services'].sudo().search_count(
            [('student_id', '=', student_id.id)])
        val['registartion_count'] = registartion_count
        return val

    @http.route(['/my/service/request',
                 '/my/service/request<int:student_id>',
                 '/my/service/request<int:student_id>/page/<int:page>',
                 '/my/service/requestpage/<int:page>'],
                type='http', auth='user', website=True)
    def all_service_request(
            self, student_id=None, date_begin=None, date_end=None, page=0,
            search='', search_in='sequence', ppg=False, sortby=None, filterby=None,
            groupby='State', **post):

        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])

        if student_id:
            val = self._parent_prepare_portal_layout_values_services(student_id.id)

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name'},
            'state': {'label': _('Status'), 'order': 'state'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'draft': {'label': _('Draft'),
                      'domain': [('state', '=', 'draft')]},
            'submit': {'label': _('Submit'),
                       'domain': [('state', '=', 'submit')]},
        }

        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']

        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = set([v[1] for v in attrib_values])

        searchbar_inputs = {
            'sequence': {'input': 'sequence',
                         'label': _('Search in sequence')},
            'state': {'input': 'Status', 'label': _('Search in Status')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        searchbar_groupby = {}

        domain += self.get_search_domain_service_registration(search, attrib_values)
        if student_id:
            keep = QueryURL('/my/service/request/%s' %
                            student_id.id, search=search, amenity=attrib_list,
                            order=post.get('order'))

        else:
            keep = QueryURL('/my/service/request',
                            search=search, amenity=attrib_list,
                            order=post.get('order'))

        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        if search and search_in:
            search_domain = []
            if search_in in ('all', 'sequence'):
                search_domain = expression.OR([search_domain,
                                               [('name', 'ilike', search), ]])
            if search_in in ('all', 'state'):
                search_domain = expression.OR([search_domain,
                                               [('state', 'ilike', search)]])
            domain += search_domain

        student = request.env["op.student"].sudo().search(
            [('user_id', '=', request.env.user.id)])

        total = request.env['student.services'].sudo().search_count([('student_id', '=', student.id)])
        if student_id:
            pager = portal_pager(
                url="/my/service/request/%s" % student_id.id,
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )
        else:
            pager = portal_pager(
                url="/my/service/request",
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )

        if student_id:
            student_access = self.get_student(student_id=student_id)
            if student_access is False:
                return request.render('website.404')
            domain +=[('student_id', '=', student.id)]
            subject_registration_id = request.env[
                'student.services'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'student.services'].browse(attributes_ids)

        else:
            subject_registration_id = request.env[
                'student.services'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'student.services'].browse(attributes_ids)

        if groupby == 'state':
            grouped_tasks = [
                request.env['student.services'].sudo().concat(*g)
                for k, g in groupbyelem(
                    subject_registration_id, itemgetter('state'))]
        else:
            grouped_tasks = [subject_registration_id]

        if student_id:
            val.update({
                'date': date_begin,
                'subject_registration_ids': subject_registration_id,
                'pager': pager,
                'ppg': ppg,
                'keep': keep,
                'stud_id': student_id,
                'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                'filterby': filterby,
                'search_count': total,
                'default_url': '/my/service/request/',
                'searchbar_sortings': searchbar_sortings,
                'sortby': sortby,
                'attributes': attributes,
                'attrib_values': attrib_values,
                'attrib_set': attrib_set,

                'searchbar_inputs': searchbar_inputs,
                'search_in': search_in,
                'grouped_tasks': grouped_tasks,
                'searchbar_groupby': searchbar_groupby,
                'groupby': groupby,
                'page_name': 'service_request_form'

            })
            return request.render(
                'odx_portal_student.all_service_request', val)

    @http.route(['/my/service_request/service_request-form'],
                auth='user', website=True, type='http')
    def all_service_request_form(self, ppg=False, page=0,
                                 sortby=None, groupby=None, filterby=None,
                                 search_in='all', search='', **kw):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        requested_service = request.env['services.configuration'].sudo().search([])
        return request.render(
            'odx_portal_student.service_request_form',
            {
                'student_id': student_id,
                'requested_services': requested_service,
                'page_name': 'service_request_form'
            })

    @http.route(['/my/service_request/selected_suspension_request-form/<int:task_id>'],
                type='http', auth='user', website=True)
    def portal_student_service_request_data(self, task_id=None):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        service_request_id = request.env[
            'student.services'].sudo().search(
            [('id', '=', task_id)])

        return request.render(
            "odx_portal_student."
            "portal_student_service_request_data",
            {'service_request': service_request_id,
             'page_name': 'service_request_form',
             'student': student_id,
             })

    @http.route(['/my/service_request/service_request-form/submit'], type='http', auth="public", website=True)
    def create_service_request_form(self, **kw):
        name = kw.get('student_id')
        service_date = kw.get('date')
        requested_service = request.httprequest.form.getlist('requested_service')
        requested_service_list = []
        for line in requested_service:
            requested_service_list.append((0, 0, {'services_line': int(line)}))

        create_service_request = request.env['student.services'].sudo().create({
            "student_id": int(name),
            "date": service_date,
            "requested_service": requested_service_list
        })
        create_service_request.action_submit()
        return werkzeug.utils.redirect(
            '/my/service_request/selected_suspension_request-form/%s' % create_service_request.id)


    @http.route(['/student/service/total_amount'],
                type='http', auth='user', website=True)
    def portal_service_totalamount_data(self, **post):
        service_ids = post.get('service_ids')
        if service_ids:
            count = range(2, len(service_ids), 4)
            amount_var=0
            for rec in count:
                amount = request.env['services.configuration'].sudo().search([('id', '=', int(service_ids[rec]))]).product_id.list_price
                amount_var+=amount
            total_amount = {
                'amount': amount_var,
            }
            return json.JSONEncoder().encode(total_amount)