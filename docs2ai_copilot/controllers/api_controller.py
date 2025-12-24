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
            
            # Post the bill
            bill.action_post()
            
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
            "currency": "USD",  // ISO currency code (e.g., USD, BDT)
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
                    "tax": 10,  // Tax percentage (e.g., 10 for 10%) - OR use tax_ids: [1, 2]
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
            currency_code = data.get('currency')
            currency_id_value = data.get('currency_id')  # Backward compatibility
            if currency_code:
                currency_code = currency_code.upper()
                currency_env = request.env['res.currency'].sudo().with_context(active_test=False)
                currency = currency_env.search([
                    '|', ('name', '=', currency_code),
                    ('symbol', '=', currency_code)
                ], limit=1)
                if currency:
                    if not currency.active:
                        currency.write({'active': True})
                else:
                    currency_vals = {
                        'name': currency_code,
                        'symbol': currency_code,
                        'rounding': 0.01,
                        'active': True,
                    }
                    if 'decimal_places' in currency_env._fields:
                        currency_vals['decimal_places'] = 2
                    currency = currency_env.create(currency_vals)
                    _logger.info(f'Auto-created currency {currency_code} (ID: {currency.id})')
                vals['currency_id'] = currency.id
            elif currency_id_value:
                currency = request.env['res.currency'].sudo().search([
                    '|', ('name', '=', currency_id_value),
                    ('id', '=', currency_id_value)
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
                    
                    # Handle tax - can be percentage (tax) or tax_ids array
                    if 'tax' in line:
                        # Search for tax by percentage rate for purchase invoices
                        tax_percentage = float(line['tax'])
                        tax = request.env['account.tax'].sudo().search([
                            ('amount', '=', tax_percentage),
                            ('type_tax_use', '=', 'purchase'),  # For vendor bills
                            ('amount_type', '=', 'percent'),
                        ], limit=1)
                        if not tax:
                            # Auto-create tax if not found
                            company = request.env.company
                            # Get tax account from existing purchase tax or find suitable account
                            tax_account = None
                            # Try to get account from default purchase tax
                            if company.account_purchase_tax_id:
                                existing_tax = company.account_purchase_tax_id
                                tax_line = existing_tax.invoice_repartition_line_ids.filtered(
                                    lambda l: l.repartition_type == 'tax'
                                )
                                if tax_line and tax_line[0].account_id:
                                    tax_account = tax_line[0].account_id
                            
                            # If no account found, try to find any expense account
                            if not tax_account:
                                tax_account = request.env['account.account'].sudo().search([
                                    ('account_type', '=', 'expense'),
                                    ('company_id', '=', company.id)
                                ], limit=1)
                            
                            # Create the tax record
                            tax_vals = {
                                'name': f'Tax {tax_percentage}%',
                                'amount': tax_percentage,
                                'amount_type': 'percent',
                                'type_tax_use': 'purchase',
                                'company_id': company.id,
                                'invoice_repartition_line_ids': [
                                    (0, 0, {
                                        'repartition_type': 'base',
                                        'factor_percent': 100.0,
                                    }),
                                    (0, 0, {
                                        'repartition_type': 'tax',
                                        'factor_percent': 100.0,
                                        'account_id': tax_account.id if tax_account else False,
                                    }),
                                ],
                                'refund_repartition_line_ids': [
                                    (0, 0, {
                                        'repartition_type': 'base',
                                        'factor_percent': 100.0,
                                    }),
                                    (0, 0, {
                                        'repartition_type': 'tax',
                                        'factor_percent': 100.0,
                                        'account_id': tax_account.id if tax_account else False,
                                    }),
                                ],
                            }
                            tax = request.env['account.tax'].sudo().create(tax_vals)
                            _logger.info(f'Auto-created tax {tax_percentage}% for purchase invoices (ID: {tax.id})')
                        line_data['tax_ids'] = [(6, 0, [tax.id])]
                    elif 'tax_ids' in line:
                        # Backward compatibility with tax_ids
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
            
            # Post the bill
            bill.action_post()
            
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
                    'currency': bill.currency_id.name if bill.currency_id else '',
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

    # ============================================
    # EXPENSE APIs
    # ============================================

    @http.route('/api/expenses', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_expenses(self, limit=100, offset=0, **kwargs):
        """
        Get list of expenses
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :return: JSON response with expenses list
        """
        try:
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            expenses = request.env['hr.expense'].sudo().search([], limit=limit, offset=offset, order='id desc')
            
            result = []
            for expense in expenses:
                result.append({
                    'id': expense.id,
                    'name': expense.name or '',
                    'employee_id': expense.employee_id.id if expense.employee_id else None,
                    'employee_name': expense.employee_id.name if expense.employee_id else '',
                    'date': expense.date.isoformat() if expense.date else '',
                    'product_id': expense.product_id.id if expense.product_id else None,
                    'product_name': expense.product_id.name if expense.product_id else '',
                    'quantity': expense.quantity,
                    'price_unit': expense.price_unit,
                    'total_amount': expense.total_amount,
                    'total_amount_currency': expense.total_amount_currency,
                    'currency_id': expense.currency_id.name if expense.currency_id else '',
                    'payment_mode': expense.payment_mode,
                    'payment_mode_label': dict(expense._fields['payment_mode'].selection).get(expense.payment_mode, ''),
                    'vendor_id': expense.vendor_id.id if expense.vendor_id else None,
                    'vendor_name': expense.vendor_id.name if expense.vendor_id else '',
                    'manager_id': expense.manager_id.id if expense.manager_id else None,
                    'manager_name': expense.manager_id.name if expense.manager_id else '',
                    'department_id': expense.department_id.id if expense.department_id else None,
                    'department_name': expense.department_id.name if expense.department_id else '',
                    'state': expense.state,
                    'tax_ids': [tax.id for tax in expense.tax_ids],
                    'tax_names': [tax.name for tax in expense.tax_ids],
                    'account_id': expense.account_id.id if expense.account_id else None,
                    'account_name': expense.account_id.name if expense.account_id else '',
                    'company_id': expense.company_id.id if expense.company_id else None,
                    'company_name': expense.company_id.name if expense.company_id else '',
                })
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': request.env['hr.expense'].sudo().search_count([]),
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing expenses: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/expenses', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_expense(self, **kwargs):
        """
        Create a new expense
        
        Expected JSON body:
        {
            "name": "Expense Description",
            "employee_id": 1,
            "date": "2024-01-15",
            "product_id": 1,
            "quantity": 1.0,
            "price_unit": 100.0,
            "total_amount": 100.0,
            "total_amount_currency": 100.0,
            "currency_id": "USD",
            "payment_mode": "own_account",  // "own_account" or "company_account"
            "vendor_id": 1,
            "manager_id": 1,
            "tax_ids": [1, 2],
            "account_id": 1,
            "description": "Internal notes",
            "analytic_distribution": {},
            "attachment": {
                "name": "receipt.pdf",
                "data": "base64_encoded_file_data",
                "mimetype": "application/pdf"
            }
        }
        
        :return: JSON response with created expense data
        """
        try:
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            vals = {}
            
            # Required fields
            if 'name' in data:
                vals['name'] = data['name']
            if 'employee_id' in data:
                vals['employee_id'] = data['employee_id']
            else:
                # Try to get current user's employee
                employee = request.env.user.employee_id
                if employee:
                    vals['employee_id'] = employee.id
                else:
                    error_response = {
                        'status': 'error',
                        'message': 'employee_id is required'
                    }
                    return request.make_response(
                        json.dumps(error_response),
                        headers=[('Content-Type', 'application/json')],
                        status=400
                    )
            
            # Optional fields
            if 'date' in data:
                vals['date'] = data['date']
            # Support both product_id and category_id (category_id is an alias for product_id)
            if 'category_id' in data:
                vals['product_id'] = data['category_id']
            elif 'product_id' in data:
                vals['product_id'] = data['product_id']
            if 'quantity' in data:
                vals['quantity'] = data['quantity']
            if 'price_unit' in data:
                vals['price_unit'] = data['price_unit']
            if 'total_amount' in data:
                vals['total_amount'] = data['total_amount']
            if 'total_amount_currency' in data:
                vals['total_amount_currency'] = data['total_amount_currency']
            if 'payment_mode' in data:
                if data['payment_mode'] in ['own_account', 'company_account']:
                    vals['payment_mode'] = data['payment_mode']
            if 'vendor_id' in data:
                vals['vendor_id'] = data['vendor_id']
            if 'manager_id' in data:
                vals['manager_id'] = data['manager_id']
            if 'account_id' in data:
                vals['account_id'] = data['account_id']
            if 'description' in data:
                vals['description'] = data['description']
            if 'analytic_distribution' in data:
                vals['analytic_distribution'] = data['analytic_distribution']
            
            # Handle currency - support both 'currency' and 'currency_id'
            currency_value = data.get('currency') or data.get('currency_id')
            if currency_value:
                # Try to convert to int if it's a numeric string
                try:
                    currency_id_int = int(currency_value)
                    currency = request.env['res.currency'].sudo().browse(currency_id_int)
                    if currency.exists():
                        vals['currency_id'] = currency.id
                    else:
                        # Search by name if ID doesn't exist
                        currency = request.env['res.currency'].sudo().search([
                            ('name', '=', str(currency_value))
                        ], limit=1)
                        if currency:
                            vals['currency_id'] = currency.id
                except (ValueError, TypeError):
                    # Not a number, search by name
                    currency = request.env['res.currency'].sudo().search([
                        ('name', '=', str(currency_value))
                    ], limit=1)
                    if currency:
                        vals['currency_id'] = currency.id
            
            # Handle taxes
            if 'tax_ids' in data:
                vals['tax_ids'] = [(6, 0, data['tax_ids'])]
            
            # Create expense
            expense = request.env['hr.expense'].sudo().create(vals)
            
            # Handle attachment if provided
            attachment_id = None
            if 'attachment' in data and data['attachment']:
                attachment_data = data['attachment']
                attachment_name = attachment_data.get('name', 'receipt.pdf')
                attachment_datas = attachment_data.get('data', '')
                attachment_mimetype = attachment_data.get('mimetype', 'application/pdf')
                
                if attachment_datas:
                    # Create ir.attachment record
                    attachment_vals = {
                        'name': attachment_name,
                        'datas': attachment_datas,
                        'res_model': 'hr.expense',
                        'res_id': expense.id,
                        'mimetype': attachment_mimetype,
                        'type': 'binary',
                    }
                    attachment = request.env['ir.attachment'].sudo().create(attachment_vals)
                    attachment_id = attachment.id
                    
                    # Set as main attachment
                    expense._message_set_main_attachment_id(attachment, force=True)
                    
                    # Post attachment in the chatter
                    expense.message_post(
                        body=_('Receipt attached from API'),
                        attachment_ids=[attachment.id]
                    )
            
            response_data = {
                'status': 'success',
                'message': 'Expense created successfully',
                'data': {
                    'id': expense.id,
                    'name': expense.name or '',
                    'employee_id': expense.employee_id.id if expense.employee_id else None,
                    'employee_name': expense.employee_id.name if expense.employee_id else '',
                    'date': expense.date.isoformat() if expense.date else '',
                    'product_id': expense.product_id.id if expense.product_id else None,
                    'product_name': expense.product_id.name if expense.product_id else '',
                    'quantity': expense.quantity,
                    'price_unit': expense.price_unit,
                    'total_amount': expense.total_amount,
                    'total_amount_currency': expense.total_amount_currency,
                    'currency_id': expense.currency_id.name if expense.currency_id else '',
                    'payment_mode': expense.payment_mode,
                    'payment_mode_label': dict(expense._fields['payment_mode'].selection).get(expense.payment_mode, ''),
                    'vendor_id': expense.vendor_id.id if expense.vendor_id else None,
                    'vendor_name': expense.vendor_id.name if expense.vendor_id else '',
                    'manager_id': expense.manager_id.id if expense.manager_id else None,
                    'manager_name': expense.manager_id.name if expense.manager_id else '',
                    'state': expense.state,
                    'tax_ids': [tax.id for tax in expense.tax_ids],
                    'attachment_id': attachment_id,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating expense: {str(e)}")
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
            _logger.error(f"Validation error creating expense: {str(e)}")
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
            _logger.error(f"Error creating expense: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    # ============================================
    # TAX APIs
    # ============================================

    @http.route('/api/taxes', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_taxes(self, limit=100, offset=0, type_tax_use=None, **kwargs):
        """
        Get list of taxes
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :param type_tax_use: Filter by type ('sale', 'purchase', 'none')
        :return: JSON response with taxes list
        """
        try:
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            domain = []
            if type_tax_use:
                domain.append(('type_tax_use', '=', type_tax_use))
            
            taxes = request.env['account.tax'].sudo().search(domain, limit=limit, offset=offset, order='id desc')
            
            result = []
            for tax in taxes:
                result.append({
                    'id': tax.id,
                    'name': tax.name,
                    'amount': tax.amount,
                    'amount_type': tax.amount_type,
                    'type_tax_use': tax.type_tax_use,
                    'type_tax_use_label': dict(tax._fields['type_tax_use'].selection).get(tax.type_tax_use, ''),
                    'company_id': tax.company_id.id if tax.company_id else None,
                    'company_name': tax.company_id.name if tax.company_id else '',
                    'active': tax.active,
                })
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': request.env['account.tax'].sudo().search_count(domain),
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing taxes: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/taxes', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_tax(self, **kwargs):
        """
        Create a new tax
        
        Expected JSON body:
        {
            "name": "Tax 10%",
            "amount": 10.0,
            "amount_type": "percent",
            "type_tax_use": "purchase",  // "sale", "purchase", or "none"
            "company_id": 1
        }
        
        :return: JSON response with created tax data
        """
        try:
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            vals = {}
            
            # Required fields
            if 'name' in data:
                vals['name'] = data['name']
            else:
                error_response = {
                    'status': 'error',
                    'message': 'name is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            if 'amount' in data:
                vals['amount'] = float(data['amount'])
            else:
                error_response = {
                    'status': 'error',
                    'message': 'amount is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Optional fields
            if 'amount_type' in data:
                vals['amount_type'] = data['amount_type']
            else:
                vals['amount_type'] = 'percent'  # Default
            
            if 'type_tax_use' in data:
                if data['type_tax_use'] in ['sale', 'purchase', 'none']:
                    vals['type_tax_use'] = data['type_tax_use']
                else:
                    vals['type_tax_use'] = 'none'
            else:
                vals['type_tax_use'] = 'none'
            
            if 'company_id' in data:
                vals['company_id'] = data['company_id']
            
            # Create default repartition lines if not provided
            if 'invoice_repartition_line_ids' not in vals:
                company = request.env.company
                tax_account = None
                
                # Try to find suitable account based on type_tax_use
                if vals.get('type_tax_use') == 'purchase':
                    tax_account = request.env['account.account'].sudo().search([
                        ('account_type', '=', 'expense'),
                        ('company_id', '=', company.id)
                    ], limit=1)
                elif vals.get('type_tax_use') == 'sale':
                    tax_account = request.env['account.account'].sudo().search([
                        ('account_type', '=', 'income'),
                        ('company_id', '=', company.id)
                    ], limit=1)
                
                vals['invoice_repartition_line_ids'] = [
                    (0, 0, {'repartition_type': 'base', 'factor_percent': 100.0}),
                    (0, 0, {'repartition_type': 'tax', 'factor_percent': 100.0, 'account_id': tax_account.id if tax_account else False}),
                ]
                vals['refund_repartition_line_ids'] = [
                    (0, 0, {'repartition_type': 'base', 'factor_percent': 100.0}),
                    (0, 0, {'repartition_type': 'tax', 'factor_percent': 100.0, 'account_id': tax_account.id if tax_account else False}),
                ]
            
            # Create tax
            tax = request.env['account.tax'].sudo().create(vals)
            
            response_data = {
                'status': 'success',
                'message': 'Tax created successfully',
                'data': {
                    'id': tax.id,
                    'name': tax.name,
                    'amount': tax.amount,
                    'amount_type': tax.amount_type,
                    'type_tax_use': tax.type_tax_use,
                    'type_tax_use_label': dict(tax._fields['type_tax_use'].selection).get(tax.type_tax_use, ''),
                    'company_id': tax.company_id.id if tax.company_id else None,
                    'company_name': tax.company_id.name if tax.company_id else '',
                    'active': tax.active,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating tax: {str(e)}")
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
            _logger.error(f"Validation error creating tax: {str(e)}")
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
            _logger.error(f"Error creating tax: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    # ============================================
    # VENDOR DELETE API
    # ============================================

    @http.route('/api/vendors/<int:vendor_id>', type='http', auth='bearer', methods=['DELETE'], csrf=False)
    def delete_vendor(self, vendor_id, **kwargs):
        """
        Delete a vendor
        
        :param vendor_id: ID of the vendor to delete
        :return: JSON response
        """
        try:
            vendor = request.env['res.partner'].sudo().browse(vendor_id)
            
            if not vendor.exists():
                error_response = {
                    'status': 'error',
                    'message': f'Vendor with ID {vendor_id} not found'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            vendor_name = vendor.name
            vendor.unlink()
            
            response_data = {
                'status': 'success',
                'message': f'Vendor "{vendor_name}" deleted successfully'
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error deleting vendor: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    # ============================================
    # MANAGER APIs
    # ============================================

    @http.route('/api/managers', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_managers(self, limit=100, offset=0, **kwargs):
        """
        Get list of managers (users with expense approval rights)
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :return: JSON response with managers list
        """
        try:
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            # Get users with expense team approver group
            expense_group_ext_id = 'hr_expense.group_hr_expense_team_approver'
            domain = [('share', '=', False)]  # Internal users only
            
            # Search for all internal users
            all_users = request.env['res.users'].sudo().search(domain, order='id desc')
            
            # Filter users who have the expense team approver group using has_group method
            managers = all_users.filtered(lambda u: u.has_group(expense_group_ext_id))
            
            # Apply pagination
            managers = managers[offset:offset + limit]
            
            result = []
            for manager in managers:
                result.append({
                    'id': manager.id,
                    'name': manager.name,
                    'login': manager.login,
                    'email': manager.email or '',
                    'employee_id': manager.employee_id.id if manager.employee_id else None,
                    'employee_name': manager.employee_id.name if manager.employee_id else '',
                    'active': manager.active,
                })
            
            # Calculate total count
            all_users_total = request.env['res.users'].sudo().search(domain)
            total_count = len(all_users_total.filtered(lambda u: u.has_group(expense_group_ext_id)))
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': total_count,
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing managers: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/managers', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_manager(self, **kwargs):
        """
        Create a new manager (user with expense approval rights)
        
        Expected JSON body:
        {
            "name": "Manager Name",
            "login": "manager_login",
            "email": "manager@example.com",
            "password": "password123",
            "employee_id": 1  // Optional: link to employee
        }
        
        :return: JSON response with created manager data
        """
        try:
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            vals = {}
            
            # Required fields
            if 'name' in data:
                vals['name'] = data['name']
            else:
                error_response = {
                    'status': 'error',
                    'message': 'name is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            if 'login' in data:
                vals['login'] = data['login']
            else:
                error_response = {
                    'status': 'error',
                    'message': 'login is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            if 'password' in data:
                vals['password'] = data['password']
            else:
                error_response = {
                    'status': 'error',
                    'message': 'password is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Optional fields
            if 'email' in data:
                vals['email'] = data['email']
            if 'employee_id' in data:
                vals['employee_id'] = data['employee_id']
            
            # Set as internal user
            vals['share'] = False
            
            # Create user
            manager = request.env['res.users'].sudo().create(vals)
            
            # Add expense team approver group
            expense_group = request.env.ref('hr_expense.group_hr_expense_team_approver', raise_if_not_found=False)
            if expense_group:
                manager.groups_id = [(4, expense_group.id)]
            
            response_data = {
                'status': 'success',
                'message': 'Manager created successfully',
                'data': {
                    'id': manager.id,
                    'name': manager.name,
                    'login': manager.login,
                    'email': manager.email or '',
                    'employee_id': manager.employee_id.id if manager.employee_id else None,
                    'employee_name': manager.employee_id.name if manager.employee_id else '',
                    'active': manager.active,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating manager: {str(e)}")
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
            _logger.error(f"Validation error creating manager: {str(e)}")
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
            _logger.error(f"Error creating manager: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    # ============================================
    # CATEGORY APIs (Expense Categories)
    # ============================================

    @http.route('/api/categories', type='http', auth='bearer', methods=['GET'], csrf=False)
    def list_categories(self, limit=100, offset=0, **kwargs):
        """
        Get list of expense categories (products that can be expensed)
        
        :param limit: Maximum number of records to return (default: 100)
        :param offset: Number of records to skip (default: 0)
        :return: JSON response with categories list
        """
        try:
            try:
                limit = int(limit) if limit else 100
                offset = int(offset) if offset else 0
            except (ValueError, TypeError):
                limit = 100
                offset = 0
            
            # Search for products that can be expensed
            categories = request.env['product.product'].sudo().search([
                ('can_be_expensed', '=', True)
            ], limit=limit, offset=offset, order='id desc')
            
            result = []
            for category in categories:
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'description': category.description or '',
                    'default_code': category.default_code or '',
                    'type': category.type,
                    'categ_id': category.categ_id.id if category.categ_id else None,
                    'categ_name': category.categ_id.name if category.categ_id else '',
                    'standard_price': category.standard_price,
                    'uom_id': category.uom_id.id if category.uom_id else None,
                    'uom_name': category.uom_id.name if category.uom_id else '',
                    'company_id': category.company_id.id if category.company_id else None,
                    'company_name': category.company_id.name if category.company_id else '',
                    'active': category.active,
                })
            
            response_data = {
                'status': 'success',
                'count': len(result),
                'total': request.env['product.product'].sudo().search_count([('can_be_expensed', '=', True)]),
                'data': result
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error(f"Error listing categories: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/categories', type='http', auth='bearer', methods=['POST'], csrf=False)
    def create_category(self, **kwargs):
        """
        Create a new expense category (product that can be expensed)
        
        Expected JSON body:
        {
            "name": "Meals",
            "description": "Restaurants, business lunches, etc.",
            "default_code": "FOOD",
            "type": "service",
            "categ_id": 1,
            "standard_price": 0.0,
            "uom_id": 1,
            "company_id": 1
        }
        
        :return: JSON response with created category data
        """
        try:
            data = json.loads(request.httprequest.data.decode('utf-8')) if request.httprequest.data else {}
            
            vals = {}
            
            # Required fields
            if 'name' in data:
                vals['name'] = data['name']
            else:
                error_response = {
                    'status': 'error',
                    'message': 'name is required'
                }
                return request.make_response(
                    json.dumps(error_response),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Set as expensable
            vals['can_be_expensed'] = True
            vals['purchase_ok'] = True  # Required for can_be_expensed
            
            # Optional fields
            if 'description' in data:
                vals['description'] = data['description']
            if 'default_code' in data:
                vals['default_code'] = data['default_code']
            if 'type' in data:
                if data['type'] in ['consu', 'service']:
                    vals['type'] = data['type']
                else:
                    vals['type'] = 'service'  # Default for expenses
            else:
                vals['type'] = 'service'  # Default for expenses
            
            if 'categ_id' in data:
                vals['categ_id'] = data['categ_id']
            if 'standard_price' in data:
                vals['standard_price'] = float(data['standard_price'])
            else:
                vals['standard_price'] = 0.0  # Default for expense categories
            
            if 'uom_id' in data:
                vals['uom_id'] = data['uom_id']
            else:
                # Default to unit if not provided
                uom_unit = request.env['uom.uom'].sudo().search([('name', '=', 'Units')], limit=1)
                if not uom_unit:
                    uom_unit = request.env['uom.uom'].sudo().search([], limit=1)
                if uom_unit:
                    vals['uom_id'] = uom_unit.id
            
            if 'company_id' in data:
                vals['company_id'] = data['company_id']
            
            # Create category
            category = request.env['product.product'].sudo().create(vals)
            
            response_data = {
                'status': 'success',
                'message': 'Category created successfully',
                'data': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description or '',
                    'default_code': category.default_code or '',
                    'type': category.type,
                    'categ_id': category.categ_id.id if category.categ_id else None,
                    'categ_name': category.categ_id.name if category.categ_id else '',
                    'standard_price': category.standard_price,
                    'uom_id': category.uom_id.id if category.uom_id else None,
                    'uom_name': category.uom_id.name if category.uom_id else '',
                    'can_be_expensed': category.can_be_expensed,
                    'company_id': category.company_id.id if category.company_id else None,
                    'company_name': category.company_id.name if category.company_id else '',
                    'active': category.active,
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
        except json.JSONDecodeError as e:
            _logger.error(f"JSON decode error creating category: {str(e)}")
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
            _logger.error(f"Validation error creating category: {str(e)}")
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
            _logger.error(f"Error creating category: {str(e)}")
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            return request.make_response(
                json.dumps(error_response),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

