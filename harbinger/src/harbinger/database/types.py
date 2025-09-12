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

from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import Column

_T = TypeVar("_T")

if TYPE_CHECKING:
    from sqlalchemy.orm import Mapped
    from sqlalchemy.types import TypeEngine

    class mapped_column(Mapped[_T]):
        def __init__(
            self,
            __typ: TypeEngine[_T] | type[TypeEngine[_T]] | Any | None,
            *arg,
            **kw,
        ): ...

else:
    mapped_column = Column
