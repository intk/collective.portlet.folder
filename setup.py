from setuptools import setup, find_packages

version = '0.0.2'

setup(name='collective.portlet.foldercontents',
      version=version,
      description="A portlet that fetches results from a folder",
      long_description=open("README.rst").read() + "\n" +
      open("CHANGES.rst").read(),
      classifiers=[
          "Environment :: Web Environment",
          "Framework :: Plone",
          "Framework :: Plone :: 5.0",
          "Framework :: Plone :: 5.1",
          "Framework :: Zope2",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
      ],
      keywords='folder contents portlet',
      author='INTK',
      author_email='andre@intk.com',
      url='https://github.com/intk/collective.portlet.folder',
      license='GPL version 2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective', "collective.portlet"],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.memoize',
          'plone.portlets',
          'plone.app.portlets',
          'plone.app.vocabularies',
      ],
      extras_require={
          'test': [
              'plone.app.testing',
              'plone.app.contenttypes',
          ],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """
      )
