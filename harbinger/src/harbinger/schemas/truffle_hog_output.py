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


from pydantic import (BaseModel, Field)


from .truffle_hog import THSourceMetadata


class TruffleHogOutput(BaseModel):
    source_meta_data: THSourceMetadata | None = Field(
        validation_alias="SourceMetadata", default=None
    )
    source_id: int | None = Field(validation_alias="SourceID", default=None)
    source_type: int | None = Field(validation_alias="SourceType", default=None)
    source_name: str | None = Field(validation_alias="SourceName", default=None)
    detector_type: int | None = Field(validation_alias="DetectorType", default=None)
    detector_name: str | None = Field(validation_alias="DecoderName", default=None)
    raw: str | None = Field(validation_alias="Raw", default=None)
    raw_v2: str | None = Field(validation_alias="RawV2", default=None)
    extra_data: dict | None = Field(validation_alias="ExtraData", default=None)
    structured_data: str | None = Field(validation_alias="StructuredData", default=None)

