# -*- coding: utf-8 -*-
from zope.interface import alsoProvides, implements
from zope.component import adapts
from zope import schema
from plone.supermodel import model
from plone.dexterity.interfaces import IDexterityContainer
from plone.autoform.interfaces import IFormFieldProvider
from plone.app.uuid.utils import uuidToCatalogBrain, uuidToObject
from plone.namedfile import field as namedfile
from zope.component._api import getMultiAdapter
from zope.component._api import getUtility
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletAssignmentSettings
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.app.contenttypes import _
from zope.container.interfaces import INameChooser
from collective.portlet.foldercontents.folder import Assignment as FolderAssignment
import plone.api

class IDownloads(model.Schema):
	pass

class Downloads(object):
	implements(IDownloads)
	adapts(IDexterityContainer)

	def __init__(self, context):
		self.context = context


def createPortlet(uid):
    portlet = None

    try:
        portlet = FolderAssignment(header=u"Downloads", uid=uid, limit=None,
                random=False, show_more=False, show_dates=False,
                exclude_context=False)
    except:
        pass
    return portlet

def addPortletToContext(context, portlet, columnName="plone.rightcolumn"):
    if not portlet:
        return

    column = getUtility(IPortletManager, columnName)
    manager = getMultiAdapter((context, column), IPortletAssignmentMapping)
    chooser = INameChooser(manager)
    manager[chooser.chooseName(None, portlet)] = portlet

def newObjectAdded(obj, event):
    if IDownloads.providedBy(obj):
        try:
            downloads_folder = plone.api.content.create(container=obj, type="Folder", id="downloads", title="Downloads")
            plone.api.content.transition(obj=downloads_folder, to_state="published")
        except:
            pass

        try:
            # Create the portlet automatically
            portlet = createPortlet(downloads_folder.UID())
            if portlet:
                addPortletToContext(obj, portlet)
        except:
            raise
    else:
        return False





