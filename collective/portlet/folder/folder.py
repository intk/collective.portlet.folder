from ComputedAttribute import ComputedAttribute
from plone.app.layout.navigation.defaultpage import isDefaultPage
from plone.app.portlets.browser import formhelper
from plone.app.portlets.portlets import base
from plone.app.uuid.utils import uuidToObject
from plone.app.vocabularies.catalog import CatalogSource
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.instance import memoize
from plone.portlet.collection import PloneMessageFactory as _
from plone.portlets.interfaces import IPortletDataProvider
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import NotFound
from zope import schema
from zope.component import getUtility
from zope.interface import implementer
import random

COLLECTIONS = []

try:
    from plone.app.collection.interfaces import ICollection
    COLLECTIONS.append(ICollection.__identifier__)
except ImportError:
    pass

try:
    from plone.app.contenttypes.interfaces import ICollection
    COLLECTIONS.append(ICollection.__identifier__)
except ImportError:
    pass


class IFolderPortlet(IPortletDataProvider):
    """A portlet which renders the results of a folder object.
    """

    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of the rendered portlet"),
        required=True)

    uid = schema.Choice(
        title=_(u"Target folder"),
        description=_(u"Find the folder which provides the items to list"),
        required=True,
        source=CatalogSource(portal_type=('Folder')),
        )

    limit = schema.Int(
        title=_(u"Limit"),
        description=_(u"Specify the maximum number of items to show in the "
                      u"portlet. Leave this blank to show all items."),
        required=False)

    random = schema.Bool(
        title=_(u"Select random items"),
        description=_(u"If enabled, items will be selected randomly from the "
                      u"folder, rather than based on its sort order."),
        required=True,
        default=False)

    show_more = schema.Bool(
        title=_(u"Show more... link"),
        description=_(u"If enabled, a more... link will appear in the footer "
                      u"of the portlet, linking to the underlying "
                      u"Folder."),
        required=True,
        default=True)

    show_dates = schema.Bool(
        title=_(u"Show dates"),
        description=_(u"If enabled, effective dates will be shown underneath "
                      u"the items listed."),
        required=True,
        default=False)

    exclude_context = schema.Bool(
        title=_(u"Exclude the Current Context"),
        description=_(
            u"If enabled, the listing will not include the current item the "
            u"portlet is rendered for if it otherwise would be."),
        required=True,
        default=True)


@implementer(IFolderPortlet)
class Assignment(base.Assignment):
    """
    Portlet assignment.
    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    header = u""
    limit = None
    random = False
    show_more = True
    show_dates = False
    exclude_context = False

    # bbb
    target_folder = None

    def __init__(self, header=u"", uid=None, limit=None,
                 random=False, show_more=True, show_dates=False,
                 exclude_context=True):
        self.header = header
        self.uid = uid
        self.limit = limit
        self.random = random
        self.show_more = show_more
        self.show_dates = show_dates
        self.exclude_context = exclude_context

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen. Here, we use the title that the user gave.
        """
        return self.header

    def _uid(self):
        # This is only called if the instance doesn't have a uid
        # attribute, which is probably because it has an old
        # 'target_folder' attribute that needs to be converted.
        path = self.target_folder
        portal = getToolByName(self, 'portal_url').getPortalObject()
        try:
            folder = portal.unrestrictedTraverse(path.lstrip('/'))
        except (AttributeError, KeyError, TypeError, NotFound):
            return
        return folder.UID()
    uid = ComputedAttribute(_uid, 1)


class Renderer(base.Renderer):

    _template = ViewPageTemplateFile('folder.pt')
    render = _template

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

    @property
    def available(self):
        return len(self.results())

    def folder_url(self):
        folder = self.folder()
        if folder is None:
            return
        parent = folder.aq_parent
        if isDefaultPage(parent, folder):
            folder = parent
        return folder.absolute_url()

    def css_class(self):
        header = self.data.header
        normalizer = getUtility(IIDNormalizer)
        return "portlet-folder-%s" % normalizer.normalize(header)

    @memoize
    def results(self):
        if self.data.random:
            return self._random_results()
        else:
            return self._standard_results()

    def _standard_results(self):
        results = []
        folder = self.folder()
        if folder is not None:
            context_path = '/'.join(self.context.getPhysicalPath())
            exclude_context = getattr(self.data, 'exclude_context', False)
            limit = self.data.limit
            if limit and limit > 0:
                # pass on batching hints to the catalog
                results = folder.getFolderContents()
                results = results._sequence
            else:
                results = folder.getFolderContents()
            if exclude_context:
                results = [
                    brain for brain in results
                    if brain.getPath() != context_path]
            if limit and limit > 0:
                results = results[:limit]
        return results

    def _random_results(self):
        # intentionally non-memoized
        results = []
        folder = self.folder()
        if folder is not None:
            context_path = '/'.join(self.context.getPhysicalPath())
            exclude_context = getattr(self.data, 'exclude_context', False)
            results = folder.getFolderContents()
            if results is None:
                return []
            limit = self.data.limit and min(len(results), self.data.limit) or 1

            if exclude_context:
                results = [
                    brain for brain in results
                    if brain.getPath() != context_path]
            if len(results) < limit:
                limit = len(results)
            results = random.sample(results, limit)

        return results

    @memoize
    def folder(self):
        return uuidToObject(self.data.uid)

    def include_empty_footer(self):
        """
        Whether or not to include an empty footer element when the more
        link is turned off.
        Always returns True (this method provides a hook for
        sub-classes to override the default behaviour).
        """
        return True


class AddForm(formhelper.AddForm):
    schema = IFolderPortlet
    label = _(u"Add Folder Portlet")
    description = _(u"This portlet displays a listing of items from a "
                    u"Folder.")

    def create(self, data):
        return Assignment(**data)


class EditForm(formhelper.EditForm):
    schema = IFolderPortlet
    label = _(u"Edit Folder Portlet")
    description = _(u"This portlet displays a listing of items from a "
                    u"Folder.")
