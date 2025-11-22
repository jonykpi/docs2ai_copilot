{
    'name': 'Docs2AI copilot',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': 'Upload vendor bills to Docs2AI - docs2ai copilot',
    'description': """
        <p><strong>Docs2AI Copilot</strong> lets accounting teams push vendor bills (PDF or image)
        straight to Docs2AI for OCR and automated data extraction.</p>
        <ul>
            <li>Adds an <em>Upload to Docs2AI</em> button on vendor bills</li>
            <li>Validates API credentials and target folder directly from Odoo settings</li>
            <li>Attaches the processed document back to the bill for full traceability</li>
            <li>Supports PDF, JPG, PNG, GIF, BMP and WEBP uploads</li>
        </ul>
        <p>Use it to eliminate manual data entry, keep auditors happy, and
        centralize vendor paperwork without leaving Odoo.</p>
        <p><strong>Supported versions:</strong> Odoo 16.0 → 19.0 (Community, Enterprise,
        Odoo.sh or on-premise deployments; 19.0 is the primary tested release).</p>
    """,
    'author': 'Docs2ai',
    'website': 'https://www.docs2ai.co',
    'depends': ['account', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/docs2ai_upload_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'docs2ai_copilot/static/src/css/drag_drop_widget.css',
            'docs2ai_copilot/static/src/js/drag_drop_files.js',
            'docs2ai_copilot/static/src/js/docs2ai_upload_wizard_view.js',
            'docs2ai_copilot/static/src/js/docs2ai_file_uploader.js',
            'docs2ai_copilot/static/src/xml/docs2ai_file_uploader.xml',
        ],
    },
    'icon': 'static/description/icon.png',
    
    'images': [ 'static/description/banner.png',  'static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
