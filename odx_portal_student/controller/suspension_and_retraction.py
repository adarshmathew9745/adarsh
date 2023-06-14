# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.website.controllers.main import QueryURL
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from odoo.osv import expression
import werkzeug.utils
import json

PPG = 10


class AGWsuspensionController(CustomerPortal):

    def _parent_prepare_portal_layout_values_services(self, student_id=None):
        val = {'registartion_count': ''}
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        suspension_count = request.env['suspension.request'].sudo().search_count(
            [('student_id', '=', student_id.id)])
        val['suspension_count'] = suspension_count
        return val

    def get_search_domain_retraction_registration(self, search, attrib_values):
        domain = []
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', ('name', 'ilike', srch),
                    ('state', 'ilike', srch)
                ]
                domain += [('student_id', '=', student_id.id)]

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

    def get_search_domain_suspension_registration(self, search, attrib_values):
        domain = []
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', ('name', 'ilike', srch),
                    ('state', 'ilike', srch)
                ]
                domain += [('student_id', '=', student_id.id)]

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

    @http.route(['/my/suspension_request',
                 '/my/suspension_request<int:student_id>',
                 '/my/suspension_request<int:student_id>/page/<int:page>',
                 '/my/suspension_request<int:page>'],
                type='http', auth='user', website=True)
    def all_suspension_request(
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
            'submitted': {'label': _('Submitted'),
                          'domain': [('state', '=', 'submitted')]},
            'library approval': {'label': _('Waiting Library Approval'),
                                 'domain': [('state', '=', 'library approval')]},
            'student affair approval': {'label': _('Waiting Student Affair Approval'),
                                        'domain': [('state', '=', 'student affair approval')]},
            'social benfits approval': {'label': _('Waiting Social Benfits Approval'),
                                        'domain': [('state', '=', 'social benfits approval')]},
            'rejected': {'label': _('Rejected'),
                         'domain': [('state', '=', 'rejected')]},
            'approved': {'label': _('Waiting Library Approval'),
                         'domain': [('state', '=', 'approved')]},
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

        domain += self.get_search_domain_suspension_registration(search, attrib_values)
        if student_id:
            keep = QueryURL('/my/suspension_request/%s' %
                            student_id.id, search=search, amenity=attrib_list,
                            order=post.get('order'))

        else:
            keep = QueryURL('/my/suspension_request',
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
        domain += [('student_id', '=', student_id.id)]

        student = request.env["op.student"].sudo().search(
            [('user_id', '=', request.env.user.id)])

        total = request.env['suspension.request'].sudo().search_count([('student_id', '=', student.id)])
        if student_id:
            pager = portal_pager(
                url="/my/suspension_request/%s" % student_id.id,
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )
        else:
            pager = portal_pager(
                url="/my/suspension_request",
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
            subject_registration_id = request.env[
                'suspension.request'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'suspension.request'].browse(attributes_ids)

        else:
            subject_registration_id = request.env[
                'suspension.request'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'suspension.request'].browse(attributes_ids)

        if groupby == 'state':
            grouped_tasks = [
                request.env['suspension.request'].sudo().concat(*g).search([('student_id', '=', student_id.id)])
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
                'default_url': '/my/suspension_request',
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
                'page_name': 'suspension_request_form'

            })
            return request.render(
                'odx_portal_student.all_suspension_request', val)

    @http.route(['/my/suspension_request/selected_suspension_request-form/<int:task_id>'],
                type='http', auth='user', website=True)
    def portal_student_suspension_request_data(self, task_id=None):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        suspension_request_id = request.env[
            'suspension.request'].sudo().search(
            [('id', '=', task_id)])
        service = request.env['services.line'].sudo().search([('id', '=', task_id)])
        return request.render(
            "odx_portal_student."
            "portal_student_suspension_request_data",
            {'suspension_request': suspension_request_id,
             'page_name': 'suspension_request_form',
             'student': student_id,
             })

    @http.route(['/my/suspension_request/suspension_request-form'],
                auth='user', website=True, type='http')
    def all_suspension_request_form(self, **kw):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        suspension_type = request.env['suspension.config'].sudo().search([('configuration_type','=','academic suspension'),('state','=','active')])
        specialization = request.env['op.department'].sudo().search([('id', '=', student_id.department_id.id)])
        academic_year = request.env['op.academic.year'].sudo().search([])
        # academic_term = request.env['op.academic.term'].sudo().search([])

        return request.render(
            'odx_portal_student.suspension_request_form',
            {'student_id': student_id,
             'suspension_type': suspension_type,
             'specialization': specialization,
             'academic_year': academic_year,
             # 'academic_terms': academic_term,
             'page_name': 'suspension_request_form',
             })

    @http.route(['/suspension/request/registration/submit'], type='http', auth="public", website=True)
    def create_suspension_request_form(self, **kw):
        student_id = kw.get('student_id')
        suspension_type = kw.get('suspension_type')
        student_number = kw.get('student_number')
        student_phone = kw.get('student_phone')
        specialization = kw.get('specialization')
        academic_year = kw.get('academic_year')
        request_date = kw.get('date')
        academic_term = request.httprequest.form.getlist('academic_term')
        create_suspension_request = request.env['suspension.request'].sudo().create({
            "student_id": int(student_id),
            "suspension_id": int(suspension_type),
            "student_no": student_number,
            "student_phone_no": student_phone,
            "departments_id": int(specialization),
            "academic_year": int(academic_year),
            "request_date": request_date,
            "academic_ids": academic_term
        })
        create_suspension_request.action_submit()
        return werkzeug.utils.redirect(
            '/my/suspension_request/selected_suspension_request-form/%s' % create_suspension_request.id)

    @http.route(['/my/retraction/request',
                 '/my/retraction/request<int:student_id>',
                 '/my/retraction/request<int:student_id>/page/<int:page>',
                 '/my/retraction/request<int:page>'],
                type='http', auth='user', website=True)
    def all_retraction_request(
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
            'submitted': {'label': _('Submitted'),
                          'domain': [('state', '=', 'submitted')]},
            'library approval': {'label': _('Waiting Library Approval'),
                                 'domain': [('state', '=', 'library approval')]},
            'student affair approval': {'label': _('Waiting Student Affair Approval'),
                                        'domain': [('state', '=', 'student affair approval')]},
            'social benfits approval': {'label': _('Waiting Social Benfits Approval'),
                                        'domain': [('state', '=', 'social benfits approval')]},
            'rejected': {'label': _('Rejected'),
                         'domain': [('state', '=', 'rejected')]},
            'approved': {'label': _('Waiting Library Approval'),
                         'domain': [('state', '=', 'approved')]},
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

        searchbar_groupby = {
            # 'none': {'input': 'none', 'label': _('None')},
            # 'state': {'input': 'state', 'label': _('State')},
        }

        domain += self.get_search_domain_retraction_registration(search, attrib_values)
        if student_id:
            keep = QueryURL('/my/retraction/request/%s' %
                            student_id.id, search=search, amenity=attrib_list,
                            order=post.get('order'))

        else:
            keep = QueryURL('/my/retraction/request',
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

        total = request.env['retraction.request'].sudo().search_count([('student_id', '=', student.id)])
        if student_id:
            pager = portal_pager(
                url="/my/retraction/request/%s" % student_id.id,
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )
        else:
            pager = portal_pager(
                url="/my/retraction/request",
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )

        if student_id:
            student_access = self.get_student(student_id=student_id)
            domain += [('student_id', '=', student_id.id)]
            if student_access is False:
                return request.render('website.404')

            subject_registration_id = request.env[
                'retraction.request'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'retraction.request'].browse(attributes_ids)

        else:
            domain += [('student_id', '=', student_id.id)]
            subject_registration_id = request.env[
                'retraction.request'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'retraction.request'].browse(attributes_ids)

        if groupby == 'state':
            grouped_tasks = [
                request.env['retraction.request'].sudo().concat(*g)
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
                'default_url': '/my/retraction/request',
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
                'page_name': 'retraction_request_form'
            })
            return request.render(
                'odx_portal_student.all_retraction_request', val)

    @http.route(['/my/retraction/request/selected/form/<int:task_id>'],
                type='http', auth='user', website=True)
    def portal_student_retraction_request_data(self, task_id=None):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        retraction_request_id = request.env[
            'retraction.request'].sudo().search(
            [('id', '=', task_id)])
        service = request.env['services.line'].sudo().search([('id', '=', task_id)])
        return request.render(
            "odx_portal_student."
            "portal_student_retraction_request_data",
            {'retraction_request': retraction_request_id,
             'page_name': 'retraction_request_form',
             'student': student_id,
             })

    @http.route(['/my/retraction_request/retraction_request-form'],
                auth='user', website=True, type='http')
    def all_retraction_request_form(self, **kw):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        suspension_type = request.env['suspension.config'].sudo().search(
            [('configuration_type', '=', 'clearance withdrawn')])
        course = request.env['op.course'].sudo().search([])
        specialization = request.env['op.department'].sudo().search([('id', '=', student_id.department_id.id)])
        academic_year = request.env['op.academic.year'].sudo().search([])

        return request.render(
            'odx_portal_student.retraction_request_form',
            {
                'student_id': student_id,
                'suspension_type': suspension_type,
                'specialization': specialization,
                'course': course,
                'academic_year': academic_year,
                'page_name': 'retraction_request_form'
            })

    @http.route(['/my/retraction_request/retraction_request/submit'], type='http', auth="public", website=True)
    def create_retraction_request_form(self, **kw):
        name = kw.get('student_id')
        suspension_type = kw.get('suspension_type')
        student_number = kw.get('student_number')
        student_phone = kw.get('student_phone')
        specialization = kw.get('specialization')
        course = kw.get('course')
        academic_year = kw.get('academic_year')
        request_date = kw.get('request_date')
        withdrawn_reason = kw.get('withdrawn_reason')
        term = kw.get('term')
        reject_reason = kw.get('reject_reason')
        create_retraction_request = request.env['retraction.request'].sudo().create({
            "student_id": int(name),
            "suspension_id": int(suspension_type),
            "student_no": student_number,
            "student_phone_no": student_phone,
            "departments_id": int(specialization),
            "course_id": int(course),
            "academic_year": int(academic_year),
            "request_date": request_date,
            "retraction_reason": withdrawn_reason,
            "academic_term": int(term),
            "reject_reason": reject_reason,
        })
        create_retraction_request.action_submit()
        return werkzeug.utils.redirect('/my/retraction/request/selected/form/%s' % create_retraction_request.id)

    @http.route(['/terms/ajax/work'],
                type='http', auth='user', website=True)
    def portal_demo_request_data(self, **post):
        date_list = []
        academic_year = post.get('academic_year')
        if academic_year:
            year = request.env['op.academic.year'].sudo().search([('id', '=', academic_year)])
            terms = request.env['op.academic.term'].sudo().search([('academic_year_id', '=', int(academic_year))])
            term_list = []
            for term in terms:
                term_list.append({
                    'id': term.id,
                    'name': term.name
                })
            date_start = str(year.start_date)
            date_end = str(year.end_date)
            date_dict = {
                'start_date': date_start,
                'end_date': date_end,
                'terms': term_list,
            }
            date_list.append(date_start)
            date_list.append(date_end)
            return json.JSONEncoder().encode(date_dict)

    @http.route(['/terms/suspension/ajax/work'],
                type='http', auth='user', website=True)
    def portal_suspension_request_data(self, **post):
        academic_year = post.get('academic_year')
        if academic_year:
            terms = request.env['op.academic.term'].sudo().search([('academic_year_id', '=', int(academic_year))])
            term_list = []
            for term in terms:
                term_list.append({
                    'id': term.id,
                    'name': term.name
                })
            date_dict = {
                'terms': term_list,
            }
            return json.JSONEncoder().encode(date_dict)

    @http.route(['/terms/new/ajax/work'],
                type='http', auth='user', website=True)
    def portal_retract_request_data(self, **post):
        academic_term = post.get('academic_term')
        if academic_term:
            terms = request.env['op.academic.term'].sudo().search([('id', '=', int(academic_term))])
            term_list = []
            for term in terms:
                term_list.append({
                    'start_date': str(term.term_start_date),
                })
            date_dict = {
                'terms': term_list,
            }
            return json.JSONEncoder().encode(date_dict)