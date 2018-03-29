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
from plone.app.uuid.utils import uuidToCatalogBrain
from plone.app.event.browser.formatted_date import FormattedDateProvider
from zope.contentprovider.interfaces import IContentProvider
from plone.event.interfaces import IEvent
from zope.component import getMultiAdapter

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

    archive_images = schema.Bool(
        title=_(u"Activate archive images style"),
        description=_(u"If enabled, the images will be rendered with the archive style"),
        required=False,
        default=False)

    start_from = schema.Int(
        title=_(u"Item in the folder to start showing the archive"),
        description=_(u"Item in the folder to start showing the archive"),
        required=False)




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
    archive_images = False
    start_from = None

    # bbb
    target_folder = None

    def __init__(self, header=u"", uid=None, limit=None,
                 random=False, show_more=True, show_dates=False,
                 exclude_context=True, archive_images=False, start_from=None):
        self.header = header
        self.uid = uid
        self.limit = limit
        self.random = random
        self.show_more = show_more
        self.show_dates = show_dates
        self.exclude_context = exclude_context
        self.archive_images = archive_images
        self.start_from = start_from

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

    def show_archive(self):
        return self.data.archive_images

    def find_orientation(self, item):
        if type(item) == str:
            if item == "L":
                return "landscape"
            else:
                return "portrait"

        item_class = ""
        if item.portal_type == "Image":
            image_obj = item.getObject()
            if getattr(image_obj, 'image', None):
                try:
                    w, h = image_obj.image.getImageSize()
                    if w > h:
                        item_class = "%s" %('landscape')
                    else:
                        item_class = "%s" %('portrait')
                except:
                    return item_class
        elif item.hasMedia:
            image = uuidToCatalogBrain(item.leadMedia)
            image_obj = image.getObject()
            if getattr(image_obj, 'image', None):
                try:
                    w, h = image_obj.image.getImageSize()
                    if w > h:
                        item_class = "%s" %('landscape')
                    else:
                        item_class = "%s" %('portrait')
                except:
                    return item_class

        return item_class

    def getImageProperties(self, item):
        link = item.getURL()+"/view"
        title = item.Title
        description = item.Description

        try:
            if item.portal_type == "Image":
                image = item.getObject()
                parent = image.aq_parent
                if parent.portal_type == "Folder":
                    if parent.id == "slideshow":
                        obj = parent.aq_parent
                        if obj.portal_type == "Object":
                            title = obj.title
                            description = obj.description
                            link = obj.absolute_url()

        except:
            raise

        return {"link": link, "title": title, "description": description}

    def getImageClass(self, item, has_media=False):

        item_class = "entry"

        if item.portal_type == "Image":
            image_obj = item.getObject()
            if getattr(image_obj, 'image', None):
                try:
                    w, h = image_obj.image.getImageSize()
                    if w > h:
                        item_class = "%s %s" %(item_class, 'landscape')
                    else:
                        item_class = "%s %s" %(item_class, 'portrait')
                except:
                    return item_class
        elif has_media:
            image = uuidToCatalogBrain(item.leadMedia)
            image_obj = image.getObject()
            if getattr(image_obj, 'image', None):
                try:
                    w, h = image_obj.image.getImageSize()
                    if w > h:
                        item_class = "%s %s" %(item_class, 'landscape')
                    else:
                        item_class = "%s %s" %(item_class, 'portrait')
                except:
                    return item_class

        return item_class
        
    def pairItems(self, results):
        # L P L L L P P P
        TEST_INPUT = ["L", "P", "L", "L", "L", "P", "P", "P"]
        FIRST_ITEM = 0
        
        items = results
        total_items = len(items)
        items_checked = []
        final_patterns = []

        right = True
        previous_pair = ""

        for i in range(total_items):
            if i not in items_checked:

                right_pattern = "right" if right else "left"
                pattern = {
                    "size": "small",
                    "orientation": self.find_orientation(items[i]),
                    "position": "pair",
                    "clearfix": False,
                    "item": items[i],
                    "right": right_pattern,
                    "bottom": ""
                }
               
                if i == FIRST_ITEM:
                    pattern['position'] = "single"
                    pattern['size'] = "big"
                    final_patterns.append(pattern)
                    items_checked.append(i)
                    if right:
                        right = False
                    else:
                        right = True
                else:
                    if i+1 < total_items:
                        next_orientation = self.find_orientation(items[i+1])

                        if next_orientation == pattern["orientation"] == "landscape":
                            pattern["position"] = "single"
                            pattern["size"] = "big"
                            final_patterns.append(pattern)
                            if right:
                                right = False
                            else:
                                right = True

                            previous_pair = ""
                        else:
                            new_pattern = {
                                "size": pattern['size'],
                                "orientation": pattern['orientation'],
                                "position": "pair",
                                "clearfix": True,
                                "item": items[i+1],
                                "right": pattern['right'],
                                "bottom": pattern['bottom']
                            }
                            new_pattern["orientation"] = next_orientation

                            if next_orientation == pattern['orientation'] == "portrait":
                                pattern['size'] = "big"
                                new_pattern['size'] = "big"

                            if not previous_pair:
                                if right:
                                    pattern['bottom'] = "bottom"
                                    new_pattern['bottom'] = "up"
                                else:
                                    new_pattern['bottom'] = "bottom"
                                    pattern['bottom'] = "up"
                            else:
                                if previous_pair == "bottom":
                                    pattern['bottom'] = "up"
                                    new_pattern['bottom'] = "bottom"
                                    previous_pair = "bottom"
                                else:
                                    pattern['bottom'] = "bottom"
                                    new_pattern['bottom'] = "up"
                                    previous_pair = "up"

                            final_patterns.append(pattern)
                            final_patterns.append(new_pattern)
                            items_checked.append(i)
                            items_checked.append(i+1)
                    else:
                        pattern['position'] = "single"
                        pattern['size'] = "big"
                        final_patterns.append(pattern)
            else:
                pass

        return final_patterns

    def getImageObject(self, item):
        if item.portal_type == "Image":
            return item.getURL()+"/@@images/image/mini"
        if item.leadMedia != None:
            uuid = item.leadMedia
            media_object = uuidToCatalogBrain(uuid)
            if media_object:
                return media_object.getURL()+"/@@images/image/mini"
            else:
                return None
        else:
            return None

    def getImageScale(self, item, scale="large"):
        if item.portal_type == "Image":
            return item.getURL()+"/@@images/image/%s" %(scale)
        if getattr(item, 'leadMedia', None) != None:
            uuid = item.leadMedia
            media_object = uuidToCatalogBrain(uuid)
            if media_object:
                return media_object.getURL()+"/@@images/image/%s" %(scale)
            else:
                return None
        else:
            return None

    def is_event(self, obj):
        if getattr(obj, 'getObject', False):
            obj = obj.getObject()
        return IEvent.providedBy(obj)

    def formatted_date(self, obj):
        item = obj.getObject()
        provider = getMultiAdapter(
            (self.context, self.request, self),
            IContentProvider, name='formatted_date'
        )
        return provider(item)

    def date_speller(self, date):
        return date_speller(self.context, date)

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
            start_from = self.data.start_from
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
            
            if start_from and start_from > 0:
                try:
                    results = results[start_from:len(results)-1]
                except:
                    raise
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
