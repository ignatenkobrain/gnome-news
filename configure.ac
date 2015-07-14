AC_INIT([GNOME News],
        [0.0.1],
        [https://github.com/ignatenkobrain/gnome-news/issues/new],
        [gnome-news],
        [https://wiki.gnome.org/Design/Apps/Potential/News])
AX_IS_RELEASE([git-directory])

AM_INIT_AUTOMAKE([check-news dist-xz no-dist-gzip subdir-objects])
AC_CONFIG_MACRO_DIR([m4])
AM_MAINTAINER_MODE([enable])
m4_ifdef([AM_SILENT_RULES], [AM_SILENT_RULES([yes])])

AM_PATH_PYTHON([3.4])

PKG_PROG_PKG_CONFIG([0.22])
m4_define([pygobject_required_version], [3.0.0])
PKG_CHECK_MODULES(PYGOBJECT, pygobject-3.0 >= pygobject_required_version)

# GResources
AC_PATH_PROG([GLIB_COMPILE_RESOURCES], [glib-compile-resources])

# Internationalisation
GETTEXT_PACKAGE=gnome-news
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], ["$GETTEXT_PACKAGE"], [gettext package name])
IT_PROG_INTLTOOL([0.50.2])

# GSettings
GLIB_GSETTINGS

# AppData
APPSTREAM_XML

AC_CONFIG_FILES([
  Makefile
  data/Makefile
  gnomenews/Makefile
  po/Makefile.in
])
AC_OUTPUT
