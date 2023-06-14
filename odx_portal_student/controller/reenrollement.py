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


class AGWReenrollmentController(CustomerPortal):

    def _parent_prepare_portal_layout_values_services(self, student_id=None):
        val = {'registartion_count': ''}
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        suspension_count = request.env['reenrollment.request'].sudo().search_count(
            [('student_id', '=', student_id.id)])
        val['suspension_count'] = suspension_count
        return val

    def get_search_domain_reenrollement_registration(self, search, attrib_values):
        domain = []
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', ('name', 'ilike', srch),
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

    @http.route(['/my/reenrollment',
                 '/my/reenrollment<int:student_id>',
                 '/my/reenrollment<int:student_id>/page/<int:page>',
                 '/my/reenrollment<int:page>'],
                type='http', auth='user', website=True)
    def all_reenrollment_request(
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
            'check': {'label': _('Check Duration'),
                          'domain': [('state', '=', 'check')]},
            'approval': {'label': _('Waiting for Approval'),
                                 'domain': [('state', '=', 'approval')]},
            'approved': {'label': _('Approved'),
                                        'domain': [('state', '=', 'approved')]},
            'rejected': {'label': _('rejected'),
                                        'domain': [('state', '=', 'rejected')]},
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

        domain += self.get_search_domain_reenrollement_registration(search, attrib_values)
        if student_id:
            keep = QueryURL('/my/reenrollment/%s' %
                            student_id.id, search=search, amenity=attrib_list,
                            order=post.get('order'))

        else:
            keep = QueryURL('/my/reenrollment',
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

        total = request.env['reenrollment.request'].sudo().search_count([('student_id', '=', student.id)])
        if student_id:
            pager = portal_pager(
                url="/my/reenrollment/%s" % student_id.id,
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )
        else:
            pager = portal_pager(
                url="/my/reenrollment",
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
                'reenrollment.request'].sudo().search(
                domain, order=order, limit=ppg,offset=pager['offset'])
            attributes = request.env[
                'reenrollment.request'].browse(attributes_ids)

        else:
            subject_registration_id = request.env[
                'reenrollment.request'].sudo().search(
                domain, order=order, limit=ppg,offset=pager['offset'])
            attributes = request.env[
                'reenrollment.request'].browse(attributes_ids)

        if groupby == 'state':
            grouped_tasks = [
                request.env['reenrollment.request'].sudo().concat(*g).search([('student_id', '=', student.id)])
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
                'default_url': '/my/reenrollment',
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
                'page_name': 'reenrollment_request_form'

            })
            return request.render(
                'odx_portal_student.all_reenrollement_request', val)

    @http.route(['/my/reenrollment_request/reenrollment_request-form'],
                auth='user', website=True, type='http')
    def all_reenrollement_request_form(self, ppg=False,page=0,
                       sortby=None, groupby=None, filterby=None,
                       search_in='all', search='', **kw):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([
            ('user_id', '=', user.id)])
        semester = request.env['op.academic.term'].sudo().search([])
        year = request.env['op.academic.year'].sudo().search([])

        return request.render(
                        'odx_portal_student.reenrollement_request_form',{'student_id':student_id,
                                                                          'semester': semester,
                                                                          'year': year,
                                                                          'page_name':'reenrollment_request_form',
                                                                          })

    @http.route(['/my/reenrollement/request/selected/form/<int:task_id>'],
                type='http', auth='user', website=True)
    def portal_student_reenrollement_request_data(self, task_id=None):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        reenrollement_request_id = request.env[
            'reenrollment.request'].sudo().search(
            [('id', '=', task_id)])
        return request.render(
            "odx_portal_student."
            "portal_student_reenrollement_request_data",
            {'reenrollement_request': reenrollement_request_id,
             'page_name': 'reenrollment_request_form',
             'student': student_id,
             })

    @http.route(['/reenrollement/submit'], type='http', auth="public", website=True)
    def portal_create_reenrollement(self, **kw):
        name = kw.get('name')
        date = kw.get('date')
        student = kw.get('student_id')
        year = kw.get('year')
        student_no = kw.get('student_no')
        semester = kw.get('semester')
        sus_year= kw.get('sus_year')
        sus_duration = kw.get('sus_duration')
        sus_semester = kw.get('sus_semester')
        created_reenrollement = request.env['reenrollment.request'].sudo().create({
            'name':name,
            'date':date,
            'student_id':int(student),
            'academic_year':int(year),
            'student_no':student_no,
            'semester_id':int(semester),

        })
        created_reenrollement.action_check_duration()
        created_reenrollement.action_submit()
        return werkzeug.utils.redirect('/my/reenrollement/request/selected/form/%s'%created_reenrollement.id)


    @http.route(['/student/profile'],
                auth='user', website=True, type='http')
    def all_student_profile_form(self):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([
            ('user_id', '=', user.id)])

        return werkzeug.utils.redirect('/student/profile/%s'%student_id.id)

    @http.route(['/terms/enroll/ajax/work'],
                type='http', auth='user', website=True)
    def portal_enroll_request_data(self, **post):
        academic_year = post.get('academic_year')
        if academic_year:
            terms = request.env['op.academic.term'].sudo().search([('academic_year_id', '=', int(academic_year))])
            term_list = []
            for term in terms:
                term_list.append({
                    'id': term.id,
                    'name': term.name,
                })
            date_dict = {
                'terms': term_list,
            }
            return json.JSONEncoder().encode(date_dict)