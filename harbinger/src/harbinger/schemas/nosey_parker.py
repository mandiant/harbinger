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


from pydantic import BaseModel


class NPBlobMetadata(BaseModel):
    charset: str | None = ""
    id: str | None = ""
    mime_essence: str | None = ""
    num_bytes: int | None = 0


class NPOffset(BaseModel):
    column: int
    line: int


class NPSnippet(BaseModel):
    after: str | None = ""
    before: str | None = ""
    matching: str | None = ""


class NPSpan(BaseModel):
    start: NPOffset
    end: NPOffset


class NPLocation(BaseModel):
    source_span: NPSpan


class NPMatch(BaseModel):
    blob_id: str | None = ""
    blob_metadata: NPBlobMetadata
    comment: str | None = ""
    groups: list[str] | None = None
    location: NPLocation
    rule_name: str | None = ""
    rule_structural_id: str | None = ""
    rule_text_id: str | None = ""
    score: str | None = ""
    snippet: NPSnippet
    status: str | None = ""
    structural_id: str | None = ""


class NoseyParkerOutput(BaseModel):
    finding_id: str | None = ""
    groups: list[str] | None = None
    matches: list[NPMatch]
    mean_score: int | None = None
    num_matches: int | None = 0
    rule_name: str | None = ""
    rule_structural_id: str | None = ""
    rule_text_id: str | None = ""
    commend: str | None = ""
