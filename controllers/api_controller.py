import logging
import json
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class Docs2AIApiController(http.Controller):
    """REST API Controller for Docs2AI module"""

    @http.route('/api/customers', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_customers(self, limit=100, offset=0, **kwargs):
        """
        Get list of customers
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :return: JSON response with customer list
        """
        try:
            # Convert limit and offset to integers
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            # Search for customers (partners with customer_rank > 0)
            customers = request.env['res.partner'].sudo().search([
                ('customer_rank', '>', 0)
            ], limit=limit, offset=offset, order='id desc')
            
            result = []
            for customer in customers:
                result.append({
                    'id': customer.id,
                    'name': customer.name,
                    'email': customer.email or '',
                    'phone': customer.phone or '',
                    'mobile': getattr(customer, 'mobile', '') or '',
                    'street': customer.street or '',
                    'street2': customer.street2 or '',
                    'city': customer.city or '',
                    'state_id': customer.state_id.name if customer.state_id else '',
                    'zip': customer.zip or '',
                    'country_id': customer.country_id.name if customer.country_id else '',
                    'vat': customer.vat or '',
                    'is_company': customer.is_company,
                    'customer_rank': customer.customer_rank,
                })
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': request.env['res.partner'].sudo().search_count([('customer_rank', '>', 0)]),
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing customers: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/customers', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_customer(self, **kwargs):
        """
        Create a new customer
        
        Expected JSON body:
        {
            "name": "Customer Name",
            "email": "customer@example.com",
            "phone": "+1234567890",
            "street": "Street Address",
            "city": "City",
            "zip": "12345",
            "country_id": "Country Name",
            "vat": "VAT Number",
            "is_company": true/false
        }
        
        :return: JSON response with created customer data
        """
        try:
            # Parse JSON from request body for HTTP type
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            # Prepare partner values
            vals = {
                'name': data.get('name'),
                'customer_rank': 1,  # Set as customer
            }
            
            # Optional fields
            if 'email' in data:
                vals['email'] = data['email']
            if 'phone' in data:
                vals['phone'] = data['phone']
            if 'mobile' in data and hasattr(request.env['res.partner'], 'mobile'):
                vals['mobile'] = data['mobile']
            if 'street' in data:
                vals['street'] = data['street']
            if 'street2' in data:
                vals['street2'] = data['street2']
            if 'city' in data:
                vals['city'] = data['city']
            if 'zip' in data:
                vals['zip'] = data['zip']
            if 'vat' in data:
                vals['vat'] = data['vat']
            if 'is_company' in data:
                vals['is_company'] = data['is_company']
            
            # Handle country
            if 'country_id' in data:
                country = request.env['res.country'].sudo().search([
                    '|', ('name', '=', data['country_id']),
                    ('code', '=', data['country_id'])
                ], limit=1)
                if country:
                    vals['country_id'] = country.id
            
            # Handle state
            if 'state_id' in data and vals.get('country_id'):
                state = request.env['res.country.state'].sudo().search([
                    ('name', '=', data['state_id']),
                    ('country_id', '=', vals['country_id'])
                ], limit=1)
                if state:
                    vals['state_id'] = state.id
            
            # Validate required fields
            if not vals.get('name'):
                error_response = {
                    'status': 'error',
                    'message': 'Name is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Create customer
            customer = request.env['res.partner'].sudo().create(vals)
            
            response_data = {
                'status': 'success',
                'message': 'Customer created successfully',
                'data': {
                    'id': customer.id,
                    'name': customer.name,
                    'email': customer.email or '',
                    'phone': customer.phone or '',
                    'mobile': getattr(customer, 'mobile', '') or '',
                    'street': customer.street or '',
                    'street2': customer.street2 or '',
                    'city': customer.city or '',
                    'state_id': customer.state_id.name if customer.state_id else '',
                    'zip': customer.zip or '',
                    'country_id': customer.country_id.name if customer.country_id else '',
                    'vat': customer.vat or '',
                    'is_company': customer.is_company,
                    'customer_rank': customer.customer_rank,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating customer: {str(e)}")
            error_response = {
                'status': 'error',
                'message': 'Invalid JSON in request body'
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except ValidationError as e:
            _logger.error(f"Validation error creating customer: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except Exception as e:
            _logger.error(f"Error creating customer: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/vendors', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_vendors(self, limit=100, offset=0, **kwargs):
        """
        Get list of vendors
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :return: JSON response with vendor list
        """
        try:
            # Convert limit and offset to integers
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            # Search for vendors (partners with supplier_rank > 0)
            vendors = request.env['res.partner'].sudo().search([
                ('supplier_rank', '>', 0)
            ], limit=limit, offset=offset, order='id desc')
            
            result = []
            for vendor in vendors:
                result.append({
                    'id': vendor.id,
                    'name': vendor.name,
                    'email': vendor.email or '',
                    'phone': vendor.phone or '',
                    'mobile': getattr(vendor, 'mobile', '') or '',
                    'street': vendor.street or '',
                    'street2': vendor.street2 or '',
                    'city': vendor.city or '',
                    'state_id': vendor.state_id.name if vendor.state_id else '',
                    'zip': vendor.zip or '',
                    'country_id': vendor.country_id.name if vendor.country_id else '',
                    'vat': vendor.vat or '',
                    'is_company': vendor.is_company,
                    'supplier_rank': vendor.supplier_rank,
                })
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': request.env['res.partner'].sudo().search_count([('supplier_rank', '>', 0)]),
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing vendors: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/vendors', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_vendor(self, **kwargs):
        """
        Create a new vendor
        
        Expected JSON body:
        {
            "name": "Vendor Name",
            "email": "vendor@example.com",
            "phone": "+1234567890",
            "street": "Street Address",
            "city": "City",
            "zip": "12345",
            "country_id": "Country Name",
            "vat": "VAT Number",
            "is_company": true/false
        }
        
        :return: JSON response with created vendor data
        """
        try:
            # Parse JSON from request body for HTTP type
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            # Prepare partner values
            vals = {
                'name': data.get('name'),
                'supplier_rank': 1,  # Set as vendor
            }
            
            # Optional fields
            if 'email' in data:
                vals['email'] = data['email']
            if 'phone' in data:
                vals['phone'] = data['phone']
            if 'mobile' in data and hasattr(request.env['res.partner'], 'mobile'):
                vals['mobile'] = data['mobile']
            if 'street' in data:
                vals['street'] = data['street']
            if 'street2' in data:
                vals['street2'] = data['street2']
            if 'city' in data:
                vals['city'] = data['city']
            if 'zip' in data:
                vals['zip'] = data['zip']
            if 'vat' in data:
                vals['vat'] = data['vat']
            if 'is_company' in data:
                vals['is_company'] = data['is_company']
            
            # Handle country
            if 'country_id' in data:
                country = request.env['res.country'].sudo().search([
                    '|', ('name', '=', data['country_id']),
                    ('code', '=', data['country_id'])
                ], limit=1)
                if country:
                    vals['country_id'] = country.id
            
            # Handle state
            if 'state_id' in data and vals.get('country_id'):
                state = request.env['res.country.state'].sudo().search([
                    ('name', '=', data['state_id']),
                    ('country_id', '=', vals['country_id'])
                ], limit=1)
                if state:
                    vals['state_id'] = state.id
            
            # Validate required fields
            if not vals.get('name'):
                error_response = {
                    'status': 'error',
                    'message': 'Name is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Create vendor
            vendor = request.env['res.partner'].sudo().create(vals)
            
            response_data = {
                'status': 'success',
                'message': 'Vendor created successfully',
                'data': {
                    'id': vendor.id,
                    'name': vendor.name,
                    'email': vendor.email or '',
                    'phone': vendor.phone or '',
                    'mobile': getattr(vendor, 'mobile', '') or '',
                    'street': vendor.street or '',
                    'street2': vendor.street2 or '',
                    'city': vendor.city or '',
                    'state_id': vendor.state_id.name if vendor.state_id else '',
                    'zip': vendor.zip or '',
                    'country_id': vendor.country_id.name if vendor.country_id else '',
                    'vat': vendor.vat or '',
                    'is_company': vendor.is_company,
                    'supplier_rank': vendor.supplier_rank,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating vendor: {str(e)}")
            error_response = {
                'status': 'error',
                'message': 'Invalid JSON in request body'
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except ValidationError as e:
            _logger.error(f"Validation error creating vendor: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except Exception as e:
            _logger.error(f"Error creating vendor: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/sales-entries', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_sales_entries(self, limit=100, offset=0, **kwargs):
        """
        Get list of sales entries (customer invoices and credit notes)
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :return: JSON response with sales entries list
        """
        try:
            # Convert limit and offset to integers
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            # Search for sales entries (out_invoice and out_refund)
            sales_entries = request.env['account.move'].sudo().search([
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ], limit=limit, offset=offset, order='id desc')
            
            result = []
            for entry in sales_entries:
                result.append({
                    'id': entry.id,
                    'name': entry.name or '',
                    'move_type': entry.move_type,
                    'move_type_label': dict(entry._fields['move_type'].selection).get(entry.move_type, ''),
                    'partner_id': entry.partner_id.id if entry.partner_id else None,
                    'partner_name': entry.partner_id.name if entry.partner_id else '',
                    'date': entry.date.isoformat() if entry.date else '',
                    'invoice_date': entry.invoice_date.isoformat() if entry.invoice_date else '',
                    'invoice_date_due': entry.invoice_date_due.isoformat() if entry.invoice_date_due else '',
                    'state': entry.state,
                    'amount_total': entry.amount_total,
                    'amount_untaxed': entry.amount_untaxed,
                    'amount_tax': entry.amount_tax,
                    'amount_residual': entry.amount_residual,
                    'currency_id': entry.currency_id.name if entry.currency_id else '',
                    'payment_state': entry.payment_state,
                    'journal_id': entry.journal_id.name if entry.journal_id else '',
                    'company_id': entry.company_id.name if entry.company_id else '',
                })
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': request.env['account.move'].sudo().search_count([('move_type', 'in', ['out_invoice', 'out_refund'])]),
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing sales entries: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/sales-entries', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_sales_entry(self, **kwargs):
        """
        Create a new sales entry (customer invoice)
        
        Expected JSON body:
        {
            "partner_id": 1,
            "invoice_date": "2024-01-15",
            "invoice_date_due": "2024-02-15",
            "invoice_line_ids": [
                {
                    "product_id": 1,
                    "name": "Product Description",
                    "quantity": 1.0,
                    "price_unit": 100.0,
                    "tax_ids": [1, 2]
                }
            ]
        }
        
        :return: JSON response with created sales entry data
        """
        try:
            # Parse JSON from request body for HTTP type
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            # Prepare invoice values
            vals = {
                'move_type': 'out_invoice',  # Customer Invoice
            }
            
            # Required fields
            if 'partner_id' in data:
                vals['partner_id'] = data['partner_id']
            else:
                error_response = {
                    'status': 'error',
                    'message': 'partner_id is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Optional fields
            if 'invoice_date' in data:
                vals['invoice_date'] = data['invoice_date']
            if 'invoice_date_due' in data:
                vals['invoice_date_due'] = data['invoice_date_due']
            if 'journal_id' in data:
                vals['journal_id'] = data['journal_id']
            if 'currency_id' in data:
                currency = request.env['res.currency'].sudo().search([
                    '|', ('name', '=', data['currency_id']),
                    ('id', '=', data['currency_id'])
                ], limit=1)
                if currency:
                    vals['currency_id'] = currency.id
            
            # Invoice lines
            if 'invoice_line_ids' in data:
                line_vals = []
                for line in data['invoice_line_ids']:
                    line_data = {}
                    if 'product_id' in line:
                        line_data['product_id'] = line['product_id']
                    if 'name' in line:
                        line_data['name'] = line['name']
                    if 'quantity' in line:
                        line_data['quantity'] = line['quantity']
                    if 'price_unit' in line:
                        line_data['price_unit'] = line['price_unit']
                    if 'tax_ids' in line:
                        line_data['tax_ids'] = [(6, 0, line['tax_ids'])]
                    if 'account_id' in line:
                        line_data['account_id'] = line['account_id']
                    line_vals.append((0, 0, line_data))
                vals['invoice_line_ids'] = line_vals
            
            # Create invoice
            invoice = request.env['account.move'].sudo().create(vals)
            
            response_data = {
                'status': 'success',
                'message': 'Sales entry created successfully',
                'data': {
                    'id': invoice.id,
                    'name': invoice.name or '',
                    'move_type': invoice.move_type,
                    'partner_id': invoice.partner_id.id if invoice.partner_id else None,
                    'partner_name': invoice.partner_id.name if invoice.partner_id else '',
                    'date': invoice.date.isoformat() if invoice.date else '',
                    'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else '',
                    'state': invoice.state,
                    'amount_total': invoice.amount_total,
                    'amount_untaxed': invoice.amount_untaxed,
                    'amount_tax': invoice.amount_tax,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating sales entry: {str(e)}")
            error_response = {
                'status': 'error',
                'message': 'Invalid JSON in request body'
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except ValidationError as e:
            _logger.error(f"Validation error creating sales entry: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except Exception as e:
            _logger.error(f"Error creating sales entry: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/purchase-entries', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_purchase_entries(self, limit=100, offset=0, **kwargs):
        """
        Get list of purchase entries (vendor bills and credit notes)
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :return: JSON response with purchase entries list
        """
        try:
            # Convert limit and offset to integers
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            # Search for purchase entries (in_invoice and in_refund)
            purchase_entries = request.env['account.move'].sudo().search([
                ('move_type', 'in', ['in_invoice', 'in_refund'])
            ], limit=limit, offset=offset, order='id desc')
            
            result = []
            for entry in purchase_entries:
                result.append({
                    'id': entry.id,
                    'name': entry.name or '',
                    'move_type': entry.move_type,
                    'move_type_label': dict(entry._fields['move_type'].selection).get(entry.move_type, ''),
                    'partner_id': entry.partner_id.id if entry.partner_id else None,
                    'partner_name': entry.partner_id.name if entry.partner_id else '',
                    'date': entry.date.isoformat() if entry.date else '',
                    'invoice_date': entry.invoice_date.isoformat() if entry.invoice_date else '',
                    'invoice_date_due': entry.invoice_date_due.isoformat() if entry.invoice_date_due else '',
                    'state': entry.state,
                    'amount_total': entry.amount_total,
                    'amount_untaxed': entry.amount_untaxed,
                    'amount_tax': entry.amount_tax,
                    'amount_residual': entry.amount_residual,
                    'currency_id': entry.currency_id.name if entry.currency_id else '',
                    'payment_state': entry.payment_state,
                    'journal_id': entry.journal_id.name if entry.journal_id else '',
                    'company_id': entry.company_id.name if entry.company_id else '',
                })
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': request.env['account.move'].sudo().search_count([('move_type', 'in', ['in_invoice', 'in_refund'])]),
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing purchase entries: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/purchase-entries', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_purchase_entry(self, **kwargs):
        """
        Create a new purchase entry (vendor bill)
        
        Expected JSON body:
        {
            "partner_id": 1,
            "invoice_date": "2024-01-15",
            "invoice_date_due": "2024-02-15",
            "invoice_line_ids": [
                {
                    "product_id": 1,
                    "name": "Product Description",
                    "quantity": 1.0,
                    "price_unit": 100.0,
                    "tax_ids": [1, 2]
                }
            ]
        }
        
        :return: JSON response with created purchase entry data
        """
        try:
            # Parse JSON from request body for HTTP type
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            # Prepare bill values
            vals = {
                'move_type': 'in_invoice',  # Vendor Bill
            }
            
            # Required fields
            if 'partner_id' in data:
                vals['partner_id'] = data['partner_id']
            else:
                error_response = {
                    'status': 'error',
                    'message': 'partner_id is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Optional fields
            if 'invoice_date' in data:
                vals['invoice_date'] = data['invoice_date']
            if 'invoice_date_due' in data:
                vals['invoice_date_due'] = data['invoice_date_due']
            if 'journal_id' in data:
                vals['journal_id'] = data['journal_id']
            if 'currency_id' in data:
                currency = request.env['res.currency'].sudo().search([
                    '|', ('name', '=', data['currency_id']),
                    ('id', '=', data['currency_id'])
                ], limit=1)
                if currency:
                    vals['currency_id'] = currency.id
            
            # Invoice lines
            if 'invoice_line_ids' in data:
                line_vals = []
                for line in data['invoice_line_ids']:
                    line_data = {}
                    if 'product_id' in line:
                        line_data['product_id'] = line['product_id']
                    if 'name' in line:
                        line_data['name'] = line['name']
                    if 'quantity' in line:
                        line_data['quantity'] = line['quantity']
                    if 'price_unit' in line:
                        line_data['price_unit'] = line['price_unit']
                    if 'tax_ids' in line:
                        line_data['tax_ids'] = [(6, 0, line['tax_ids'])]
                    if 'account_id' in line:
                        line_data['account_id'] = line['account_id']
                    line_vals.append((0, 0, line_data))
                vals['invoice_line_ids'] = line_vals
            
            # Create bill
            bill = request.env['account.move'].sudo().create(vals)
            
            response_data = {
                'status': 'success',
                'message': 'Purchase entry created successfully',
                'data': {
                    'id': bill.id,
                    'name': bill.name or '',
                    'move_type': bill.move_type,
                    'partner_id': bill.partner_id.id if bill.partner_id else None,
                    'partner_name': bill.partner_id.name if bill.partner_id else '',
                    'date': bill.date.isoformat() if bill.date else '',
                    'invoice_date': bill.invoice_date.isoformat() if bill.invoice_date else '',
                    'state': bill.state,
                    'amount_total': bill.amount_total,
                    'amount_untaxed': bill.amount_untaxed,
                    'amount_tax': bill.amount_tax,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating purchase entry: {str(e)}")
            error_response = {
                'status': 'error',
                'message': 'Invalid JSON in request body'
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except ValidationError as e:
            _logger.error(f"Validation error creating purchase entry: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except Exception as e:
            _logger.error(f"Error creating purchase entry: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/bills', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_bills(self, limit=100, offset=0, **kwargs):
        """
        Get list of vendor bills only (not refunds)
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :return: JSON response with vendor bills list
        """
        try:
            # Convert limit and offset to integers
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            # Search for vendor bills and receipts (in_invoice and in_receipt, not in_refund)
            bills = request.env['account.move'].sudo().search([
                ('move_type', 'in', ['in_invoice', 'in_receipt'])
            ], limit=limit, offset=offset, order='id desc')
            
            result = []
            for bill in bills:
                # Determine type based on move_type
                bill_type = 'receipt' if bill.move_type == 'in_receipt' else 'bill'
                type_label = 'Purchase Receipt' if bill.move_type == 'in_receipt' else 'Vendor Bill'
                
                result.append({
                    'id': bill.id,
                    'name': bill.name or '',
                    'type': bill_type,
                    'move_type': bill.move_type,
                    'move_type_label': type_label,
                    'partner_id': bill.partner_id.id if bill.partner_id else None,
                    'partner_name': bill.partner_id.name if bill.partner_id else '',
                    'date': bill.date.isoformat() if bill.date else '',
                    'invoice_date': bill.invoice_date.isoformat() if bill.invoice_date else '',
                    'invoice_date_due': bill.invoice_date_due.isoformat() if bill.invoice_date_due else '',
                    'state': bill.state,
                    'amount_total': bill.amount_total,
                    'amount_untaxed': bill.amount_untaxed,
                    'amount_tax': bill.amount_tax,
                    'amount_residual': bill.amount_residual,
                    'currency_id': bill.currency_id.name if bill.currency_id else '',
                    'payment_state': bill.payment_state,
                    'journal_id': bill.journal_id.name if bill.journal_id else '',
                    'company_id': bill.company_id.name if bill.company_id else '',
                })
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': request.env['account.move'].sudo().search_count([('move_type', 'in', ['in_invoice', 'in_receipt'])]),
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing bills: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/bills', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_bill(self, **kwargs):
        """
        Create a new vendor bill or receipt
        
        Expected JSON body:
        {
            "type": "bill",  // "bill" or "receipt" (default: "bill")
            "partner_id": 1,
            "bill_name": "BILL/2024/01/0001",  // Optional: custom bill name
            "invoice_date": "2024-01-15",
            "invoice_date_due": "2024-02-15",
            "journal_id": 1,
            "currency_id": "USD",
            "attachment": {
                "name": "document.pdf",
                "data": "base64_encoded_file_data",
                "mimetype": "application/pdf"
            },
            "invoice_line_ids": [
                {
                    "product_id": 1,
                    "name": "Product Description",
                    "quantity": 1.0,
                    "price_unit": 100.0,
                    "tax_ids": [1, 2],
                    "account_id": 1
                }
            ]
        }
        
        :return: JSON response with created vendor bill/receipt data
        """
        try:
            # Parse JSON from request body for HTTP type
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            # Determine move_type based on type field
            bill_type = data.get('type', 'bill').lower()
            if bill_type == 'receipt':
                move_type = 'in_receipt'  # Purchase Receipt
            else:
                move_type = 'in_invoice'  # Vendor Bill (default)
            
            # Prepare bill values
            vals = {
                'move_type': move_type,
            }
            
            # Required fields
            if 'partner_id' in data:
                vals['partner_id'] = data['partner_id']
            else:
                error_response = {
                    'status': 'error',
                    'message': 'partner_id is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Optional fields
            if 'invoice_date' in data:
                vals['invoice_date'] = data['invoice_date']
            if 'invoice_date_due' in data:
                vals['invoice_date_due'] = data['invoice_date_due']
            if 'journal_id' in data:
                vals['journal_id'] = data['journal_id']
            if 'currency_id' in data:
                currency = request.env['res.currency'].sudo().search([
                    '|', ('name', '=', data['currency_id']),
                    ('id', '=', data['currency_id'])
                ], limit=1)
                if currency:
                    vals['currency_id'] = currency.id
            
            # Invoice lines
            if 'invoice_line_ids' in data:
                line_vals = []
                for line in data['invoice_line_ids']:
                    line_data = {}
                    if 'product_id' in line:
                        line_data['product_id'] = line['product_id']
                    if 'name' in line:
                        line_data['name'] = line['name']
                    if 'quantity' in line:
                        line_data['quantity'] = line['quantity']
                    if 'price_unit' in line:
                        line_data['price_unit'] = line['price_unit']
                    if 'tax_ids' in line:
                        line_data['tax_ids'] = [(6, 0, line['tax_ids'])]
                    if 'account_id' in line:
                        line_data['account_id'] = line['account_id']
                    line_vals.append((0, 0, line_data))
                vals['invoice_line_ids'] = line_vals
            
            # Create bill
            bill = request.env['account.move'].sudo().create(vals)
            
            # Handle bill_name if provided (after creation to override auto-generated name)
            if 'bill_name' in data and data['bill_name']:
                bill.write({'name': data['bill_name']})
            
            # Handle attachment if provided
            attachment_id = None
            if 'attachment' in data and data['attachment']:
                attachment_data = data['attachment']
                attachment_name = attachment_data.get('name', 'document.pdf')
                attachment_datas = attachment_data.get('data', '')
                attachment_mimetype = attachment_data.get('mimetype', 'application/pdf')
                
                if attachment_datas:
                    # Create ir.attachment record
                    attachment_vals = {
                        'name': attachment_name,
                        'datas': attachment_datas,
                        'res_model': 'account.move',
                        'res_id': bill.id,
                        'mimetype': attachment_mimetype,
                        'type': 'binary',
                    }
                    attachment = request.env['ir.attachment'].sudo().create(attachment_vals)
                    attachment_id = attachment.id
                    
                    # Post attachment in the chatter
                    bill.message_post(
                        body=_('Document attached from API'),
                        attachment_ids=[attachment.id]
                    )
            
            # Determine type label
            type_label = 'Purchase Receipt' if move_type == 'in_receipt' else 'Vendor Bill'
            
            response_data = {
                'status': 'success',
                'message': f'{type_label} created successfully',
                'data': {
                    'id': bill.id,
                    'name': bill.name or '',
                    'type': bill_type,
                    'move_type': bill.move_type,
                    'move_type_label': type_label,
                    'partner_id': bill.partner_id.id if bill.partner_id else None,
                    'partner_name': bill.partner_id.name if bill.partner_id else '',
                    'date': bill.date.isoformat() if bill.date else '',
                    'invoice_date': bill.invoice_date.isoformat() if bill.invoice_date else '',
                    'state': bill.state,
                    'amount_total': bill.amount_total,
                    'amount_untaxed': bill.amount_untaxed,
                    'amount_tax': bill.amount_tax,
                    'attachment_id': attachment_id,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating bill: {str(e)}")
            error_response = {
                'status': 'error',
                'message': 'Invalid JSON in request body'
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except ValidationError as e:
            _logger.error(f"Validation error creating bill: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except Exception as e:
            _logger.error(f"Error creating bill: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

