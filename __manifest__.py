{
    'name': 'Docs2AI Upload',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': 'Upload vendor bills to Docs2AI - docs2ai',
    'description': """
        This module adds a button to vendor bill forms to upload PDF or image files to Docs2AI.
        After clicking the button, users can select a PDF or image file which will be sent to the Docs2AI API.
        This module only works with vendor bills (purchase entries), not customer invoices.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['account', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/docs2ai_upload_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
