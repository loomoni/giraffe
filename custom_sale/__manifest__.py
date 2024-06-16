# -*- coding: utf-8 -*-
{
    'name': "Custom Sale",

    'summary': """
        Custom Sale""",

    'description': """
        Custom Sale
    """,

    'author': "Loomoni Morwo",
    'website': "https://loomoni.co.tz/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [

        'security/security.xml',
        'security/ir.model.access.csv',
        'views/remove_login_brand.xml',
        'views/views.xml',
    ],

    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
