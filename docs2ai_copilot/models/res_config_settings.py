import requests
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    docs2ai_api_key = fields.Char(
        string='Docs2AI API Key',
        config_parameter='docs2ai.api_key',
        help='API key for Docs2AI authentication'
    )
    
    docs2ai_folder_id = fields.Char(
        string='Folder ID',
        config_parameter='docs2ai.folder_id',
        help='Folder ID where documents will be uploaded (e.g., 2589). Will be validated on save.'
    )
    
    docs2ai_folder_name = fields.Char(
        string='Folder Name',
        config_parameter='docs2ai.folder_name',
        readonly=True,
        help='Folder name from Docs2AI (auto-filled after validation)'
    )
    
    docs2ai_scanner_link = fields.Char(
        string='Scanner Link',
        config_parameter='docs2ai.scanner_link',
        readonly=True,
        help='Scanner link for this folder (auto-filled after validation)'
    )
    
    docs2ai_return_url = fields.Char(
        string='Return URL',
        config_parameter='docs2ai.return_url',
        default='http://localhost:8069/odoo',
        help='Return URL after document processing'
    )

    def set_values(self):
        """Override to validate folder_id before saving"""
        # Get current and new values
        current_folder_id = self.env['ir.config_parameter'].sudo().get_param('docs2ai.folder_id', '')
        new_folder_id = self.docs2ai_folder_id
        api_key = self.docs2ai_api_key
        # Only validate if folder_id changed and is provided
        if new_folder_id and new_folder_id != current_folder_id and api_key:
            try:
                # Call API to validate folder_id BEFORE saving
                api_url = f'https://app.docs2ai.com/api/enterprise/{new_folder_id}/get-scanner-link'
                headers = {
                    'Authorization': f'Bearer {api_key}'
                }
                
                _logger.info(f'Validating folder_id {new_folder_id} with Docs2AI API...')
                response = requests.get(api_url, headers=headers, timeout=10)
                
                if response.status_code == 404:
                    # Folder not found - don't save folder_id
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('message', 'Folder not found')
                    _logger.error(f'Folder validation failed: {error_msg}')
                    # Revert folder_id to current value
                    self.docs2ai_folder_id = current_folder_id
                    raise UserError(_('Folder validation failed: %s. Folder ID was not saved.') % error_msg)
                
                elif response.status_code == 200:
                    # Success - parse response and prepare to save
                    response_data = response.json()
                    _logger.info(f'API Response: {response_data}')
                    
                    if response_data.get('status') == 'success':
                        folder_name = response_data.get('folder_name', '')
                        scanner_link = response_data.get('scanner_link', '')
                        
                        # Log the scanner link format
                        _logger.info(f'Scanner link received: {scanner_link}')
                        
                        # Update fields so they get saved
                        self.docs2ai_folder_name = folder_name
                        self.docs2ai_scanner_link = scanner_link
                        
                        _logger.info(f'Folder validated successfully: {folder_name}, Scanner link saved')
                    else:
                        error_msg = response_data.get('message', 'Unknown error')
                        self.docs2ai_folder_id = current_folder_id
                        raise UserError(_('Folder validation failed: %s. Folder ID was not saved.') % error_msg)
                else:
                    # Other error
                    error_msg = response.text or f'HTTP {response.status_code}'
                    _logger.error(f'Folder validation error: {error_msg}')
                    self.docs2ai_folder_id = current_folder_id
                    raise UserError(_('Error validating folder: %s. Folder ID was not saved.') % error_msg)
                    
            except requests.exceptions.RequestException as e:
                _logger.error(f'Request exception during folder validation: {str(e)}')
                self.docs2ai_folder_id = current_folder_id
                raise UserError(_('Error connecting to Docs2AI API: %s. Folder ID was not saved.') % str(e))
            except Exception as e:
                _logger.error(f'Unexpected error during folder validation: {str(e)}')
                if isinstance(e, UserError):
                    raise
                self.docs2ai_folder_id = current_folder_id
                raise UserError(_('An error occurred: %s. Folder ID was not saved.') % str(e))
        elif not new_folder_id:
            # Folder ID cleared - clear folder info
            self.docs2ai_folder_name = ''
            self.docs2ai_scanner_link = ''
        
        # Call parent to save all values (including validated folder_id)
        super().set_values()
