# GitHub Integration for Odoo

This module provides GitHub API integration for Odoo, allowing users to connect to GitHub API using different authentication methods and manage GitHub repositories. It leverages the HTTP Client module for seamless API communication and automatic data synchronization.

## Features

- Connect to GitHub API using personal tokens or GitHub Apps
- List repositories for the authenticated user
- Manage GitHub authentication with token expiration handling
- Support for different authentication methods (personal token, fine-grained token, GitHub App)
- JWT authentication for GitHub Apps
- Token expiration management according to the authentication methods
- User-based access control
- Authentication method selection wizard
- Automatic data synchronization with GitHub API

## Technical Features

- Built on top of the HTTP Client module
- Automatic data synchronization through the https.pool.web abstract model
- Repository listing and management without manual API requests
- User-based access control
- Authentication method selection wizard
- Efficient data fetching with database savepoints for transactional safety

## Models

### GitHub Authentication (github.auth)

This model stores GitHub authentication credentials and handles token management. It supports different authentication methods:
- Personal Access Token
- Fine-grained Token
- GitHub App

For GitHub App authentication, you can specify which users are allowed to use the authentication method.

### GitHub Repository (github.repository)

This model represents GitHub repositories and provides methods for fetching and managing repository data from the GitHub API. It inherits from the `https.pool.web` abstract model from the HTTP Client module.

### GitHub Authentication Selection Wizard (github.auth.selection.wizard)

This wizard allows users to select which authentication method to use when they have multiple active authentication methods available.

## Usage

### Setting up Authentication

1. Go to GitHub > Configuration > Authentication
2. Create a new authentication record
3. Select the authentication type (Personal Access Token, Fine-grained Token, or GitHub App)
4. Fill in the required fields based on the authentication type
5. For GitHub App authentication, specify the authorized users

### Fetching Repositories

1. Go to GitHub > Fetch Repositories
2. If you have multiple authentication methods, select the one you want to use
3. Click Confirm to fetch repositories

### Viewing Repositories

1. Go to GitHub > Repositories
2. View the list of repositories fetched from GitHub
3. Click on a repository to view its details

## Security

- Regular users can only see their own repositories and the authentication methods they are authorized to use
- System users have full access to all repositories and authentication methods
- Only system users can create and manage authentication methods
- Regular users can view and update repositories but not create or delete them

## Dependencies

- HTTP Client module (`http_client`)
- Python libraries: `urllib3`, `pyjwt`

## Installation

1. Install the required dependencies
2. Install the HTTP Client module
3. Install this module
4. Configure authentication methods
5. Fetch repositories

## Additional Resources

- [Medium Post: HTTP Client Module (Spanish)](https://medium.com/@kherney/cliente-http-para-odoo-el-compa%C3%B1ero-ideal-para-tus-apis-1280d35c005f): A technical article explaining how the HTTP Client module and the https.pool.web abstract model enable automatic data synchronization with external APIs, using this module as a case study.
- [Medium Post: GitHub Integration (Spanish)](https://medium.com/@kherney/github-modulo-odoo-usando-api-6db91d8630f7): A technical article focusing on the GitHub module's philosophy, architecture, and main features, highlighting its modular design and integration capabilities.

## License

AGPL-3
