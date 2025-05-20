{
    "name": "Invoice activity",
    "summary": """Module for invoice zip file.""",
    "author": "CODE-OX",
    "website": "https://www.code-ox.com/",
    "license": "LGPL-3",
    "category": "Accounting",
    "version": "18.0.0.0",
    "depends": ['account'],
    "data": [
        "security/ir.model.access.csv",
        'data/server_action.xml',
        ],
    'installable': True,
    'application': True,
}
