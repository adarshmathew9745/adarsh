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


class SubjectDeletionController(CustomerPortal):

    def _parent_prepare_portal_layout_values_services(self, student_id=None):
        val = {'registartion_count': ''}
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        suspension_count = request.env['subject.deletion'].sudo().search_count(
            [('student_id', '=', student_id.id)])
        val['suspension_count'] = suspension_count
        return val

    def get_search_domain_subject_deletion(self, search, attrib_values):
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

    @http.route(['/subject/deletion',
                 '/subject/deletion<int:student_id>',
                 '/subject/deletion<int:student_id>/page/<int:page>',
                 '/subject/deletion<int:page>'],
                type='http', auth='user', website=True)
    def all_subject_deletion_request(
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

        searchbar_groupby = {}

        domain += self.get_search_domain_subject_deletion(search, attrib_values)
        if student_id:
            keep = QueryURL('/subject/deletion/%s' %
                            student_id.id, search=search, amenity=attrib_list,
                            order=post.get('order'))

        else:
            keep = QueryURL('/subject/deletion/',
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

        total = request.env['subject.deletion'].sudo().search_count([('student_id', '=', student.id)])
        if student_id:
            pager = portal_pager(
                url="/subject/deletion/%s" % student_id.id,
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )
        else:
            pager = portal_pager(
                url="/subject/deletion",
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
                'subject.deletion'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'drop.absence'].browse(attributes_ids)

        else:
            subject_registration_id = request.env[
                'subject.deletion'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'drop.absence'].browse(attributes_ids)

        if groupby == 'state':
            grouped_tasks = [
                request.env['subject.deletion'].sudo().concat(*g).search([('student_id', '=', student.id)])
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
                'default_url': '/subject/deletion',
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
                'page_name': 'subject_deletion_form'

            })
            return request.render(
                'odx_portal_student.subject_deletion_request', val)

    @http.route(['/subject/deletion/subject_deletion-form'],
                auth='user', website=True, type='http')
    def subject_deletion_request_form(self, ppg=False, page=0,
                                      sortby=None, groupby=None, filterby=None,
                                      search_in='all', search='', **kw):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([
            ('user_id', '=', user.id)])
        courses = request.env['op.course'].sudo().search([], order="id desc")
        batches = request.env['op.batch'].sudo().search([])
        events = request.env['calendar.events'].sudo().search([])
        semester = request.env['op.academic.term'].sudo().search([])
        year = request.env['op.academic.year'].sudo().search([])
        refund = request.env['refund.details'].sudo().search([])
        subject_id = request.env['op.subject'].sudo().search([])
        session_id = request.env['generate.time.table'].sudo().search([])

        return request.render(
            'odx_portal_student.subject_deletion_request_form',
            {'student_id': student_id,
             'courses': courses,
             'batches': batches,
             'events': events,
             'semester': semester,
             'year': year,
             'refund': refund,
             'subject_id': subject_id,
             # 'subject_del': sub_data,
             'session_id': session_id,
             'page_name': 'subject_deletion_form'
             })

    @http.route(['/my/subject/deletion/selected/form/<int:task_id>'],
                type='http', auth='user', website=True)
    def portal_student_subject_delete_data(self, task_id=None):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        subject_request_id = request.env[
            'subject.deletion'].sudo().search(
            [('id', '=', task_id)])
        return request.render(
            "odx_portal_student."
            "portal_student_subject_delete_request_data",
            {'subject_request': subject_request_id,
             'page_name': 'subject_deletion_form',
             'student': student_id,
             })

    @http.route(['/delete/subject/form/submit'], type='http', auth="public", website=True)
    def portal_delete_subject_submit(self, **kw):
        student = kw.get('student_id')
        batch = kw.get('batch')
        course = kw.get('course')
        date = kw.get('date')
        event = kw.get('event')
        delete_subject_list = request.httprequest.form.getlist('subject_delete_list')
        line_ids_list=[]
        year = kw.get('year')
        semester = kw.get('semester')
        refund = kw.get('refund')
        checkbox = kw.get('addAfterDelCheck')
        if (checkbox == 'on'):
            check = True
        else:
            check = False
        subject_id_list = kw.get('subject_id_list')
        session_id_list = kw.get('session_id_list')
        subject = subject_id_list[:-1].split(",")
        session = session_id_list[:-1].split(",")
        line_id_list = []
        if (check == True):
            for line in range(len(subject)):
                line_id_list.append((0, 0, {'subject_id': int(subject[line]), 'session_id': int(session[line])}))
        delete_subject = request.env['subject.deletion'].sudo().create({
            'student_id': int(student),
            'batch_id': int(batch),
            'course_id': int(course),
            'date': date,
            'add_after_delete': check,
            'deleted_subject_id': line_ids_list,
            'event': int(event),
            'academic_year': int(year),
            'academic_semester': int(semester),
            'refund_id': int(refund),
            'added_subjects': line_id_list,
        })
        request.env.cr.commit()
        lines_to_delete = delete_subject.subject_ids
        for line_1 in delete_subject.subject_ids:
            if str(line_1.subject_id.id) in delete_subject_list:
                line_1.update({'delete': True})
        delete_subject._get_from_registration()
        delete_subject.action_submit()
        return werkzeug.utils.redirect('/my/subject/deletion/selected/form/%s' % delete_subject.id)

    @http.route(['/onchange/batch/coures/subject/deletion'],
                type='http', auth='user', website=True)
    def portal_ajax_subject_deletion_onchange_request_data(self, **post):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        course_id = post.get('course_id')
        batch_id = post.get('batch_id')
        sub_dict = []
        if course_id and batch_id:
            sub_data = student_id._get_from_registration(student_id.id, course_id, batch_id)
            for sub in sub_data:
                sub_dict.append({
                    'id': sub.id,
                    'name': sub.name
                })
            sub_value = {
                'subject': sub_dict,
            }
            return json.JSONEncoder().encode(sub_value)
