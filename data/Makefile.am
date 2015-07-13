# Desktop file
@INTLTOOL_DESKTOP_RULE@
desktopdir = $(datadir)/applications
desktop_in_files = org.gnome.News.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)

# GSettings
@GSETTINGS_RULES@
gsettings_SCHEMAS = org.gnome.News.gschema.xml
# For uninstalled use
gschemas.compiled: $(gsettings_SCHEMAS) Makefile
	$(AM_V_GEN) $(GLIB_COMPILE_SCHEMAS) $(builddir)

# AppData
@INTLTOOL_XML_RULE@
@APPSTREAM_XML_RULES@
appstream_in_files = org.gnome.News.appdata.xml.in
appstream_XML = $(appstream_in_files:.appdata.xml.in=.appdata.xml)

resource_files = $(shell $(GLIB_COMPILE_RESOURCES) --sourcedir=$(srcdir) --sourcedir=$(builddir) --generate-dependencies $(builddir)/gnome-news.gresource.xml) 
gnome-news.gresource: gnome-news.gresource.xml $(resource_files)
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir) --sourcedir=$(builddir) $<

resourcedir = $(pkgdatadir)
resource_DATA = gnome-news.gresource

EXTRA_DIST = \
	$(desktop_in_files) \
	$(appstream_in_files) \
	$(gsettings_SCHEMAS) \
	$(resource_files) \
	gnome-news.gresource.xml \
	$(NULL)

CLEANFILES = \
	$(desktop_DATA) \
	gnome-news.gresource \
	$(appstream_XML) \
	*.valid \
	gschemas.compiled \
	$(NULL)

all-local: gschemas.compiled

-include $(top_srcdir)/git.mk
