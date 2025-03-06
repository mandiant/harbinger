# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from harbinger.database import models
from harbinger.config import admin

from sqlalchemy.orm.decl_api import DeclarativeMeta

import unittest
from sqladmin.models import ModelViewMeta


class TestAdminModels(unittest.IsolatedAsyncioTestCase):

    def test_admin_models(self):
        database_objects = dict(
            [
                (name, cls)
                for name, cls in models.__dict__.items()
                if type(cls) == DeclarativeMeta
            ]
        )   

        admin_models = dict(
            [
                (name, cls)
                for name, cls in admin.__dict__.items()
                if type(cls) == ModelViewMeta and name != 'ModelView'
            ]
        ) 
        for name, value in admin_models.items():
            self.assertNotEqual(getattr(value, 'name'), '', f'name of {name} is unset')
            self.assertIn(getattr(value, 'name'), database_objects, f'{name} is missing from the database objects')
