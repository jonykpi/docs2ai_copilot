import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    docs2ai_copiloted = fields.Boolean(string='Uploaded to Docs2AI', default=False, readonly=True)
    docs2ai_copilot_date = fields.Datetime(string='Docs2AI Upload Date', readonly=True)
    docs2ai_has_scanner_link = fields.Boolean(string='Has Scanner Link', compute='_compute_docs2ai_scanner_link', readonly=True, store=False)
    
    @api.depends()
    def _compute_docs2ai_scanner_link(self):
        """Check if scanner link is configured"""
        scanner_link = self.env['ir.config_parameter'].sudo().get_param('docs2ai.scanner_link', '')
        has_link = bool(scanner_link)
        for record in self:
            record.docs2ai_has_scanner_link = has_link

    def _is_expense_move(self):
        """Check if this account move is related to expenses"""
        return bool(self.expense_ids)
    
    def _get_docs2ai_type(self):
        """Get the type for Docs2AI upload: 'vendor_bill' or 'expense'"""
        if self._is_expense_move():
            return 'expense'
        elif self.move_type == 'in_invoice':
            return 'vendor_bill'
        return None
    
    def action_upload_to_docs2ai(self):
        """Open wizard to upload PDF/Image to Docs2AI"""
        # Handle list view header button (no records selected) - allow upload without bill
        if not self:
            # Determine type from active model or move_type in context
            upload_type = 'vendor_bill'  # Default for account.move
            if self.env.context.get('default_move_type') == 'in_invoice':
                upload_type = 'vendor_bill'
            return {
                'name': 'Upload to Docs2AI',
                'type': 'ir.actions.act_window',
                'res_model': 'docs2ai.upload.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_upload_type': upload_type,  # Set type from context
                },
            }
        
        # Handle both single record and multiple records from list view
        if len(self) == 1:
            # Single record - open wizard with bill/expense pre-selected
            self.ensure_one()
            # Check if it's a vendor bill or expense move
            docs2ai_type = self._get_docs2ai_type()
            if not docs2ai_type:
                raise UserError(_('This feature is only available for vendor bills or expenses.'))
            
            context = {}
            if docs2ai_type == 'vendor_bill':
                context['default_invoice_id'] = self.id
            elif docs2ai_type == 'expense':
                # Use the first expense if multiple exist
                expense = self.expense_ids[0] if self.expense_ids else None
                if expense:
                    context['default_expense_id'] = expense.id
            
            return {
                'name': 'Upload to Docs2AI',
                'type': 'ir.actions.act_window',
                'res_model': 'docs2ai.upload.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
        else:
            # Multiple records - open wizard for first selected vendor bill or expense
            valid_moves = self.filtered(lambda m: m._get_docs2ai_type() is not None)
            if not valid_moves:
                raise UserError(_('Please select at least one vendor bill or expense.'))
            return valid_moves[0].action_upload_to_docs2ai()
    
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

    @api.model
    def docs2ai_get_verification_status(self):
        """Fetch pending verification count and running flag from Docs2AI."""
        params = self.env['ir.config_parameter'].sudo()
        api_key = (params.get_param('docs2ai.api_key') or '').strip()
        folder_id = (params.get_param('docs2ai.folder_id') or '').strip()

        if not api_key or not folder_id:
            _logger.warning('Docs2AI status skipped: missing api_key or folder_id (api: %s, folder: %s)', bool(api_key), bool(folder_id))
            return {
                'success': False,
                'message': _('Docs2AI API key or folder ID is not configured.'),
                'total_pending': 0,
                'is_running': False,
            }
            

        base_url = f'http://backend.test/api/enterprise/{folder_id}/get-progress-status'
        headers = {
            'Authorization': api_key,
            'Accept': 'application/json',
        }

        _logger.info('Docs2AI: Requesting status for folder %s at %s', folder_id, base_url)
        response_json = {}
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            _logger.info('Docs2AI: Response status code: %s', response.status_code)
            response.raise_for_status()
            if response.content:
                response_json = response.json()
                _logger.info('Docs2AI: Status response: %s', response_json)
        except (ValueError, requests.exceptions.JSONDecodeError):
            _logger.warning('Docs2AI get-progress-status response is not JSON.')
            response_json = {}
        except requests.RequestException as exc:
            _logger.warning('Failed to fetch Docs2AI verification status: %s', exc)
            return {
                'success': False,
                'message': str(exc),
                'total_pending': 0,
                'is_running': False,
            }

        data = response_json.get('data') if isinstance(response_json, dict) else {}
        total_pending = 0
        is_running = False

        if isinstance(data, dict):
            total_pending = int(data.get('total_pending') or 0)
            is_running = bool(data.get('is_running'))
        elif isinstance(data, list):
            total_pending = len(data)
            is_running = any(
                isinstance(item, dict) and item.get('status') in {'pending', 'in_progress'}
                for item in data
            )

        return {
            'success': True,
            'message': response_json.get('message') if isinstance(response_json, dict) else '',
            'total_pending': total_pending,
            'is_running': is_running,
        }

