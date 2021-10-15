
=============
ckanext-zippreview
=============

Preview contents of ZIP files, even if they are hosted on external sites!

------------
Requirements
------------

CKAN 2.3+ (Resource view support)

------------
Installation
------------

To install ckanext-zippreview:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-zippreview Python package into your virtual environment::

     pip install ckanext-zippreview

3. Add ``zip_view`` to the ``ckan.plugins`` setting and ``ckan.views.default_views`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


------------------------
Development Installation
------------------------

To install ckanext-zippreview for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/datagovau/ckanext-zippreview.git
    cd ckanext-zippreview
    python setup.py develop
    pip install -r dev-requirements.txt
