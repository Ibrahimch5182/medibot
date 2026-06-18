"""
RBAC configuration for MediBot.

Very important:
RBAC must be applied at the retrieval layer, meaning Qdrant should only return
chunks that the user's role is allowed to see.
"""

from typing import Dict, List


ROLE_COLLECTIONS: Dict[str, List[str]] = {
    "doctor": ["general", "clinical", "nursing"],
    "nurse": ["general", "nursing"],
    "billing_executive": ["general", "billing"],
    "technician": ["general", "equipment"],
    "admin": ["general", "clinical", "nursing", "billing", "equipment"],
}


COLLECTION_ACCESS_ROLES: Dict[str, List[str]] = {
    "general": ["doctor", "nurse", "billing_executive", "technician", "admin"],
    "clinical": ["doctor", "admin"],
    "nursing": ["nurse", "doctor", "admin"],
    "billing": ["billing_executive", "admin"],
    "equipment": ["technician", "admin"],
}


DEMO_USERS: Dict[str, Dict[str, str]] = {
    "dr.mehta": {"password": "doctor", "role": "doctor"},
    "nurse.priya": {"password": "nurse", "role": "nurse"},
    "billing.ravi": {"password": "billing_executive", "role": "billing_executive"},
    "tech.anand": {"password": "technician", "role": "technician"},
    "admin.sys": {"password": "admin", "role": "admin"},
}


def get_accessible_collections(role: str) -> List[str]:
    """Return document collections accessible by a role."""
    return ROLE_COLLECTIONS.get(role, [])


def is_valid_role(role: str) -> bool:
    """Check whether a role exists in our RBAC matrix."""
    return role in ROLE_COLLECTIONS


def get_access_roles_for_collection(collection: str) -> List[str]:
    """Return roles allowed to access a collection."""
    return COLLECTION_ACCESS_ROLES.get(collection, [])