from django.db.models import Count, Sum


def get_cycle_stats(project):
    if project.cycletour_set:
        return project.cycletour_set.aggregate(
            cyclists=Count('user', distinct=True),
            km_sum=Sum('km'),
            euro_sum=Sum('euro'))
    return None
