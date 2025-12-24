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


class Docs2AIFileAttachment(models.TransientModel):
    _name = 'docs2ai.file.attachment'
    _description = 'File attachment for Docs2AI upload'

    wizard_id = fields.Many2one('docs2ai.upload.wizard', string='Wizard', required=True, ondelete='cascade')
    file_data = fields.Binary(string='File', required=True, attachment=True)
    filename = fields.Char(string='Filename', required=True)
    upload_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status', default='pending', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)

    @api.onchange('file_data')
    def _onchange_file_data(self):
        """Auto-populate filename when file is selected"""
        if self.file_data and not self.filename:
            # Try to get filename from attachment
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id)
            ], limit=1, order='id desc')
            if attachment and attachment.name:
                self.filename = attachment.name
            else:
                self.filename = 'document.pdf'


class Docs2AIUploadWizard(models.TransientModel):
    _name = 'docs2ai.upload.wizard'
    _description = 'Wizard to upload PDF/Image to Docs2AI'

    invoice_id = fields.Many2one('account.move', string='Vendor Bill (Optional)', required=False, domain=[('move_type', '=', 'in_invoice')])
    expense_id = fields.Many2one('hr.expense', string='Expense (Optional)', required=False)
    upload_type = fields.Selection([
        ('vendor_bill', 'Vendor Bill'),
        ('expense', 'Expense'),
    ], string='Type', default=False, readonly=False)
    pdf_file = fields.Binary(string='Document File (PDF or Image)', attachment=True, help='Single file upload (legacy support)')
    pdf_filename = fields.Char(string='Filename')
    file_ids = fields.One2many('docs2ai.file.attachment', 'wizard_id', string='Files to Upload')

    @api.onchange('invoice_id', 'expense_id')
    def _onchange_upload_type(self):
        """Update upload type when invoice_id or expense_id changes"""
        if self.expense_id:
            self.upload_type = 'expense'
        elif self.invoice_id:
            self.upload_type = 'vendor_bill'
        # Don't override if already set from context (for header button clicks)
        # Only clear if both are None and upload_type was set from these fields

    @api.model
    def default_get(self, fields_list):
        """Set default vendor bill or expense from context"""
        res = super().default_get(fields_list)
        if 'invoice_id' in self.env.context:
            invoice_id = self.env.context['invoice_id']
            invoice = self.env['account.move'].browse(invoice_id)
            # Only allow vendor bills (not refunds)
            if invoice.move_type == 'in_invoice':
                res['invoice_id'] = invoice_id
        if 'expense_id' in self.env.context:
            expense_id = self.env.context['expense_id']
            expense = self.env['hr.expense'].browse(expense_id)
            if expense.exists():
                res['expense_id'] = expense_id
        # Set upload_type from context if provided (for header button clicks)
        if 'default_upload_type' in self.env.context:
            res['upload_type'] = self.env.context['default_upload_type']
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

    def _upload_single_file(self, file_data, filename, api_key, folder_id, return_url, upload_type=None):
        """Upload a single file to Docs2AI API"""
        # Validate file type
        mime_type = self._validate_file_type(filename, file_data)
        
        # Build API URL with folder_id
        api_url = f'http://backend.test/api/enterprise/{folder_id}/send-file-doc2ai'
        
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
        
        # Add type parameter if provided (vendor or expenses)
        if upload_type:
            # Map internal type to API type
            if upload_type == 'vendor_bill':
                data['type'] = 'vendor'
            elif upload_type == 'expense':
                data['type'] = 'expenses'
        
        # Make API call
        api_type = data.get('type', 'N/A')
        _logger.info(f'Uploading file {filename} to Docs2AI (folder: {folder_id}, type: {api_type})...')
        _logger.info(f'API URL: {api_url}')
        _logger.info(f'File: {filename} ({mime_type})')
        _logger.info(f'Upload type: {upload_type} -> API type: {api_type}')
        
        response = requests.post(
            api_url,
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        # Log response details
        _logger.info(f'API Response Status Code: {response.status_code}')
        
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
            return True, None
        else:
            error_msg = response.text or f'HTTP {response.status_code}'
            _logger.error(f'Docs2AI API Error - Status: {response.status_code}')
            _logger.error(f'Docs2AI API Error - Body: {error_msg[:1000]}')
            return False, error_msg

    def action_upload(self):
        """Upload PDF/Image(s) to Docs2AI API"""
        self.ensure_one()
        
        # Collect files to upload
        files_to_upload = []
        
        # Check for multiple files first (new way)
        if self.file_ids:
            for file_attachment in self.file_ids:
                if file_attachment.file_data:
                    file_data = base64.b64decode(file_attachment.file_data)
                    files_to_upload.append({
                        'data': file_data,
                        'filename': file_attachment.filename or 'document.pdf',
                        'attachment': file_attachment
                    })
        
        # Fallback to single file (legacy support)
        elif self.pdf_file:
            file_data = base64.b64decode(self.pdf_file)
            files_to_upload.append({
                'data': file_data,
                'filename': self.pdf_filename or 'document.pdf',
                'attachment': None
            })
        
        if not files_to_upload:
            raise UserError(_('Please select at least one file to upload.'))
        
        # Determine upload type - check expense_id or invoice_id directly
        upload_type = None
        self.ensure_one()
        
        # Check expense_id first
        if self.expense_id:
            upload_type = 'expense'
            # Update the field for consistency
            if self.upload_type != 'expense':
                self.upload_type = 'expense'
            _logger.info(f'Upload type determined from expense_id: {self.expense_id.id} -> {upload_type}')
        # Then check invoice_id
        elif self.invoice_id:
            # Ensure this is a vendor bill (not refund or other type)
            if self.invoice_id.move_type != 'in_invoice':
                raise UserError(_('This feature is only available for vendor bills.'))
            upload_type = 'vendor_bill'
            # Update the field for consistency
            if self.upload_type != 'vendor_bill':
                self.upload_type = 'vendor_bill'
            _logger.info(f'Upload type determined from invoice_id: {self.invoice_id.id} -> {upload_type}')
        # Fallback: use upload_type field (set from context for header button clicks)
        elif self.upload_type:
            upload_type = self.upload_type
            _logger.info(f'Upload type determined from upload_type field: {upload_type}')
        else:
            _logger.warning(f'No upload_type determined: expense_id={self.expense_id.id if self.expense_id else None}, invoice_id={self.invoice_id.id if self.invoice_id else None}, upload_type={self.upload_type}')
            # Try to determine from active model in context
            active_model = self.env.context.get('active_model')
            if active_model == 'hr.expense':
                upload_type = 'expense'
                self.upload_type = 'expense'
                _logger.info(f'Upload type determined from active_model (hr.expense): {upload_type}')
            elif active_model == 'account.move':
                upload_type = 'vendor_bill'
                self.upload_type = 'vendor_bill'
                _logger.info(f'Upload type determined from active_model (account.move): {upload_type}')
        
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
        
        # Upload all files
        success_count = 0
        failed_count = 0
        errors = []
        
        for file_info in files_to_upload:
            try:
                success, error_msg = self._upload_single_file(
                    file_info['data'],
                    file_info['filename'],
                    api_key,
                    folder_id,
                    return_url,
                    upload_type
                )
                
                if success:
                    success_count += 1
                    if file_info['attachment']:
                        file_info['attachment'].write({
                            'upload_status': 'success'
                        })
                else:
                    failed_count += 1
                    error_text = error_msg or _('Unknown error')
                    errors.append(f"{file_info['filename']}: {error_text}")
                    if file_info['attachment']:
                        file_info['attachment'].write({
                            'upload_status': 'failed',
                            'error_message': error_text
                        })
                        
            except Exception as e:
                failed_count += 1
                error_text = str(e)
                errors.append(f"{file_info['filename']}: {error_text}")
                _logger.error(f'Error uploading {file_info["filename"]}: {error_text}')
                if file_info['attachment']:
                    file_info['attachment'].write({
                        'upload_status': 'failed',
                        'error_message': error_text
                    })
        
        # Mark vendor bill or expense move as uploaded if at least one file succeeded
        if success_count > 0:
            if self.invoice_id:
                self.invoice_id.write({
                    'docs2ai_copiloted': True,
                    'docs2ai_copilot_date': fields.Datetime.now(),
                })
            elif self.expense_id and self.expense_id.account_move_id:
                # Mark the account move associated with the expense
                self.expense_id.account_move_id.write({
                    'docs2ai_copiloted': True,
                    'docs2ai_copilot_date': fields.Datetime.now(),
                })
        
        # Prepare notification message
        if failed_count == 0:
            # All successful
            message = _('Successfully uploaded %d file(s) to Docs2AI.') % success_count
            notification_type = 'success'
        elif success_count == 0:
            # All failed
            error_details = '\n'.join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_details += f'\n... and {len(errors) - 5} more error(s)'
            raise UserError(_('Failed to upload all files to Docs2AI:\n\n%s') % error_details)
        else:
            # Partial success
            message = _('Uploaded %d file(s) successfully, %d failed.') % (success_count, failed_count)
            notification_type = 'warning'
            if errors:
                error_details = '\n'.join(errors[:3])  # Show first 3 errors
                if len(errors) > 3:
                    error_details += f'\n... and {len(errors) - 3} more error(s)'
                message += f'\n\nErrors:\n{error_details}'
        
        # Return action to close wizard, show notification, and refresh page
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Upload Complete'),
                'message': message,
                'type': notification_type,
                'sticky': failed_count > 0,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            }
        }
    
    def action_add_file(self):
        """Add a new file attachment line"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add File'),
            'res_model': 'docs2ai.file.attachment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_wizard_id': self.id,
            }
        }
