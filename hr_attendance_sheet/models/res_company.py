# Copyright 2020 Pavlov Media
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_sheet_range = fields.Selection(
        selection=[('MONTHLY', 'Month'),
                   ('BIWEEKLY', 'Bi-Week'),
                   ('WEEKLY', 'Week'),
                   ('DAILY', 'Day')],
        string='Attendance Sheet Range',
        default='WEEKLY',
        help="The range of your Attendance Sheet.")

    attendance_week_start = fields.Selection(
        selection=[('0', 'Monday'),
                   ('1', 'Tuesday'),
                   ('2', 'Wednesday'),
                   ('3', 'Thursday'),
                   ('4', 'Friday'),
                   ('5', 'Saturday'),
                   ('6', 'Sunday')],
        string='Week Starting Day',
        default='0')

    attendance_sheet_review_policy = fields.Selection(
        string='Attendance Sheet Review Policy',
        selection=[
            ('hr', 'HR Manager/Officer'),
            ('employee_manager', "Employee's Manager"),
            ('hr_or_manager', "HR or Employee's Manager")
        ],
        default='hr',
        help='How Attendance Sheets review is performed.')

    split_attendance = fields.Boolean(
        string="Split Attendance",
        help="Split attendance into two start/end times cross over midnight.")

    auto_lunch = fields.Boolean(
        string="Auto Lunch",
        help="Applies a lunch period if duration is over the max time.")

    auto_lunch_duration = fields.Float(
        string="Duration",
        help="The duration on an attendance that would trigger an auto lunch.")

    auto_lunch_hours = fields.Float(
        string="Lunch Hours",
        help="Enter the lunch period that would be used for an auto lunch.")
