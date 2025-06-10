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

import uuid
import yaml
from harbinger.database import crud, schemas
from sqlalchemy.exc import IntegrityError
from harbinger.config import get_settings
from pydantic import ValidationError
import collections
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from yaml.scanner import ScannerError

settings = get_settings()

log = structlog.get_logger()

_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


# https://stackoverflow.com/a/33300001
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


# https://stackoverflow.com/a/21048064
def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())


# https://stackoverflow.com/a/77775117
def uuid_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


def dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))


def getattr_representer(dumper, data: schemas.TypeEnum):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data.value)


def none_representer(dumper, entry):
    return dumper.represent_scalar("tag:yaml.org,2002:null", "")


yaml.add_representer(schemas.TypeEnum, getattr_representer)
yaml.add_representer(collections.OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)
yaml.add_representer(str, str_presenter)
yaml.add_representer(uuid.UUID, uuid_representer)
yaml.add_representer(type(None), none_representer)


async def process_harbinger_yaml(
    db: AsyncSession, yaml_data: bytes | str
) -> list[schemas.FileConfig] | None:
    try:
        entry = yaml.safe_load(yaml_data)
        config = schemas.HarbingerYaml(**entry)
        for server in config.c2_server_types or []:
            created, obj = await crud.create_c2_server_type(
                db,
                schemas.C2ServerTypeCreate(
                    id=server.id,
                    name=server.name,
                    docker_image=server.docker_image,
                    command=server.command,
                    icon=server.icon_base64,
                ),
            )
            if not created:
                await crud.delete_c2_server_arguments(db, obj.id)
            for argument in server.required_arguments or []:
                await crud.create_c2_server_argument(
                    db,
                    schemas.C2ServerArgumentsCreate(
                        name=argument.name,
                        regex=argument.regex,
                        default=str(argument.default) if argument.default else None,
                        error=(
                            argument.error
                            if argument.error
                            else "Please fill in this value"
                        ),
                        type=(
                            argument.type
                            if argument.type
                            else argument.default_type()
                        ),
                        c2_server_type_id=obj.id,
                    ),
                )
        await db.commit()
        for label in config.labels or []:
            try:
                await crud.create_label(
                    db,
                    label,
                )
            except IntegrityError:
                await db.rollback()
        for category in config.setting_categories or []:
            c_db = await crud.create_setting_category(db, category)
            for setting in category.settings:
                setting.category_id = c_db.id
                await crud.create_setting(db, setting)
        for playbook in config.playbooks or []:
            dump = playbook.model_dump(exclude_unset=True)

            for arg in dump["args"]:
                arg["type"] = arg["type"].value

            myorder = [
                "id",
                "name",
                "icon",
                "tactic",
                "technique",
                "labels",
                "add_depends_on",
                "args",
                "steps",
            ]
            ordered = collections.OrderedDict()
            for k in myorder:
                try:
                    ordered[k] = dump[k]
                except KeyError:
                    pass

            playbook.yaml = yaml.dump(ordered)
            await crud.create_playbook_template(db, playbook)
        for action in config.actions or []:
            await crud.create_action(db, action)
        for c2_server in config.c2_servers or []:
            await crud.create_c2_server(db, c2_server)
        return config.files
    except ValidationError as e:
        log.warning(e)
    except TypeError as e:
        log.warning(e)
    except ScannerError as e:
        log.warning(e)
    return None
