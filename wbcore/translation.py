# -*- coding: utf-8 -*-
"""
Necessary for the modeltranslation package

"""

from modeltranslation.translator import register, TranslationOptions
from .models import Project, Location, Address, Host, Partner, Event, NewsPost, BlogPost, Document, Team, Milestep, Content

@register(Content)
class ContentTranslationOptions(TranslationOptions):
    fields = ('text',)

@register(Project)
class ProjectTranslationOptions(TranslationOptions):
    fields = ('name','short_description', 'description',)

@register(Location)
class LocationTranslationOptions(TranslationOptions):
    fields = ('name','city','description',)

@register(Address)
class AddressTranslationOptions(TranslationOptions):
    fields = ('name','city',)
    prepopulated_fields={'name':'all'}

@register(Host)
class HostTranslationOptions(TranslationOptions):
    fields = ('city',)

@register(Partner)
class PartnerTranslationOptions(TranslationOptions):
    fields = ('name','description',)

@register(Event)
class EventTranslationOptions(TranslationOptions):
    fields = ('title','description',)

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
