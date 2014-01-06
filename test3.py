# -*- coding: utf-8 -*-
'''
Created on Dec 30, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from StringIO import StringIO
import tokenize
import keyword
import token

def runit(s):
    result = []
    g = tokenize.generate_tokens(StringIO(s).readline)   # tokenize the string
    for toknum, tokval, _1, _2, _3  in g:
        if toknum == tokenize.NAME and not keyword.iskeyword(tokval):
           result.append("Eval('%s')" % tokval)
        elif tokenize.OP == toknum:
           result.append(tokval)
    return " ".join(result)
  
t = 1

t