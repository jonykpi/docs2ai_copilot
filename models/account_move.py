from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    docs2ai_uploaded = fields.Boolean(string='Uploaded to Docs2AI', default=False, readonly=True)
    docs2ai_upload_date = fields.Datetime(string='Docs2AI Upload Date', readonly=True)
    docs2ai_has_scanner_link = fields.Boolean(string='Has Scanner Link', compute='_compute_docs2ai_scanner_link', readonly=True, store=False)
    
    @api.depends()
    def _compute_docs2ai_scanner_link(self):
        """Check if scanner link is configured"""
        scanner_link = self.env['ir.config_parameter'].sudo().get_param('docs2ai.scanner_link', '')
        has_link = bool(scanner_link)
        for record in self:
            record.docs2ai_has_scanner_link = has_link

    def action_upload_to_docs2ai(self):
        """Open wizard to upload PDF/Image to Docs2AI (only for vendor bills)"""
        self.ensure_one()
        # Only allow for vendor bills (not refunds or other types)
        if self.move_type != 'in_invoice':
            raise UserError(_('This feature is only available for vendor bills.'))
        return {
            'name': 'Upload to Docs2AI',
            'type': 'ir.actions.act_window',
            'res_model': 'docs2ai.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
            }
        }
    
    def action_open_scanner_link(self):
        """Open Docs2AI scanner link in new window"""
        self.ensure_one()
        scanner_link = self.env['ir.config_parameter'].sudo().get_param('docs2ai.scanner_link', '')
        if scanner_link:
            return {
                'type': 'ir.actions.act_url',
                'url': scanner_link,
                'target': 'new',
            }
        return False

