# Copyright 2020 Pavlov Media
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, \
    DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError

import pytz
from datetime import datetime, timedelta, time


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    attendance_sheet_id = fields.Many2one(
        'hr.attendance.sheet',
        string="Sheet",
        compute="_compute_attendance_sheet_id",
        store=True)
    duration = fields.Float(
        string="Duration (Hrs)",
        compute="_compute_duration",)
    auto_lunch = fields.Boolean(
        string="Auto Lunch Applied",
        help="If Auto Lunch is enabled and applied on this attendance.")
    split_attendance = fields.Boolean(
        string="Split Attendance",
        help="If attendance was split due to overnight coverage.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        related="attendance_sheet_id.company_id")

    # Get Methods
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

    def _get_attendance_state(self):
        """ Check and raise error if related sheet is not in 'draft' state """
        if self._context.get('allow_modify_confirmed_sheet', False):
            return
        if self.attendance_sheet_id and \
                self.attendance_sheet_id.state == 'locked':
            raise UserError(_(
                "You cannot modify an entry in a locked sheet."
            ))
        elif self.attendance_sheet_id.state == 'done' and \
                self.env.user not in \
                self.attendance_sheet_id._get_possible_reviewers():
            raise UserError(_(
                "You cannot modify an entry in a approved sheet"
            ))
        return True

    # Compute Methods
    @api.depends('employee_id', 'check_in', 'check_out')
    def _compute_attendance_sheet_id(self):
        """ Find and set current sheet in current attendance record """
        for attendance in self:
            sheet_obj = self.env['hr.attendance.sheet']
            check_in = False
            if attendance.check_in:
                check_in = attendance._get_attendance_employee_tz(
                    date=attendance.check_in)
                domain = [('employee_id', '=', attendance.employee_id.id)]
                if check_in:
                    domain += [
                        ('date_start', '<=', check_in),
                        ('date_end', '>=', check_in),
                    ]
                    attendance_sheet_ids = sheet_obj.search(domain, limit=1)
                    attendance.attendance_sheet_id = \
                        attendance_sheet_ids or False

    @api.multi
    def _compute_duration(self):
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
                    self.env['hr.attendance'].sudo().create({
                        'employee_id': rec.employee_id.id,
                        'check_in': new_check_in,
                        'check_out': new_check_out,
                        'split_attendance': False})

                """ Calculate attendance duration """
                date1 = datetime.strptime(str(rec.check_in),
                                          DEFAULT_SERVER_DATETIME_FORMAT)
                date2 = datetime.strptime(str(rec.check_out),
                                          DEFAULT_SERVER_DATETIME_FORMAT)
                time_delta = date2 - date1
                tot_sec = time_delta.total_seconds()
                duration_hour = ("%d.%d" % (tot_sec // 3600,
                                            (tot_sec % 3600) // 60))
                rec.duration = float(duration_hour)

                """ If auto lunch is enabled for the company then adjust the
                duration calculation."""
                if rec.company_id.auto_lunch and \
                        rec.duration > \
                        rec.company_id.auto_lunch_duration != 0.0:
                    rec.duration = float(duration_hour) - \
                                    rec.company_id.auto_lunch_hours
                    rec.write({'auto_lunch': True})
                elif rec.company_id.auto_lunch and rec.auto_lunch:
                    rec.write({'auto_lunch': False})

    # Unlink/Write/Create Methods
    @api.multi
    def unlink(self):
        """ Restrict to delete attendance from confirmed/locked sheet """
        for attendance in self:
            attendance._get_attendance_state()
        return super(HrAttendance, self).unlink()

    @api.multi
    def write(self, vals):
        """ Restrict to write attendance from confirmed/locked sheet."""
        protected_fields = ['employee_id',
                            'check_in',
                            'check_out']
        for attendance in self:
            if attendance.attendance_sheet_id.state in ('locked', 'done') and \
                    any(f in vals.keys() for f in protected_fields):
                attendance._get_attendance_state()
        return super(HrAttendance, self).write(vals)
