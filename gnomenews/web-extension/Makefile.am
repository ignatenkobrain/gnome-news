AM_CFLAGS = $(WARN_CFLAGS)
AM_LDFLAGS = $(WARN_LDFLAGS)

pkglib_LTLIBRARIES = libnewswebextension.la

libnewswebextension_la_SOURCES = \
	web-extension-main.c

libnewswebextension_la_CPPFLAGS = \
	$(WEB_EXTENSION_CFLAGS)

libnewswebextension_la_LIBADD = \
	$(WEB_EXTENSION_LIBS)

libnewswebextension_la_LDFLAGS = \
	-module -avoid-version -no-undefined

-include $(top_srcdir)/git.mk
