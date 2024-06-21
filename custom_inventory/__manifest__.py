# __manifest__.py
{
    'name': 'Custom Product ID per Warehouse',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Manage product IDs specific to each warehouse',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': True,
}