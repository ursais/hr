# Copyright 2020 Pavlov Media
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from datetime import datetime


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_sheet_range = fields.Selection(
        selection=[('MONTHLY', 'Month'),
                   ('BIWEEKLY', 'Bi-Week'),
                   ('WEEKLY', 'Week'),
                   ('DAILY', 'Day')],
        string='Attendance Sheet Range',
        default='WEEKLY',
        required=True,
        help="The range of your Attendance Sheet.")

    @api.onchange('attendance_sheet_range')
    def onchange_attendance_sheet_range(self):
        if self.attendance_sheet_range == 'MONTHLY':
            self._origin.write({"date_start": datetime.today().date().replace(day=1)})

    date_start = fields.Date(string="Date From",
                             required=True,
                             index=True)
    date_end = fields.Date(string="Date To",
                           readonly=True,
                           index=True)

    def set_date_end(self, company):
        company = self.browse(company)
        if company.attendance_sheet_range == 'WEEKLY':
            return company.date_start + relativedelta(days=6)
        elif company.attendance_sheet_range == 'BIWEEKLY':
            return company.date_start + relativedelta(days=13)
        else:
            return company.date_start + relativedelta(months=1, day=1, days=-1)

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        if vals.get('date_start') or vals.get('attendance_sheet_range'):
            self.write({'date_end': self.set_date_end(self.id)})
        return res

    @api.multi
    def create(self, vals):
        if vals.get('date_start'):
            vals.update({'date_end': self.set_date_end(vals['id'])})
        return super().write(vals)

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

    auto_lunch = fields.Boolean(
        string="Auto Lunch",
        help="Applies a lunch period if duration is over the max time.")

    auto_lunch_duration = fields.Float(
        string="Duration",
        help="The duration on an attendance that would trigger an auto lunch.")

    auto_lunch_hours = fields.Float(
        string="Lunch Hours",
        help="Enter the lunch period that would be used for an auto lunch.")
