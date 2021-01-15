# Copyright 2020 Pavlov Media
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, \
    DEFAULT_SERVER_DATE_FORMAT

import pytz
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    split_attendance = fields.Boolean(
        string="Split Attendance",
        help="If attendance was split due to overnight coverage.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related="employee_id.company_id", store=True)
    related_attendance_id = fields.Many2one('hr.attendance',
                                            string='Related Attendance')

    @api.model
    def create(self, vals):
        """ Prevent overnight attendance during creation"""
        if vals.get('check_out', False):
            check_in_date = self._get_attendance_employee_tz(
                date=vals.get('check_in'))
            check_out_date = self._get_attendance_employee_tz(
                date=vals.get('check_out'))
            employee = self.env['hr.employee'].browse(vals.get('employee_id'))
            if employee.company_id.split_attendance and \
                    check_in_date != check_out_date:
                raise ValidationError(_("Cannot create attendance that "
                                        "starts and ends on different days."))
        return super().create(vals)

    @api.multi
    def write(self, vals):
        """ If the user clocks out after midnight, then it will split the
        attendance at midnight of the employees timezone."""
        res = super().write(vals)
        for rec in self:
            if rec.check_in and rec.check_out:
                check_in_date = pytz.utc.localize(
                    rec.check_in).astimezone(pytz.timezone(
                        rec.employee_id.tz)).date()
                check_out_date = pytz.utc.localize(
                    rec.check_out).astimezone(pytz.timezone(
                        rec.employee_id.tz)).date()
                if rec.employee_id.company_id.split_attendance and \
                        check_in_date != check_out_date and \
                        not rec.split_attendance:
                    tz = pytz.timezone(rec.employee_id.tz)
                    current_check_out = tz.localize(
                        datetime.combine(datetime.strptime(
                            str(check_in_date),
                            DEFAULT_SERVER_DATE_FORMAT),
                            time(23, 59, 59))).astimezone(pytz.utc)
                    new_check_in = tz.localize(
                        datetime.combine(datetime.strptime(
                            str(pytz.utc.localize(rec.check_in).astimezone(
                                pytz.timezone(rec.employee_id.tz)).date() +
                                timedelta(days=1)),
                            DEFAULT_SERVER_DATE_FORMAT),
                            time(0, 0, 0))).astimezone(pytz.utc)
                    new_check_out = rec.check_out
                    rec.check_out = current_check_out.replace(tzinfo=None)
                    rec.split_attendance = True
                    new_attendance = self.env['hr.attendance'].sudo().create({
                        'employee_id': rec.employee_id.id,
                        'check_in': new_check_in,
                        'related_attendance_id': rec.id,
                        'split_attendance': False})
                    rec.related_attendance_id = new_attendance.id
                    new_attendance.write({'check_out': new_check_out})
        return res
