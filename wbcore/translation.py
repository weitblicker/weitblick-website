# -*- coding: utf-8 -*-
"""
Necessary for the modeltranslation package

"""

from modeltranslation.translator import register, TranslationOptions
from .models import (
    Project, Location, Address, Host, Partner, NewsPost, BlogPost,
    Document, Team, Milestep, Content, Event, Milestone, Donation,
    BankAccount, ContactMessage, CycleDonation, CycleDonationRelation, Segment
)
from schedule.models.events import Event as ScheduleEvent


@register(Content)
class ContentTranslationOptions(TranslationOptions):
    fields = ('text',)


@register(Project)
class ProjectTranslationOptions(TranslationOptions):
    fields = ('name','short_description', 'description',)


@register(Location)
class LocationTranslationOptions(TranslationOptions):
    fields = ('name','city','description',)


@register(Host)
class HostTranslationOptions(TranslationOptions):
    fields = ('city',)


@register(Partner)
class PartnerTranslationOptions(TranslationOptions):
    fields = ('name','description',)


@register(ScheduleEvent)
class ScheduleEventTranslationOptions(TranslationOptions):
    fields = ()


@register(Event)
class EventTranslationOptions(ScheduleEventTranslationOptions):
    fields = ('title', 'description',)


@register(NewsPost)
class NewsPostTranslationOptions(TranslationOptions):
    fields = ('title','text', 'teaser')


@register(BlogPost)
class BlogPostTranslationOptions(TranslationOptions):
    fields = ('title', 'text', 'teaser')


@register(Document)
class DocumentTranslationOptions(TranslationOptions):
    fields = ('title','description')


@register(Team)
class TeamTranslationOptions(TranslationOptions):
    fields = ('name','description')


@register(Milestep)
class MilestepTranslationOptions(TranslationOptions):
    fields = ('name','description')


@register([BankAccount, Donation, Milestone, ContactMessage, Address, CycleDonation, Segment])
class BankAccountTranslationOptions(TranslationOptions):
    pass

