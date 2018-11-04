# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok / WMS Examples project
#
#    Copyright (C) 2018 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.

# we'll use 0.8.x to indicate that the target AWB version is 0.8
# patch version and dev/post etc can differ. 0.8.0dev0 means that it's
# the first version of examples for 0.8, and it's still in development"
version = '0.8.0.dev0'


def init_config(**kw):
    from .launcher import config  # flake8: noqa
