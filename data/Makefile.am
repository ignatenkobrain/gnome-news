EXTRA_DIST = \
	$(NULL)

resource_files = $(shell $(GLIB_COMPILE_RESOURCES) --sourcedir=$(srcdir) --sourcedir=$(builddir) --generate-dependencies $(builddir)/gnome-news.gresource.xml) 
gnome-news.gresource: gnome-news.gresource.xml $(resource_files)
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir) --sourcedir=$(builddir) $<

resourcedir = $(pkgdatadir)
resource_DATA = gnome-news.gresource

appsdir = $(datadir)/applications
apps_DATA = gnome-news.desktop

@INTLTOOL_DESKTOP_RULE@

# AppData
appstream_in_files = gnome-news.appdata.xml.in
appstream_XML = $(appstream_in_files:.appdata.xml.in=.appdata.xml)

@APPSTREAM_XML_RULES@
@INTLTOOL_XML_RULE@

# GSettings
gsettings_SCHEMAS = org.gnome.News.gschema.xml

# For uninstalled use
gschemas.compiled: $(gsettings_SCHEMAS) Makefile
	$(AM_V_GEN) $(GLIB_COMPILE_SCHEMAS) $(builddir)

@GSETTINGS_RULES@

EXTRA_DIST = \
	$(resource_files) \
	$(appstream_in_files) \
	gnome-news.desktop.in \
	gnome-news.gresource.xml \
	org.gnome.News.gschema.xml \
	$(NULL)

CLEANFILES = \
	gnome-news.gresource \
	$(appstream_XML) \
	$(apps_DATA) \
	*.valid \
	gschemas.compiled \
	$(NULL)

all-local: gschemas.compiled

-include $(top_srcdir)/git.mk
