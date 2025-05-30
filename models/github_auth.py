# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import jwt
import logging
import time

_logger = logging.getLogger(__name__)

class GitHubAuth(models.Model):
    """GitHub Authentication Model
    
    This model stores GitHub authentication credentials and handles token management.
    It supports different authentication methods:
    - Personal Access Token
    - Fine-grained Token
    - GitHub App
    """
    _name = 'github.auth'
    _description = 'GitHub Authentication'
    _order = 'name'
    
    name = fields.Char(string='Name', required=True, index=True)
    active = fields.Boolean(default=True, string='Active', copy=False,)
    auth_type = fields.Selection([
        ('personal', 'Personal Access Token'),
        ('fine_grained', 'Fine-grained Token'),
        ('github_app', 'GitHub App')
    ], string='Authentication Type', required=True, default='personal', copy=False)

    
    # Personal Access Token and Fine-grained Token fields
    token = fields.Char(string='Token', groups='base.group_system')
    token_expiration = fields.Datetime(string='Token Expiration')
    user_id = fields.Many2one(
        'res.users', string='User', default=lambda self: self.env.user, readonly=True,
        help="User who owns this record. This field is used for authorization purposes."
    )
    
    # GitHub App fields
    app_id = fields.Char(string='App ID', groups='base.group_system')
    app_name = fields.Char(string='App Name')
    private_key = fields.Text(string='Private Key', groups='base.group_system')
    installation_id = fields.Char(string='Installation ID', groups='base.group_system')
    jwt_token = fields.Char(string='JWT Token', groups='base.group_system')
    jwt_expiration = fields.Datetime(string='JWT Expiration')
    
    # User access for GitHub App
    user_ids = fields.Many2many('res.users', string='Authorized Users',
                               help='Users authorized to use this GitHub App authentication')
    
    # Status fields
    last_validation = fields.Datetime(string='Last Validation')
    state = fields.Selection([
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('invalid', 'Invalid')
    ], string='Status', compute='_compute_state', store=True)
    
    @api.depends('token', 'token_expiration', 'jwt_token', 'jwt_expiration', 'auth_type', 'last_validation')
    def _compute_state(self):
        """Compute the state of the authentication based on token validity and expiration."""
        now = fields.Datetime.now()
        for record in self:
            if record.auth_type in ['personal', 'fine_grained']:
                if not record.token:
                    record.state = 'invalid'
                elif record.token_expiration and record.token_expiration < now:
                    record.state = 'expired'
                else:
                    record.state = 'valid'
            elif record.auth_type == 'github_app':
                if not record.app_id or not record.private_key or not record.installation_id:
                    record.state = 'invalid'
                elif record.jwt_expiration and record.jwt_expiration < now:
                    record.state = 'expired'
                else:
                    record.state = 'valid'
    
    @api.constrains('auth_type', 'token', 'app_id', 'private_key', 'installation_id')
    def _check_required_fields(self):
        """Validate that required fields are set based on authentication type."""
        for record in self:
            if record.auth_type in ['personal', 'fine_grained'] and not record.token:
                raise ValidationError(_("Token is required for Personal Access Token and Fine-grained Token authentication."))
            elif record.auth_type == 'github_app':
                if not record.app_id:
                    raise ValidationError(_("App ID is required for GitHub App authentication."))
                if not record.private_key:
                    raise ValidationError(_("Private Key is required for GitHub App authentication."))
                if not record.installation_id:
                    raise ValidationError(_("Installation ID is required for GitHub App authentication."))
    
    def generate_jwt_token(self):
        """Generate a JWT token for GitHub App authentication."""
        self.ensure_one()
        if self.auth_type != 'github_app':
            raise UserError(_("JWT token generation is only available for GitHub App authentication."))
        
        if not self.app_id or not self.private_key:
            raise UserError(_("App ID and Private Key are required to generate a JWT token."))
        
        # JWT tokens for GitHub Apps expire after 10 minutes
        now = int(time.time())
        expiration = now + (10 * 60)  # 10 minutes
        
        payload = {
            'iat': now,
            'exp': expiration,
            'iss': self.app_id
        }
        
        try:
            token = jwt.encode(payload, self.private_key, algorithm='RS256')
            self.write({
                'jwt_token': token,
                'jwt_expiration': fields.Datetime.to_string(datetime.fromtimestamp(expiration)),
                'last_validation': fields.Datetime.now()
            })
            return token
        except Exception as e:
            _logger.error("Failed to generate JWT token: %s", str(e))
            raise UserError(_("Failed to generate JWT token: %s") % str(e))
    
    def validate_token(self):
        """Validate the authentication token by making a test API call."""
        self.ensure_one()
        # This method would make an API call to GitHub to validate the token
        # For now, we'll just update the last_validation timestamp
        self.write({'last_validation': fields.Datetime.now()})
        return True

    def check_auth(self):
        msg = ''
        for auth in self:
            if auth.auth_type in ['personal', 'fine_grained'] and not auth.token:
                raise UserError(_(f"The authorization {auth.name} for {auth.user_id.name} its token is not set."))

    
    def get_auth_headers(self):
        """Get the authentication headers for GitHub API requests."""
        self.ensure_one()
        headers = {}

        self.check_auth()

        if self.auth_type in ['personal', 'fine_grained']:
            headers['Authorization'] = f'token {self.token}'
        elif self.auth_type == 'github_app':
            # Check if JWT token is expired and regenerate if needed
            now = fields.Datetime.now()
            if not self.jwt_token or not self.jwt_expiration or self.jwt_expiration < now:
                self.generate_jwt_token()
            headers['Authorization'] = f'Bearer {self.jwt_token}'

        return headers
    
    def is_user_authorized(self, user=None):
        """Check if the given user is authorized to use this authentication."""
        self.ensure_one()
        if user is None:
            user = self.env.user
        
        if self.auth_type != 'github_app':
            # For personal and fine-grained tokens, no user restriction
            return True
        
        # For GitHub App, check if user is in authorized users
        return user in self.user_ids
    
    @api.model
    def get_auth_for_user(self, user=None):
        """Get all active authentication methods available for the given user."""
        if not user:
            user = self.env.user
        
        domain = [('active', '=', True), '|', ('auth_type', '=', 'github_app'),('user_id', '=', user.id)]
        auths = self.search(domain)
        
        # Filter auths based on user authorization
        return auths.filtered(lambda a: a.is_user_authorized(user))