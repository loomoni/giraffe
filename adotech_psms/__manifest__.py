# -*- coding: utf-8 -*-
{
    'name': 'Giraffe Psms',
    'version': '15.0.1.0.0',
    'category': 'Petrol station gateway',
    'summary': """
       Being sales gateway
    """,
    'description': """Odoo15 petrol satation sales""",
    'author': 'Adotech',
    'company': 'Adotech',
    'maintainer': 'Adotech',
    'website': 'https://adotech.co.tz/',
    'depends': ['sale', 'sale_management', 'base'],
    'data': [
        "security/ir.model.access.csv",
        "views/psms_sales.xml",
        "views/gateway.xml",
        "views/station.xml",
        "views/main_menu.xml",
        "data/cron.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'AGPL-3',
}