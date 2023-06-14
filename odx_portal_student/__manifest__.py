# -*- coding: utf-8 -*-
{
    'name': 'Student Portal',
    'version': '15.0.2',
    'category': 'Education',
    'author': 'Odox SoftHub',
    'website': 'https://www.odoxsofthub.com',
    'support': 'support@odoxsofthub.com',
    'summary': """ Student Portal""",
    'depends': ['portal', 'ag_wasl_suspensions', 'ag_new_admission_custom', 'ag_wasel_attendance', 'openeducat_web', 'openeducat_core_enterprise','openeducat_grievance_enterprise'],
    'data': [
        'views/portal_menu_custom.xml',
        'views/subject_registration_template_inherit.xml',
        'views/suspension_template.xml',
        'views/case_request_template.xml',
        'views/mark_review_request_template.xml',
        'views/retraction_template.xml',
        'views/reenrollment_template.xml',
        'views/service_request_template.xml',
        'views/subject_deletion_template.xml',
        'views/drop_absence_template_view.xml',
        'views/openeducat_subject_registration_portal_inherit.xml',
        'views/student_portal_menu.xml',
    ],
    'license': 'LGPL-3',
    # 'images': ['static/description/thumbnail.gif'],
    'application': True,
    'installable': True,
}