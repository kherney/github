# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

from . import HOST_GITHUB

_logger = logging.getLogger(__name__)

class GitHubRepository(models.Model):
    """GitHub Repository Model
    
    This model represents GitHub repositories and provides methods for fetching
    and managing repository data from the GitHub API.
    """
    _name = 'github.repository'
    _inherit = 'https.pool.web'
    _description = 'GitHub Repository'
    _order = 'name'

    _http_connection = {
        'host': HOST_GITHUB,
        'headers': {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
    }

    
    name = fields.Char(string='Repository Name', required=True, index=True)
    full_name = fields.Char(string='Full Name', readonly=True, index=True)
    description = fields.Text(string='Description')
    private = fields.Boolean(string='Private', readonly=True)
    html_url = fields.Char(string='HTML URL', readonly=True)
    clone_url = fields.Char(string='Clone URL', readonly=True)
    ssh_url = fields.Char(string='SSH URL', readonly=True)
    default_branch = fields.Char(string='Default Branch', readonly=True)
    
    # Owner information
    owner_login = fields.Char(string='Owner Login', readonly=True)
    owner_avatar_url = fields.Char(string='Owner Avatar URL', readonly=True)
    owner_html_url = fields.Char(string='Owner HTML URL', readonly=True)
    
    # Stats
    stargazers_count = fields.Integer(string='Stars', readonly=True)
    forks_count = fields.Integer(string='Forks', readonly=True)
    open_issues_count = fields.Integer(string='Open Issues', readonly=True)
    watchers_count = fields.Integer(string='Watchers', readonly=True)
    
    # Dates
    created_at = fields.Datetime(string='Created At', readonly=True)
    updated_at = fields.Datetime(string='Updated At', readonly=True)
    pushed_at = fields.Datetime(string='Pushed At', readonly=True)
    
    # GitHub API data
    github_id = fields.Integer(string='GitHub ID', readonly=True)
    raw_data = fields.Text(string='Raw Data', readonly=True, groups='base.group_system')
    
    # Authentication
    auth_id = fields.Many2one('github.auth', string='Authentication', 
                             required=False)
    
    # User who owns this record
    user_id = fields.Many2one('res.users', string='User', 
                             default=lambda self: self.env.user,
                             required=True, ondelete='cascade')

    
    _sql_constraints = [
        ('github_id_auth_id_uniq', 'unique(github_id, auth_id)', 
         'Repository must be unique per authentication method!')
    ]

    def serialize(self, repo_data):

        # Prepare values for create/update
        repo = {
            'name': repo_data.get('name'),
            'full_name': repo_data.get('full_name'),
            'description': repo_data.get('description'),
            'private': repo_data.get('private', False),
            'html_url': repo_data.get('html_url'),
            'clone_url': repo_data.get('clone_url'),
            'ssh_url': repo_data.get('ssh_url'),
            'default_branch': repo_data.get('default_branch'),
            'owner_login': repo_data.get('owner', {}).get('login'),
            'owner_avatar_url': repo_data.get('owner', {}).get('avatar_url'),
            'owner_html_url': repo_data.get('owner', {}).get('html_url'),
            'stargazers_count': repo_data.get('stargazers_count', 0),
            'forks_count': repo_data.get('forks_count', 0),
            'open_issues_count': repo_data.get('open_issues_count', 0),
            'watchers_count': repo_data.get('watchers_count', 0),
            'created_at': repo_data.get('created_at'),
            'updated_at': repo_data.get('updated_at'),
            'pushed_at': repo_data.get('pushed_at'),
            'github_id': repo_data.get('id'),
            'raw_data': json.dumps(repo_data),
            'user_id': self.env.user.id,
        }

        return repo

    
    def set_auth_headers(self):
        """ override Set authentication headers for GitHub API requests."""
        Auth = self.env['github.auth']
        
        # Get the authentication record
        auth = Auth.get_auth_for_user() or Auth.browse(self.env.context.get('default_auth', []))

        if not auth:
            raise UserError(_("No authentication method specified."))
        
        # Check if the current user is authorized to use this authentication
        if not auth.is_user_authorized():
            raise UserError(_("You are not authorized to use this authentication method."))
        
        # Get headers from the authentication record
        return auth.get_auth_headers()
    
    @api.model
    def fetch_data(self, cr):
        """Fetch repository data from GitHub API."""
        if self.env.context.get('no_fetch_data', False):
            return
        
        # Get authentication methods available for the current user
        auth_model = self.env['github.auth']
        available_auths = auth_model.get_auth_for_user()
        
        if not available_auths:
            raise UserError(_("No GitHub authentication methods available for your user."))
        
        # If multiple authentication methods are available, let the user choose
        if len(available_auths) > 1 and not self._context.get('auth_id'):
            # This would normally open a wizard, but for now we'll just use the first one
            auth = available_auths[0]
        else:
            auth = available_auths[0]
        
        # Set the authentication in context
        self = self.with_context(auth_id=auth.id)
        
        try:
            response = self.get('/user/repos')
            if response.status != 200:
                raise UserError(_("Failed to fetch repositories: %s") % response.data.decode('utf-8'))
            
            repos_data = json.loads(response.data.decode('utf-8'))
            self._process_repositories_data(cr, repos_data, auth)
            
        except Exception as e:
            _logger.error("Error fetching repositories: %s", str(e))
            raise UserError(_("Error fetching repositories: %s") % str(e))
    
    def _process_repositories_data(self, cr, repos_data, auth):
        """Process repository data from GitHub API and update the database."""
        user_id = self.env.user.id

        repos = { r.get('id'): r for r in repos_data}
        github_ids = tuple(repos.keys())  # Explict tuple conversion for SQL query

        # Check if repositories already exists
        cr.execute("SELECT id, github_id FROM github_repository WHERE github_id IN %s", (github_ids,))
        to_update = cr.fetchall()

        updated = []

        for id_update, _ in to_update:
            updated.append(_)
            repo_data = repos[_]

            vals = self.serialize(repo_data)

            # Update existing repository
            cr.execute("""
                UPDATE github_repository SET
                    name = %s,
                    full_name = %s,
                    description = %s,
                    private = %s,
                    html_url = %s,
                    clone_url = %s,
                    ssh_url = %s,
                    default_branch = %s,
                    owner_login = %s,
                    owner_avatar_url = %s,
                    owner_html_url = %s,
                    stargazers_count = %s,
                    forks_count = %s,
                    open_issues_count = %s,
                    watchers_count = %s,
                    created_at = %s,
                    updated_at = %s,
                    pushed_at = %s,
                    raw_data = %s
                WHERE id = %s
            """, (
                vals['name'], vals['full_name'], vals['description'], vals['private'],
                vals['html_url'], vals['clone_url'], vals['ssh_url'], vals['default_branch'],
                vals['owner_login'], vals['owner_avatar_url'], vals['owner_html_url'],
                vals['stargazers_count'], vals['forks_count'], vals['open_issues_count'],
                vals['watchers_count'], vals['created_at'], vals['updated_at'], vals['pushed_at'],
                vals['raw_data'], id_update
            ))

        # Create new repositories
        to_create = [_id for _id in github_ids if _id not in updated]

        if not to_create:
            return

        values = ','.join(['%s'] * len(to_create))

        params = tuple(tuple(self.serialize(repos[id_create]).values()) for id_create in to_create)

        query = """INSERT INTO github_repository (
                name, full_name, description, private, html_url, clone_url, ssh_url,
                default_branch, owner_login, owner_avatar_url, owner_html_url,
                stargazers_count, forks_count, open_issues_count, watchers_count,
                created_at, updated_at, pushed_at, github_id, raw_data, user_id
            ) VALUES %s"""

        final_query = self.env.cr.mogrify(query % values, params).decode('utf-8')

        cr.execute(final_query)
