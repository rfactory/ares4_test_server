# C:\vscode project files\Ares4\server2\app\domains\inter_domain\organizations\schemas\organization_query.py

# This file re-exports schemas from the organizations service domain,
# making them accessible to other domains through a single, stable interface.

from ....services.organizations.schemas.organization_query import (
    OrganizationResponse,
    OrganizationTypeResponse,
)
