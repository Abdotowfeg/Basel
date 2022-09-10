# -*- coding: utf-8 -*-
{
    'name': "Asset Managment",

    'summary': """
        Assets management
""",

    'description': """
Assets management
=================
Manage assets owned by a company or a person.
Keeps track of depreciations, and creates corresponding journal entries.
""",

    'category': 'Accounting',
    'version': '0.1', 
    'sequence': 32,
    # any module necessary for this one to work correctly
    'depends': ['base','account'],
    'author': 'Noptechs',
    'website': "https://noptechs.com",
    'company': 'Noptechs',
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/account_asset_data.xml',
        'views/assets.xml',
        'wizard/asset_depreciation_confirmation_wizard_views.xml',
        'wizard/asset_modify_views.xml',
        'wizard/sale_dispose_process.xml',
        'views/account_asset_views.xml',
        'views/asset_revaluation.xml',
        'views/asset_enhancement.xml',
        'views/account_move_views.xml',
    	'views/account_asset_templates.xml',
        'views/product_template_views.xml',
     	'report/account_asset_report_views.xml',
        

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
