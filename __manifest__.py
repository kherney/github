# -*- coding: utf-8 -*-
{
    'name': "GitHub Integration",
    'sequence': 370,

    'summary': "GitHub API integration for Odoo",

    'description': """
    This module provides GitHub API integration for Odoo:

    * Connect to GitHub API using personal tokens or GitHub Apps
    * List repositories for the authenticated user
    * Manage GitHub authentication with token expiration handling
    * Support for different authentication methods (personal token, fine-grained token, GitHub App)
    * JWT authentication for GitHub Apps
    * Token expiration management according with the authentication methods

    Technical Features:

    * Built on top of the HTTP Client module
    * Repository listing and management
    * User-based access control
    * Authentication method selection wizard
    """,

    'author': "Kevin Herney <kevinh939@gmail.com>",
    'url': "",
    'maintainer': 'kevinh939@gmail.com',
    'website': "https://kherney.github.io/",

    'category': 'Technical',
    'version': '17.0.0.0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['web', 'http_client'],

    # always loaded
    'data': [
        # Security
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        # Views
        'views/github_auth_views.xml',
        'views/github_repository_views.xml',
        'wizard/github_auth_selection_wizard_views.xml',
        # Menus
        'views/menus.xml'
    ],

    'application': False,
    'auto_install': False,
    'installable': True,

    'external_dependencies': {
        'python': ['urllib3', 'pyjwt'],
    },
}
