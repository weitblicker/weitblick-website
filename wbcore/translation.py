# -*- coding: utf-8 -*-
"""
Necessary for the modeltranslation package 

"""

from modeltranslation.translator import register, TranslationOptions
from .models import Project, Location

@register(Project)
class ProjectTranslationOptions(TranslationOptions):
    fields = ('name','short_description', 'description',)

@register(Location)
class LocationTranslationOptions(TranslationOptions):
    fields = ('name','description',)