# -*- coding: utf-8 -*-
'''
Created on Oct 8, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json


class JSONEncoderHTML(json.JSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    """
  
    def iterencode(self, o, _one_shot=False):
        chunks = super(JSONEncoderHTML, self).iterencode(o, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')
            yield chunk