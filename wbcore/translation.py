# -*- coding: utf-8 -*-
"""
Necessary for the modeltranslation package 

"""

from modeltranslation.translator import register, TranslationOptions
from .models import Project, Location, Address, Host, Partner, Event, Post, Document, Team, Milestep

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
    fields = ('name','description',)
    
@register(Post)
class PostTranslationOptions(TranslationOptions):
    fields = ('title','text', 'img_alt', 'teaser')
    
@register(Document)
class DocumentTranslationOptions(TranslationOptions):
    fields = ('title','description')
    
@register(Team)
class TeamTranslationOptions(TranslationOptions):
    fields = ('name','description')

@register(Milestep)
class MilestepTranslationOptions(TranslationOptions):
    fields = ('name','description')