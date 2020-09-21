# Copyright 2020 Pavlov Media
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, \
    DEFAULT_SERVER_DATE_FORMAT

import pytz
from datetime import datetime, timedelta, time


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    split_attendance = fields.Boolean(
        string="Split Attendance",
        help="If attendance was split due to overnight coverage.")
    need_split = fields.Boolean(
        string="Split Needed",
        compute="_compute_split")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related="employee_id.company_id", store=True)

    def _get_attendance_employee_tz(self, date=None):
        """ Convert date according to timezone of user """
        if not date:
            return False
        tz = False
        if self.employee_id:
            tz = self.employee_id.tz
        time_zone = pytz.timezone(tz or 'UTC')
        attendance_dt = datetime.strptime(str(date),
                                          DEFAULT_SERVER_DATETIME_FORMAT)
        attendance_tz_dt = pytz.UTC.localize(attendance_dt)
        attendance_tz_dt = attendance_tz_dt.astimezone(time_zone)
        attendance_tz_date_str = datetime.strftime(
            attendance_tz_dt, DEFAULT_SERVER_DATE_FORMAT)
        return attendance_tz_date_str

    @api.multi
    def _compute_split(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                """ If split attendance is enabled and less than 2days between
                check-in/out, then split the attendance into two attendances
                with clock out/in at midnight"""
                check_in_date = rec._get_attendance_employee_tz(
                    date=rec.check_in)
                check_out_date = rec._get_attendance_employee_tz(
                    date=rec.check_out)
                if rec.company_id.split_attendance and \
                        check_in_date != check_out_date and \
                        not rec.split_attendance:
                    tz = pytz.timezone(rec.employee_id.tz)
                    current_check_out = tz.localize(
                        datetime.combine(datetime.strptime(
                            str(rec.check_in.date()),
                            DEFAULT_SERVER_DATE_FORMAT),
                            time(23, 59, 59))).astimezone(pytz.utc)
                    new_check_out = rec.check_out
                    new_check_in = tz.localize(datetime.combine(
                        datetime.strptime(
                            check_in_date,
                            DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=1),
                        time(0, 0, 0))).astimezone(pytz.utc)
                    rec.write({'check_out': current_check_out,
                               'split_attendance': True})
                    rec.need_split = True
                    self.env['hr.attendance'].sudo().create({
                        'employee_id': rec.employee_id.id,
                        'check_in': new_check_in,
                        'check_out': new_check_out,
                        'split_attendance': False})
