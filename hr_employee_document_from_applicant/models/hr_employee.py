# Copyright (C) 2024 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for employee in employees:
            if employee.applicant_id:
                irAttachments = (
                    self.env["ir.attachment"]
                    .sudo()
                    .search(
                        [
                            ("res_model", "=", "hr.applicant"),
                            ("res_id", "=", employee.applicant_id.id),
                        ]
                    )
                )
                for attachment in irAttachments:
                    attachment.res_model = "hr.employee"
                    attachment.res_id = employee.id
        return employees
