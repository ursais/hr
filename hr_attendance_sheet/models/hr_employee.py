# Copyright 2020 Pavlov Media
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    hours_to_work = fields.Float(
        string='Hours to Work',
        help="""Expected working hours based on company policy. This is used \
             on attendance sheets to calculate overtime values.""")

    use_attendance_sheets = fields.Boolean(
        string="Use Attendance Sheets",
        help="""Used in the attendance sheet auto creation process. Employees \
             that have the 'Hourly' type will have attendance sheets \
             automatically created""")
