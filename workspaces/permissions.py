from .models import WorkspaceMembership

def is_workspace_admin(user, workspace):
    if not user.is_authenticated:
        return False

    return WorkspaceMembership.objects.filter(
        user=user,
        workspace=workspace,
        role=WorkspaceMembership.Role.ADMIN
    ).exists()