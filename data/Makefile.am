resource_files = $(shell $(GLIB_COMPILE_RESOURCES) --sourcedir=$(srcdir) --sourcedir=$(builddir) --generate-dependencies $(builddir)/gnome-news.gresource.xml) 
gnome-news.gresource: gnome-news.gresource.xml $(resource_files)
	$(AM_V_GEN) $(GLIB_COMPILE_RESOURCES) --target=$@ --sourcedir=$(srcdir) --sourcedir=$(builddir) $<

resourcedir = $(pkgdatadir)
resource_DATA = gnome-news.gresource

appsdir = $(datadir)/applications
apps_DATA = gnome-news.desktop

@INTLTOOL_DESKTOP_RULE@

appdatadir = $(datadir)/appdata
appdata_DATA = $(appdata_in_files:.xml.in=.xml)
appdata_in_files = gnome-news.appdata.xml.in

@INTLTOOL_XML_RULE@

man1_MANS = gnome-news.1

gsettings_SCHEMAS = org.gnome.News.gschema.xml

# For uninstalled use
gschemas.compiled: $(gsettings_SCHEMAS) Makefile
	$(AM_V_GEN) $(GLIB_COMPILE_SCHEMAS) $(builddir)

@GSETTINGS_RULES@

EXTRA_DIST = \
	$(resource_files) \
	gnome-news.appdata.xml.in \
	gnome-news.desktop.in \
	gnome-news.gresource.xml \
	org.gnome.News.gschema.xml \
	$(man1_MANS) \
	$(NULL)

CLEANFILES = \
	gnome-news.gresource \
	gnome-news.appdata.xml \
	$(apps_DATA) \
	*.valid \
	gschemas.compiled \
	$(NULL)

all-local: gschemas.compiled

-include $(top_srcdir)/git.mk
