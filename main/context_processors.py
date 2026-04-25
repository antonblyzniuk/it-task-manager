from .models import ProjectMembership


def user_projects(request):
    if request.user.is_authenticated:
        memberships = (
            ProjectMembership.objects
            .filter(worker=request.user)
            .select_related("project")
            .order_by("-project__updated_at")
        )
        return {"user_memberships": list(memberships)}
    return {"user_memberships": []}
