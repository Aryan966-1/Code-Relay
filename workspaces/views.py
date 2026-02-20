from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Workspace, WorkspaceMembership


@api_view(['POST'])
def create_workspace(request):
    name = request.data.get('name')
    description = request.data.get('description')

    workspace = Workspace.objects.create(
        name=name,
        description=description,
        created_by=request.user
    )

    # Make creator ADMIN
    WorkspaceMembership.objects.create(
        user=request.user,
        workspace=workspace,
        role='ADMIN'
    )

    return Response({"message": "Workspace created"})