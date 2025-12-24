import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    docs2ai_copiloted = fields.Boolean(string='Uploaded to Docs2AI', compute='_compute_docs2ai_copiloted', readonly=True, store=False)
    docs2ai_copilot_date = fields.Datetime(string='Docs2AI Upload Date', compute='_compute_docs2ai_copiloted', readonly=True, store=False)
    docs2ai_has_scanner_link = fields.Boolean(string='Has Scanner Link', compute='_compute_docs2ai_scanner_link', readonly=True, store=False)
    
    @api.depends('account_move_id')
    def _compute_docs2ai_copiloted(self):
        """Check if the associated account move has been uploaded to Docs2AI"""
        for record in self:
            if record.account_move_id:
                record.docs2ai_copiloted = record.account_move_id.docs2ai_copiloted
                record.docs2ai_copilot_date = record.account_move_id.docs2ai_copilot_date
            else:
                record.docs2ai_copiloted = False
                record.docs2ai_copilot_date = False
    
    @api.depends()
    def _compute_docs2ai_scanner_link(self):
        """Check if scanner link is configured"""
        scanner_link = self.env['ir.config_parameter'].sudo().get_param('docs2ai.scanner_link', '')
        has_link = bool(scanner_link)
        for record in self:
            record.docs2ai_has_scanner_link = has_link

    def action_upload_to_docs2ai(self):
        """Open wizard to upload PDF/Image to Docs2AI"""
        # Handle list view header button (no records selected) - allow upload without expense
        if not self:
            return {
                'name': 'Upload to Docs2AI',
                'type': 'ir.actions.act_window',
                'res_model': 'docs2ai.upload.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_upload_type': 'expense',  # Set type from context
                },
            }
        
        # Handle both single record and multiple records from list view
        if len(self) == 1:
            # Single record - open wizard with expense pre-selected
            self.ensure_one()
            return {
                'name': 'Upload to Docs2AI',
                'type': 'ir.actions.act_window',
                'res_model': 'docs2ai.upload.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_expense_id': self.id,
                }
            }
        else:
            # Multiple records - open wizard for first selected expense
            return self[0].action_upload_to_docs2ai()
    
    def action_open_scanner_link(self):
        """Open Docs2AI scanner link in new window"""
        # For list view, just open the scanner link (doesn't need specific record)
        scanner_link = self.env['ir.config_parameter'].sudo().get_param('docs2ai.scanner_link', '')
        if scanner_link:
            return {
                'type': 'ir.actions.act_url',
                'url': scanner_link,
                'target': 'new',
            }
        return False



