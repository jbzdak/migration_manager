# -*- coding: utf-8 -*-
from django.core import exceptions
from django.utils.importlib import import_module

__author__ = 'jb'


MIGRATION_MANAGERS = {}

DEFAULT_MANAGER = None

def load_manager(path):
    """
        Code taken from django.

        Copyright (c) Django Software Foundation and individual contributors.
        All rights reserved.

        Redistribution and use in source and binary forms, with or without modification,
        are permitted provided that the following conditions are met:

            1. Redistributions of source code must retain the above copyright notice,
               this list of conditions and the following disclaimer.

            2. Redistributions in binary form must reproduce the above copyright
               notice, this list of conditions and the following disclaimer in the
               documentation and/or other materials provided with the distribution.

            3. Neither the name of Django nor the names of its contributors may be used
               to endorse or promote products derived from this software without
               specific prior written permission.

        THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
        ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
        WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
        DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
        ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
        (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
        LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
        ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
        (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
        SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

    """
    try:
       mw_module, mw_classname = path.rsplit('.', 1)
    except ValueError:
       raise exceptions.ImproperlyConfigured('%s isn\'t a manager module' % path)
    try:
       mod = import_module(mw_module)
    except ImportError, e:
       raise exceptions.ImproperlyConfigured('Error importing manager %s: "%s"' % (mw_module, e))
    try:
       manager_instance = getattr(mod, mw_classname)
    except AttributeError:
       raise exceptions.ImproperlyConfigured('Manager module "%s" does not define a "%s" object' % (mw_module, mw_classname))
    return manager_instance

def initialize():
    from django.conf import settings

    global MIGRATION_MANAGERS, DEFAULT_MANAGER

    MANAGERS = getattr(settings, "MIGRATION_MANAGERS", None)

    if MANAGERS is not None:
        for k, v in MANAGERS:
            MIGRATION_MANAGERS[k] = load_manager(v)

        DEFAULT_MANAGER = MIGRATION_MANAGERS[MANAGERS[0][0]]

initialize()