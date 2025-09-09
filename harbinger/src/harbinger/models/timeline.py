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

from sqlalchemy import DateTime, String
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import Mapped

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class TimeLine(AbstractConcreteBase, Base):
    strict_attrs = True
    time_started: Mapped[DateTime] = mapped_column(DateTime(timezone=True))                                                                             
    time_completed: Mapped[DateTime] = mapped_column(DateTime(timezone=True))                                                                             
    status: Mapped[str] = mapped_column(String)
    ai_summary: Mapped[str] = mapped_column(String)
    processing_status: Mapped[str] = mapped_column(String)
