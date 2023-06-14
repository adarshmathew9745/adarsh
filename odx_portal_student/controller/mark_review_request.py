# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.website.controllers.main import QueryURL
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
import werkzeug.utils
from odoo.osv import expression

PPG = 10


class MarkReviewRequestController(CustomerPortal):

    def get_search_domain_mark_review_request(self, search, attrib_values):
        domain = []
        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike', srch), ('subject', 'ilike', srch),
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

    @http.route(['/student/mark/review/request',
                 '/student/mark/review/request<int:student_id>',
                 '/student/mark/review/request<int:student_id>/page/<int:page>',
                 '/student/mark/review/request<int:page>'],
                type='http', auth='user', website=True)
    def all_mark_review_request(
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
            'in_review': {'label': _('In Review'),
                          'domain': [('state', '=', 'in_review')]},
            'action': {'label': _('Action'),
                       'domain': [('state', '=', 'action')]},
            'reject': {'label': _('Reject'),
                       'domain': [('state', '=', 'reject')]},
            'cancel': {'label': _('Cancel'),
                       'domain': [('state', '=', 'cancel')]},
            'resolve': {'label': _('Resolve'),
                        'domain': [('state', '=', 'resolve')]},
            'close': {'label': _('Close'),
                      'domain': [('state', '=', 'close')]},
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

        domain += self.get_search_domain_mark_review_request(search, attrib_values)
        if student_id:
            keep = QueryURL('/student/mark/review/request/%s' %
                            student_id.id, search=search, amenity=attrib_list,
                            order=post.get('order'))

        else:
            keep = QueryURL('/student/mark/review/request',
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
        domain += [('is_mark_review','=',True)]

        student = request.env["op.student"].sudo().search(
            [('user_id', '=', request.env.user.id)])

        total = request.env['grievance'].sudo().search_count([('student_id', '=', student.id),('is_mark_review','=',True)])
        if student_id:
            pager = portal_pager(
                url="/student/mark/review/request/%s" % student_id.id,
                url_args={'date_begin': date_begin, 'date_end': date_end,
                          'sortby': sortby, 'filterby': filterby,
                          'search': search, 'search_in': search_in},
                total=total,
                page=page,
                step=ppg
            )
        else:
            pager = portal_pager(
                url="/student/mark/review/request",
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
                'grievance'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'grievance'].browse(attributes_ids)

        else:
            subject_registration_id = request.env[
                'grievance'].sudo().search(
                domain, order=order, limit=ppg, offset=pager['offset'])
            attributes = request.env[
                'grievance'].browse(attributes_ids)

        if groupby == 'state':
            grouped_tasks = [
                request.env['grievance'].sudo().concat(*g).search([('student_id', '=', student_id.id),('is_mark_review','=',True)])
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
                'default_url': '/student/mark/review/request',
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
                'page_name': 'mark_review_request_form'

            })
            return request.render(
                'odx_portal_student.all_mark_review_request', val)

    @http.route(['/my/mark_review_request/mark_review_request-form/<int:task_id>'],
                type='http', auth='user', website=True)
    def portal_student_mark_review_request_data(self, task_id=None):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        case_request_id = request.env[
            'grievance'].sudo().search(
            [('id', '=', task_id)])

        return request.render(
            "odx_portal_student."
            "portal_student_mark_review_request_data",
            {'case_request_id': case_request_id,
             'page_name': 'mark_review_request_form',
             'student': student_id,
             })

    @http.route(['/my/mark_review_request/mark_review_request-form'],
                auth='user', website=True, type='http')
    def all_mark_review_request_form(self):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([('user_id', '=', user.id)])
        course_id = request.env['op.course'].sudo().search([])
        batch_id = request.env['op.batch'].sudo().search([])
        faculty_id = request.env['op.faculty'].sudo().search([])
        subject_id = request.env['op.subject'].sudo().search([])
        academic_year_id = request.env['op.academic.year'].sudo().search([])
        academic_term_id = request.env['op.academic.term'].sudo().search([])
        grievance_category_id = request.env['grievance.category'].sudo().search([('parent_id','!=',False)])
        grievance_team_id = request.env['grievance.team'].sudo().search([])
        return request.render(
            'odx_portal_student.mark_review_request_form',
            {
                'student_id': student_id,
                'course_id': course_id,
                'batch_id': batch_id,
                'subject_id': subject_id,
                'faculty_id': faculty_id,
                'academic_year_id': academic_year_id,
                'academic_term_id': academic_term_id,
                'grievance_category_id': grievance_category_id,
                'grievance_team_id': grievance_team_id,
                'page_name': 'mark_review_request_form'
            })

    @http.route(['/my/mark_review_request/mark_review_request-form/submit'], type='http', auth="public", website=True)
    def create_mark_review_request_form(self, **kw):
        name = kw.get('student_id')
        course_type = kw.get('course_type')
        student_number = kw.get('student_number')
        batch_id = kw.get('batch_id')
        academic_year_id = kw.get('academic_year_id')
        academic_term_id = kw.get('academic_term_id')
        grievance_team_id = kw.get('grievance_team_id')
        created_date = kw.get('created_date')
        grievance_category_id = kw.get('grievance_category_id')
        student_classification_id = kw.get('student_classification_id')
        description = kw.get('description')
        subject_id_list = kw.get('subject_id_list')
        faculty_id_list = kw.get('faculty_id_list')
        mark_list = kw.get('mark_list')
        subject=subject_id_list[:-1].split(",")
        faculty=faculty_id_list[:-1].split(",")
        mark=mark_list[:-1].split(",")
        line_ids_list=[]
        for line in range(len(subject)):
            line_ids_list.append((0,0,{'subject_id':subject[line],'faculty_id':faculty[line],'mark':mark[line]}))

        create_mark_review_request = request.env['grievance'].sudo().create({
            "student_id": int(name),
            "grievance_for": 'student',
            "course_id": course_type,
            "student_number": student_number,
            "batch_id": batch_id,
            "academic_year_id": academic_year_id,
            "academic_term_id": academic_term_id,
            "grievance_team_id": int(grievance_team_id),
            "created_date": created_date,
            "grievance_category_id": grievance_category_id,
            "student_classification_id": student_classification_id,
            "description": description,
            "line_ids": line_ids_list,
            "is_mark_review":True,
            "is_academic":True
        })
        create_mark_review_request.submitted_progressbar()
        return werkzeug.utils.redirect('/my/mark_review_request/mark_review_request-form/%s'%create_mark_review_request.id)
