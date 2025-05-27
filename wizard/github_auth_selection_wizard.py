# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class GitHubAuthSelectionWizard(models.TransientModel):
    """GitHub Authentication Selection Wizard
    
    This wizard allows users to select which authentication method to use
    when they have multiple active authentication methods available.
    """
    _name = 'github.auth.selection.wizard'
    _description = 'GitHub Authentication Selection'
    
    auth_id = fields.Many2one('github.auth', string='Authentication Method',
                             required=True, domain="[('id', 'in', available_auth_ids)]")
    available_auth_ids = fields.Many2many('github.auth', string='Available Authentication Methods',
                                         readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        """Set default values for the wizard fields."""
        res = super(GitHubAuthSelectionWizard, self).default_get(fields_list)
        
        # Get authentication methods available for the current user
        auth_model = self.env['github.auth']
        available_auths = auth_model.get_auth_for_user()
        
        if not available_auths:
            raise UserError(_("No GitHub authentication methods available for your user."))
        
        # Set available authentication methods
        res['available_auth_ids'] = [(6, 0, available_auths.ids)]
        
        # Set default authentication method if there's only one
        if len(available_auths) == 1:
            res['auth_id'] = available_auths[0].id
        
        return res
    
    def action_confirm(self):
        """Confirm the selected authentication method and fetch repositories."""
        self.ensure_one()
        
        if not self.auth_id:
            raise UserError(_("Please select an authentication method."))
        
        # Call the repository model's fetch_data method with the selected authentication
        return {
            'type': 'ir.actions.act_window',
            'name': _('GitHub Repositories'),
            'res_model': 'github.repository',
            'view_mode': 'tree,form',
            'context': {'auth_id': self.auth_id.id},
            'target': 'current',
        }