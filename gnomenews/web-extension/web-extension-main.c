/* -*- Mode: C++; tab-width: 2; indent-tabs-mode: nil; c-basic-offset: 2 -*-
 *
 *  Copyright © 2015 Michael Catanzaro <mcatanzaro@gnome.org>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 3, or (at your option)
 *  any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <webkit2/webkit-web-extension.h>
#include <webkitdom/webkitdom.h>

static const int MAX_ELEMENT_WIDTH = 630;

static void
shrink_image_if_needed (WebKitDOMHTMLImageElement *image_element)
{
  float scale_percentage;
  glong new_height;
  glong original_width = webkit_dom_html_image_element_get_width (image_element);
  glong original_height = webkit_dom_html_image_element_get_height (image_element);

  if (original_width <= MAX_ELEMENT_WIDTH)
    return;

  scale_percentage = MAX_ELEMENT_WIDTH / (float)original_width;
  new_height = original_height * scale_percentage;

  webkit_dom_html_image_element_set_width (image_element, MAX_ELEMENT_WIDTH);
  webkit_dom_html_image_element_set_height (image_element, new_height);
}

static void
shrink_large_images (WebKitDOMDocument *document)
{
  WebKitDOMHTMLCollection *collection = webkit_dom_document_get_images (document);

  for (gulong i = 0; i < webkit_dom_html_collection_get_length (collection); i++)
    {
      WebKitDOMHTMLImageElement *image_element =
          WEBKIT_DOM_HTML_IMAGE_ELEMENT (webkit_dom_html_collection_item (collection, i));
      shrink_image_if_needed (image_element);
    }

  g_object_unref (collection);
}

static void
document_loaded_cb (WebKitWebPage *web_page,
                    gpointer user_data)
{
  WebKitDOMDocument *document = webkit_web_page_get_dom_document (web_page);

  shrink_large_images (document);
}

static void
page_created_cb (WebKitWebExtension *extension,
                 WebKitWebPage      *web_page,
                 gpointer            user_data)
{
  g_signal_connect (web_page, "document-loaded", G_CALLBACK (document_loaded_cb), NULL);
}

#pragma GCC diagnostic ignored "-Wmissing-prototypes"

G_MODULE_EXPORT void
webkit_web_extension_initialize (WebKitWebExtension *extension)
{
  g_signal_connect (extension, "page-created", G_CALLBACK (page_created_cb), NULL);
}
