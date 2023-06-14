import calendar
from datetime import datetime, date

from odoo.http import request, Response
from odoo.addons.website.controllers.main import QueryURL

from odoo import fields, _
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.osv import expression
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter

class CustomSubjectRegistrationPortal(CustomerPortal):
    @http.route(['/subject/registration/create/',
                 '/subject/registration/create/<int:student_id>',
                 '/subject/registration/create/<int:page>'],
                type='http', auth="user", website=True)
    def portal_craete_subject_registration(self, student_id=None, **kw):
        user = request.env.user
        student_id = request.env['op.student'].sudo().search([
            ('user_id', '=', user.id)])

        elective_subjects = request.env['op.subject'].sudo().search(
            [('subject_type', '=', 'elective')])

        course_ids = request.env['op.course'].sudo().search([])
        events_id = request.env['calendar.events'].sudo().search([])

        lms_module = request.env['ir.module.module'].sudo().search(
            [('name', '=', 'openeducat_lms')])

        if lms_module.state != 'uninstalled':
            course_ids = request.env['op.course'].sudo().search(
                [('online_course', '!=', True)])

        batch_ids = request.env['op.batch'].sudo().search([])

        return request.render(
            "openeducat_core_enterprise."
            "openeducat_create_subject_registration",
            {'student_id': student_id,
             'subject_registration_ids': elective_subjects,
             'course_ids': course_ids,
             'batch_ids': batch_ids,
             'events_id': events_id,
             'page_name': 'subject_reg_form'
             })

    @http.route(['/subject/registration/submit',
                 '/subject/registration/submit/<int:page>'],
                type='http', auth="user", website=True)
    def portal_submit_subject_registration(self, **kw):
        compulsory_subject = request.httprequest. \
            form.getlist('compulsory_subject_ids')
        elective_subject = request.httprequest. \
            form.getlist('elective_subject_ids')
        checkbox=kw['exceed_the_maximum']
        if (checkbox == 'on'):
            check = True
        else:
            check = False

        vals = {
            'student_id': kw['student_id'],
            'course_id': kw['course_id'],
            'batch_id': kw['batch_id'],
            'event': kw['events_id'],
            'exceed_maximum': check,
            'min_unit_load': kw['min_unit_load'],
            'max_unit_load': kw['max_unit_load'],
            'compulsory_subject_ids': [[6, 0, compulsory_subject]],
            'elective_subject_ids': [[6, 0, elective_subject]],
        }
        registration_id = request.env['op.subject.registration']
        registration_id.sudo().create(vals).action_submitted()

        return request.redirect('/subject/registration/')
