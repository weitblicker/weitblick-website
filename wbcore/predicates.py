import rules


@rules.predicate
def is_admin_for_event(user, event):
    return user.is_admin_of_host(event.host)


@rules.predicate
def is_admin_for_project(user, project):
    return user.is_admin_of_host(project.hosts)


@rules.predicate
def is_admin_for_host(user, host):
    return user.is_admin_of_host(host)


@rules.predicate
def is_admin_for_user_relation(user, relation):
    return user.is_admin_of_host(relation.host)


@rules.predicate
def is_admin_for_post(user, post):
    return user.is_admin_of_host(post.host)


@rules.predicate
def is_admin_for_document(user, document):
    return user.is_admin_of_host(document.host)


@rules.predicate
def is_admin_for_team(user, team):
    return user.is_admin_of_host(team.host)


@rules.predicate
def is_admin_for_team_user_relation(user, relation):
    return is_admin_for_team(user, relation.team)


@rules.predicate
def is_admin_for_content(user, content):
    return user.is_admin_of_host(content.host)


@rules.predicate
def is_admin_for_donation(user, donation):
    return user.is_admin_of_host(user, donation.host)


@rules.predicate
def is_admin_for_milestone(user, milestone):
    return is_admin_for_project(user, milestone.project)


@rules.predicate
def is_admin_for_milestep(user, milestep):
    return is_admin_for_milestep(user, milestep.milestone)


@rules.predicate
def is_admin_for_bank_account(user, bank_account):
    return bank_account.user.hosts and user.is_admin_of_host(bank_account.user.hosts)


@rules.predicate
def is_admin_for_contact_message(user, contact_message):
    return user.is_admin_of_host(contact_message.host)


@rules.predicate
def is_admin_for_user(user, other_user):
    return user.is_admin_of_host(other_user.hosts)


@rules.predicate
def is_admin_for_join_page(user, join_page):
    return user.is_admin_of_host(join_page.host)


@rules.predicate
def is_admin_for_social_media_link(user, social_media_link):
    return user.is_admin_of_host(social_media_link.host)


def has_role_for_address(role, user, address):
    from wbcore.models import User, Partner
    hosts = user.get_hosts_for_role(role)
    if user.userrelation_set.filter(member_type=role, host__address=address) > 0:
        return True

    # address belongs to a user
    if User.objects.filter(hosts__in=hosts, address=address).count() > 0:
        return True

    # address belongs to any partner
    if Partner.objects.filter(address=address).count > 0:
        return True

    return False


@rules.predicate
def is_admin_for_address(user, address):
    return has_role_for_address('admin', user, address)


@rules.predicate
def is_editor_for_address(user, address):
    return has_role_for_address('editor', user, address)


def has_role_for_location(role, user, location):
    from wbcore.models import Project, Event

    hosts = user.get_hosts_for_role(role)

    if hosts and not location:
        return True

    if user.userrelation_set.filter(member_type=role, host__location=location).count() > 0:
        return True

    if Project.objects.filter(hosts__in=hosts, location=location).count() > 0:
        return True

    if Event.objects.filter(host__in=hosts, location=location).count() > 0:
        return True

    return False


@rules.predicate
def is_admin_for_location(user, location):
    return has_role_for_location('admin', user, location)


@rules.predicate
def is_editor_for_location(user, location):
    return has_role_for_location('editor', user, location)


@rules.predicate
def is_super_admin(user):
    return user.is_super_admin


def has_role_for_host(role, user, obj):
    from wbcore.models import Address, Location
    if isinstance(obj, Address):
        return has_role_for_address(role, user, obj)

    if isinstance(obj, Location):
        return has_role_for_location(role, user, obj)

    if not obj:
        return user.has_role(role)

    return user.has_role_for_host(role, obj.get_hosts())


@rules.predicate
def is_admin(user, obj):
    return has_role_for_host('admin', user, obj)


@rules.predicate
def is_editor(user, obj):
    return has_role_for_host('editor', user, obj)


@rules.predicate
def is_author(user, obj):
    return has_role_for_host('author', user, obj)


@rules.predicate
def is_user_of_bank_account(user, account):
    if not account:
        return False
    return user == account.user


@rules.predicate
def is_self(user, user_obj):
    if not user_obj:
        return True
    return user == user_obj



