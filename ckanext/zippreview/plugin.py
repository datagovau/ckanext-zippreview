import ckan.plugins as p
import ckan.plugins.toolkit as tk

import ckanext.zippreview.utils as utils
from ckanext.zippreview.helpers import get_helpers


class ZipPreviewPlugin (p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IResourceView, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=False)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'ckanext-zippreview')

    # ITemplateHelpers

    def get_helpers(self):
        return get_helpers()

    # IResourceView

    def info(self):
        return {
            'name': 'zip_view',
            'title': 'ZIP Viewer',
            'default_title': 'ZIP Viewer',
            'icon': 'folder-open'
        }

    def can_view(self, data_dict):
        return utils.is_resource_supported(data_dict['resource'])

    def view_template(self, context, data_dict):
        return 'zip.html'
