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
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related="employee_id.company_id")

    def _get_attendance_employee_tz(self, date=None):
        """ Convert date according to timezone of user """
        tz = False
        if self.employee_id:
            tz = self.employee_id.tz
        if not date:
            return False
        time_zone = pytz.timezone(tz or 'UTC')
        attendance_dt = datetime.strptime(str(date),
                                          DEFAULT_SERVER_DATETIME_FORMAT)
        attendance_tz_dt = pytz.UTC.localize(attendance_dt)
        attendance_tz_dt = attendance_tz_dt.astimezone(time_zone)
        attendance_tz_date_str = datetime.strftime(
            attendance_tz_dt, DEFAULT_SERVER_DATE_FORMAT)
        return attendance_tz_date_str

    @api.multi
    def write(self, vals):
        """ If the user clocks out after midnight, then it will split the
        attendance at midnight of the employees timezone."""
        for rec in self:
            if 'check_out' in vals:
                check_out = vals.get('check_out')
            else:
                check_out = rec.check_out
            if 'check_in' in vals:
                check_in = vals.get('check_in')
            else:
                check_in = rec.check_in
            if check_in and check_out:
                check_in_date = rec._get_attendance_employee_tz(
                    date=check_in)
                check_out_date = rec._get_attendance_employee_tz(
                    date=check_out)
                if rec.company_id.split_attendance and \
                    check_in_date != check_out_date and \
                        not rec.split_attendance:
                    tz = pytz.timezone(rec.employee_id.tz)
                    current_check_out = tz.localize(
                        datetime.combine(datetime.strptime(
                            str(check_in.date()),
                            DEFAULT_SERVER_DATE_FORMAT),
                            time(23, 59, 59))).astimezone(pytz.utc)
                    new_check_out = check_out
                    new_check_in = tz.localize(datetime.combine(
                        datetime.strptime(
                            check_in_date,
                            DEFAULT_SERVER_DATE_FORMAT) + timedelta(
                            days=1),
                        time(0, 0, 0))).astimezone(pytz.utc)
                    vals.update({'check_out': current_check_out,
                                 'split_attendance': True})
                    self.env['hr.attendance'].sudo().create({
                        'employee_id': rec.employee_id.id,
                        'check_in': new_check_in,
                        'check_out': new_check_out,
                        'split_attendance': False})
        res = super(HrAttendance, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        """ If during creation, check-out crosses overnight, then make sure
        the clock-out is at local midnight to prevent overnight attendances"""
        if 'check_out' in vals and vals.get('check_out', False):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            check_in_date = self._get_attendance_employee_tz(
                date=vals.get('check_in'))
            check_out_date = self._get_attendance_employee_tz(
                date=vals.get('check_out'))
            check_in = datetime.strptime(vals.get('check_in'),
                                         '%Y-%m-%d %H:%M:%S')
            if check_in_date != check_out_date:
                tz = pytz.timezone(employee.tz)
                current_check_out = tz.localize(datetime.combine(
                    datetime.strptime(str(check_in.date()),
                                      DEFAULT_SERVER_DATE_FORMAT),
                    time(23, 59, 59))).astimezone(pytz.utc)
                vals.update({'check_out': current_check_out})
        return super().create(vals)
