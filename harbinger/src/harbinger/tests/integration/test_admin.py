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

from harbinger import models
from harbinger.config import admin
from sqladmin.models import ModelViewMeta
from sqlalchemy.orm.decl_api import DeclarativeMeta


def test_admin_models():
    """
    Tests that all SQLAdmin ModelViews are correctly configured and map to a real SQLAlchemy model.
    """
    database_objects = {name: cls for name, cls in models.__dict__.items() if isinstance(cls, DeclarativeMeta)}

    admin_models = {
        name: cls for name, cls in admin.__dict__.items() if isinstance(cls, ModelViewMeta) and name != "ModelView"
    }

    assert admin_models, "No SQLAdmin ModelViews were found to test."

    for name, value in admin_models.items():
        assert value.name != "", f"The `name` attribute of the ModelView '{name}' is unset."
        assert (
            value.name in database_objects
        ), f"The ModelView '{name}' points to a database object '{value.name}' that does not exist."
