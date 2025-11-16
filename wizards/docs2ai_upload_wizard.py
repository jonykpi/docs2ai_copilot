import base64
import requests
import logging
import mimetypes
import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Allowed file types
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/webp',
]

ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']


class Docs2AIUploadWizard(models.TransientModel):
    _name = 'docs2ai.upload.wizard'
    _description = 'Wizard to upload PDF/Image to Docs2AI'

    invoice_id = fields.Many2one('account.move', string='Vendor Bill', required=True, domain=[('move_type', '=', 'in_invoice')])
    pdf_file = fields.Binary(string='Document File (PDF or Image)', required=True, attachment=True)
    pdf_filename = fields.Char(string='Filename')

    @api.model
    def default_get(self, fields_list):
        """Set default vendor bill from context"""
        res = super().default_get(fields_list)
        if 'invoice_id' in self.env.context:
            invoice_id = self.env.context['invoice_id']
            invoice = self.env['account.move'].browse(invoice_id)
            # Only allow vendor bills (not refunds)
            if invoice.move_type == 'in_invoice':
                res['invoice_id'] = invoice_id
        return res

    def _validate_file_type(self, filename, file_data):
        """Validate that the file is PDF or image"""
        # Check extension
        if filename:
            ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext not in ALLOWED_EXTENSIONS:
                raise UserError(_('Invalid file type. Only PDF and image files (JPG, PNG, GIF, BMP, WEBP) are allowed.'))
        
        # Check MIME type from file data
        mime_type, _ = mimetypes.guess_type(filename or 'file')
        if mime_type and mime_type not in ALLOWED_MIME_TYPES:
            # Try to detect from file header
            if file_data[:4] == b'%PDF':
                mime_type = 'application/pdf'
            elif file_data[:2] == b'\xff\xd8':
                mime_type = 'image/jpeg'
            elif file_data[:8] == b'\x89PNG\r\n\x1a\n':
                mime_type = 'image/png'
            elif file_data[:6] in [b'GIF87a', b'GIF89a']:
                mime_type = 'image/gif'
            elif file_data[:2] == b'BM':
                mime_type = 'image/bmp'
            elif file_data[:4] == b'RIFF' and file_data[8:12] == b'WEBP':
                mime_type = 'image/webp'
            else:
                raise UserError(_('Invalid file type. Only PDF and image files are allowed.'))
        
        return mime_type or 'application/pdf'

    def action_upload(self):
        """Upload PDF/Image to Docs2AI API"""
        self.ensure_one()
        
        if not self.pdf_file:
            raise UserError(_('Please select a file to upload.'))
        
        if not self.invoice_id:
            raise UserError(_('Vendor bill is required.'))
        
        # Ensure this is a vendor bill (not refund or other type)
        if self.invoice_id.move_type != 'in_invoice':
            raise UserError(_('This feature is only available for vendor bills.'))
        
        try:
            # Decode the base64 file
            file_data = base64.b64decode(self.pdf_file)
            filename = self.pdf_filename or 'document.pdf'
            
            # Validate file type
            mime_type = self._validate_file_type(filename, file_data)
            
            # Get API configuration from settings
            api_key = self.env['ir.config_parameter'].sudo().get_param(
                'docs2ai.api_key', 
                default=''
            )
            
            folder_id = self.env['ir.config_parameter'].sudo().get_param(
                'docs2ai.folder_id', 
                default=''
            )
            
            return_url = self.env['ir.config_parameter'].sudo().get_param(
                'docs2ai.return_url',
                default='http://localhost:8069/odoo'
            )
            
            if not api_key:
                raise UserError(_('Docs2AI API Key is not configured. Please configure it in Settings → Docs2AI.'))
            
            if not folder_id:
                raise UserError(_('Folder ID is not configured. Please configure it in Settings → Docs2AI.'))
            
            # Build API URL with folder_id
            api_url = f'https://app.docs2ai.com/api/enterprise/{folder_id}/send-file-doc2ai'
            
            # Prepare the API request
            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            
            # Prepare files for upload - use 'document' as parameter name
            files = {
                'document': (filename, file_data, mime_type)
            }
            
            # Additional data - info must be sent as array using form-data notation
            # API expects: info[platform] = "odoo" (form-data array notation)
            data = {
                'return_url': return_url,
                'info[platform]': 'odoo',  # Form-data array notation
            }
            
            # Make API call
            _logger.info(f'Uploading vendor bill {self.invoice_id.name} to Docs2AI (folder: {folder_id})...')
            _logger.info(f'API URL: {api_url}')
            _logger.info(f'Request headers: {headers}')
            _logger.info(f'Request data: {data}')
            _logger.info(f'File: {filename} ({mime_type})')
            
            response = requests.post(
                api_url,
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            # Log response details
            _logger.info(f'API Response Status Code: {response.status_code}')
            _logger.info(f'API Response Headers: {dict(response.headers)}')
            
            try:
                # Try to parse JSON response
                response_json = response.json()
                _logger.info(f'API Response Body (JSON): {response_json}')
            except (ValueError, requests.exceptions.JSONDecodeError):
                # If not JSON, log as text
                response_text = response.text[:1000]  # Limit to first 1000 chars
                _logger.info(f'API Response Body (Text): {response_text}')
            
            # Check response
            if response.status_code == 200 or response.status_code == 201:
                # Mark vendor bill as uploaded
                self.invoice_id.write({
                    'docs2ai_uploaded': True,
                    'docs2ai_upload_date': fields.Datetime.now(),
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Document successfully uploaded to Docs2AI.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # Log detailed error information
                error_msg = response.text or f'HTTP {response.status_code}'
                _logger.error(f'Docs2AI API Error - Status: {response.status_code}')
                _logger.error(f'Docs2AI API Error - Headers: {dict(response.headers)}')
                _logger.error(f'Docs2AI API Error - Body: {error_msg[:1000]}')  # Limit to first 1000 chars
                raise UserError(_('Failed to upload to Docs2AI: %s') % error_msg)
                
        except requests.exceptions.RequestException as e:
            _logger.error(f'Request exception: {str(e)}')
            raise UserError(_('Error connecting to Docs2AI API: %s') % str(e))
        except Exception as e:
            _logger.error(f'Unexpected error: {str(e)}')
            raise UserError(_('An error occurred: %s') % str(e))
