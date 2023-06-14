# -- coding: utf-8 --
import base64
import os
import urllib
from urllib.parse import urlparse

import requests

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.website.controllers.main import QueryURL
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
import werkzeug.utils,json
from odoo.osv import expression

PPG = 10


class DropAbsenceController(CustomerPortal):

    def _parent_prepare_portal_layout_values_services(self, student_id=None):
        val = {'registartion_count': ''}
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        suspension_count = request.env['drop.absence'].sudo().search_count(
            [('student_id', '=', student_id.id)])
        val['suspension_count'] = suspension_count
        return val

    def get_search_domain_drop_absence(self, search, attrib_values):
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

    @http.route(['/attendance/drop',
                 '/attendance/drop<int:student_id>',
                 '/attendance/drop<int:student_id>/page/<int:page>',
                 '/attendance/drop<int:page>'],
                type='http', auth='user', website=True)
    def all_drop_absence_request(
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
            'submit': {'label': _('Submit'),
                      'domain': [('state', '=', 'submit')]},
            'review': {'label': _('Review'),
                      'domain': [('state', '=', 'review')]},
            'approval': {'label': _('Waiting for approval'),
                         'domain': [('state', '=', 'approval')]},
            'approved': {'label': _('Approved'),
                         'domain': [('state', '=', 'approved')]},
            'reject': {'label': _('rejected'),
                         'domain': [('state', '=', 'reject')]},
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

        domain += self.get_search_domain_drop_absence(search, attrib_values)
        if student_id:
            keep = QueryURL('/attendance/drop/%s' %
                            student_id.id, search=search, amenity=attrib_list,
                            order=post.get('order'))

        else:
            keep = QueryURL('/attendance/drop',
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

        total = request.env['drop.absence'].sudo().search_count([('student_id', '=', student.id)])
        if student_id:
            pager = portal_pager(
                url="/attendance/drop/%s" % student_id.id,
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )
        else:
            pager = portal_pager(
                url="/attendance/drop",
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
                'drop.absence'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'drop.absence'].browse(attributes_ids)

        else:
            subject_registration_id = request.env[
                'drop.absence'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'drop.absence'].browse(attributes_ids)

        if groupby == 'state':
            grouped_tasks = [
                request.env['drop.absence'].sudo().concat(*g).search([('student_id', '=', student.id)])
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
                'default_url': '/attendance/drop',
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
                'page_name': 'drop_absence_request_form'

            })
            return request.render(
                'odx_portal_student.absence_drop_request', val)



    @http.route(['/attendance/drop/absence_drop_form'],
                auth='user', website=True, type='http')
    def attendance_drop_form(self, ppg=False,page=0,
                       sortby=None, groupby=None, filterby=None,
                       search_in='all', search='', **kw):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([
            ('user_id', '=', user.id)])
        course = request.env['op.course'].sudo().search([])

        return request.render(
                        'odx_portal_student.absence_drop_form',{'student_id':student_id,'course':course,'page_name': 'drop_absence_request_form',})

    @http.route(['/my/drop/absence/selected/form/<int:task_id>'],
                type='http', auth='user', website=True)
    def portal_student_drop_absence_data(self, task_id=None):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        absence_request_id = request.env[
            'drop.absence'].sudo().search(
            [('id', '=', task_id)])
        return request.render(
            "odx_portal_student."
            "portal_student_drop_absence_request_data",
            {'absence_request': absence_request_id,
             'page_name': 'drop_absence_request_form',
             'student': student_id,
             })

    @http.route(['/drop_absence/submit'], type='http', auth="public", website=True)
    def portal_create_absence(self, **kw):
        student = kw.get('student_id')
        course = kw.get('course')
        date = kw.get('date')

        created_absence = request.env['drop.absence'].sudo().create({
            "student_id": int(student),
            "course_id": int(course),
            "date": date,
        })
        created_absence.action_review()
        subject_id_list = kw.get('subject_id_list')
        for lines in range(int(subject_id_list)):
            subject_id = 'onchange_subject_id' + str(lines)
            percentage = 'percentage' + str(lines)
            reason = 'reason' + str(lines)
            document_id = 'document' + str(lines)
            subject = kw.get(subject_id)
            percentage_var = kw.get(percentage)
            reason_var = kw.get(reason)
            document = kw.get(document_id)
            result_document = base64.b64encode(document.read())
            line = request.env['subject.absent.percentage'].sudo().search([('drop_id', '=', created_absence.id)])
            for rec in line:
                if rec.subject_id.name == subject:
                    rec.reason = reason_var
                    rec.document_id = result_document
        created_absence.action_submit()
        return werkzeug.utils.redirect('/my/drop/absence/selected/form/%s' % created_absence.id)

    @http.route(['/drop/course/ajax/work'],
                type='http', auth='user', website=True)
    def portal_drop_course_request_data(self, **post):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        drop_course = post.get('drop_course')
        if drop_course:
            subjects = request.env['absent.record'].sudo().search([('course_id', '=', int(drop_course)),('student_id', '=', int(student_id.id))])
            subject_list = []
            for sub in subjects:
                subject_list.append({
                    'id': sub.subject_id.name,
                    'subject_id':sub.subject_id.name
                })
            drop_dict = {
                'subjects': subject_list,
            }
            return json.JSONEncoder().encode(drop_dict)