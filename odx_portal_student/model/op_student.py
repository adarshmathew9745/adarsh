from odoo import models, fields, api, _


class OpStudent(models.Model):
    _inherit = 'op.student'

    def _get_from_registration(self, student_id, course_id, batch_id):
        for rec in self:
            registration_id = self.env['op.subject.registration'].search(
                [('student_id', '=', int(student_id)), ('course_id', '=', int(course_id)),
                 ('batch_id', '=', int(batch_id))])
            registration = {}
            if registration_id:
                registration_id = max(registration_id.mapped('id'))
                registration = self.env['op.subject.registration'].browse(registration_id)
            subjects = []
            data = []
            for reg in registration:
                for line in reg.subject_lines:
                    if line.subject_id.id not in subjects:
                        data.append(line.subject_id)
        return data