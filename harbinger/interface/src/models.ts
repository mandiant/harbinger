/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

export interface Chain {
  id: string;
  playbook_name: string;
  description: string;
  status: string;
  steps: number;
  complete: number;
  labels: Array<Label>;
  graph: string;
  correct: boolean;
}

export interface ChainStep {
  playbook_id: string;
  number: number;
  label: string;
  depends_on: string;
  proxy_job_id: string;
  c2_job_id: string;
  id: string;
  status: string;
  delay: string;
  execute_after: Date;
  modal: boolean;
  labels: Array<Label>;
  step_modifiers: Array<PlaybookStepModifier>;
}

export interface ProxyJob {
  credential_id: string;
  proxy_id: string;
  command: string;
  arguments: string;
  input_files: Array<string>;
  socks_server_id: string;
  id: string;
  status: string;
  exit_code: number;
  files: Array<File>;
  time_created: string;
  time_updated: string;
  time_started: string;
  time_completed: string;
  labels: Array<Label>;
  playbook_id: string;
  asciinema: boolean;
  tmate: boolean;
  proxychains: boolean;
  env: string;
  socks_server: SocksServer;
  processing_status: string;
  ai_summary: string;
}

export interface ProxyJobOutput {
  id: string;
  job_id: number;
  output: string;
  created_at: string;
  output_type: string;
}

export interface Proxy {
  id: string;
  type: string;
  host: string;
  port: number;
  status: string;
  username: string;
  password: string;
  labels: Array<Label>;
}

export interface Domain {
  id: string;
  long_name: string;
  short_name: string;
  labels: Array<Label>;
}

export interface Password {
  id: string;
  password: string;
  nt: string;
  aes128_key: string;
  aes256_key: string;
  labels: Array<Label>;
}

export interface Kerberos {
  id: string;
  client: string;
  server: string;
  key: string;
  auth: string;
  start: string;
  end: string;
  renew: string;
  ccache: string;
  kirbi: string;
}

export interface Credential {
  id: string;
  password: Password;
  kerberos: Kerberos;
  domain: Domain;
  username: string;
  labels: Array<Label>;
}

export interface File {
  filetype: string;
  magic_mimetype: string;
  magika_mimetype: string;
  exiftool: string;
  md5sum: string;
  sha1sum: string;
  sha256sum: string;
  id: string;
  job_id: string;
  filename: string;
  bucket: string;
  path: string;
  processing_status: string;
  processing_progress: string;
  processing_note: string;
  c2_task_id: string;
  labels: Array<Label>;
}


export interface C2Job {
  id: number;
  command: string;
  arguments: string;
  c2_server_id: string;
  c2_implant_id: string;
  playbook_id: string;
  input_files: Array<File>;
  status: string;
  c2_task_id: string;
  time_created: string;
  time_updated: string;
  time_started: string;
  time_completed: string;
  message: string;
  labels: Array<Label>;
}

export interface MythicTask {
  id: number;
  status: string;
  original_params: string;
  display_params: string;
  timestamp: string;
  command_name: string;
  operator: string;
  callback_id: number;
  labels: Array<Label>;
}

export interface GraphUser {
  name: string;
  objectid: string;
  domain: string;
  owned: boolean;
}

export interface GraphComputer {
  name: string;
  objectid: string;
  domain: string;
  owned: boolean;
}

export interface GraphGroup {
  name: string;
  objectid: string;
  domain: string;
}

export interface Component {
  id: number;
  name: string;
  hostname: string;
  status: string;
}

export interface Statistic {
  icon: string;
  key: string;
  value: number;
}

export interface Process {
  id: number;
  process_id: number;
  architecture: string;
  name: string;
  user: string;
  executablepath: string;
  parent_process_id: number;
  commandline: string;
  description: string;
  handle: string;
  host_id: string;
  mythic_implant: string;
  number: number;
  labels: Array<Label>;
}

export interface Node {
  id: number;
  labels: Array<string>;
  name: string;
  highvalue: string;
  domainsid: string;
  objectid: string;
  domain: string;
  element_id: number;
  whencreated: number;
  admincount: string;
  distinguishedname: string;
  owned: boolean;
}

export interface Edge {
  target: number;
  source: number;
  type: string;
}

export interface Query {
  name: string;
  icon: string;
  description: string;
}

export interface Host {
  domain_id: number;
  name: string;
  objectid: string;
  owned: boolean;
  domain: string;
  fqdn: string;
  id: number;
  labels: Array<Label>;
}

export interface MythicTaskOutput {
  id: number;
  timestamp: string;
  response_text: string;
  response_bytes: string;
  mythic_task_id: number;
  parsing_status: string;
  labels: Array<Label>;
}

export interface Suggestion {
  id: string;
  name: string;
  reason: string;
  playbook_template_id: string;
  arguments: object;
  time_created: string;
  time_updated: string;
  labels: Array<Label>;
}

export interface JobPreview {
  command: string;
  arguments: string;
  playbook_id: number;
}

export interface Pagination {
  sortBy: string;
  descending: boolean;
  page: number;
  rowsPerPage: number;
  rowsNumber: number;
}

export interface Props {
  pagination: Pagination;
}

export interface Progress {
  id: string;
  current: number;
  max: number;
  percentage: number;
  type: string;
  description: string;
}

export interface Event {
  event: string;
  id: string;
  step_status: string;
  chain_status: string;
  object_type: string;
  name: string;
  progress: Progress;
}

export interface PostgresEventPayload {
  table_name: string;
  operation: 'insert' | 'update' | 'delete';
  before: any; // Raw JSON of the old row (for 'update' and 'delete')
  after: any;  // Raw JSON of the new row (for 'insert' and 'update')
}

export interface CobaltStrikeBeacon {
  id: number;
  note: string;
  charset: string;
  internal: string;
  alive: boolean;
  session: string;
  listener: string;
  pid: number;
  lastf: string;
  computer: string;
  host: string;
  is64: boolean;
  process: string;
  ver: string;
  last: string;
  os: string;
  barch: string;
  phint: string;
  external: string;
  port: number;
  build: number;
  pbid: string;
  arch: string;
  user: string;
  state: string;
  sleep: number;
  jitter: number;
  host_id: string;
  labels: Array<Label>;
}

export interface BeaconOutput {
  id: number;
  beacon_id: number;
  command: string;
  timestamp: string;
  type: string;
  user: string;
  result: string;
  labels: Array<Label>;
}

export interface Label {
  id: string;
  name: string;
  category: string;
  color: string;
}

export interface LabelView {
  category: string;
  labels: Array<Label>;
}

export interface PlaybookTemplate {
  id: string;
  icon: string;
  name: string;
  yaml: string;
}

export interface C2Implant {
  id: string;
  c2_server_id: string;
  c2_id: string;
  c2_uid: string;
  c2_type: string;
  payload_type: string;
  name: string;
  hostname: string;
  description: string;
  sleep: number;
  jitter: number;
  os: string;
  pid: number;
  architecture: string;
  process: string;
  username: string;
  ip: string;
  external_ip: string;
  domain: string;
  last_checkin: string;
  last_checkin_formatted: string;
  host_id: string;
}

export interface C2Implant {
  id: string;
  c2_server_id: string;
  c2_id: string;
  c2_uid: string;
  c2_type: string;
  payload_type: string;
  name: string;
  hostname: string;
  description: string;
  sleep: number;
  jitter: number;
  os: string;
  pid: number;
  architecture: string;
  process: string;
  username: string;
  ip: string;
  external_ip: string;
  domain: string;
  last_checkin: string;
}

export interface C2Output {
  c2_id: number;
  c2_uid: string;
  c2_implant_id: string;
  c2_task_id: string;
  c2_server_id: string;
  response_text: string;
  output_type: string;
  timestamp: string;
  id: string;
  labels: Array<Label>;
}

export interface C2ServerStatus {
  status: string;
  message: string;
  name: string;
}

export interface C2Server {
  id: string;
  type: string;
  name: string;
  hostname: string;
  username: string;
  status: Array<C2ServerStatus>;
}

export interface C2Task {
  id: string;
  c2_id: number;
  c2_uid: string;
  c2_implant_id: string;
  status: string;
  original_params: string;
  display_params: string;
  time_started: string;
  time_completed: string;
  command_name: string;
  operator: string;
  port: string;
  processing_status: string;
  ai_summary: string;
  labels: Array<Label>;
}

export interface Timeline {
  id: string;
  status: string;
  command_name: string;
  arguments: string;
  original_params: string;
  argument_params: string;
  operator: string;
  time_started: string;
  time_completed: string;
  hostname: string;
  object_type: string;
  processing_status: string;
  ai_summary: string;
}

export interface SituationalAwareness {
  id: string;
  name: string;
  category: string;
  value_string: string;
  value_int: number;
  value_bool: boolean;
  value_json: string;
  domain_id: string;
  time_created: string;
  domain: Domain;
}

export interface ShareFile {
  type: string;
  file_id: string;
  parent_id: string;
  share_id: string;
  size: number;
  last_accessed: string;
  last_modified: string;
  created: string;
  unc_path: string;
  depth: number;
  name: string;
  downloaded: boolean;
  indexed: boolean;
  id: string;
  time_created: string;
  extension: string;
}

export interface Share {
  host_id: string;
  name: string;
  unc_path: string;
  type: number;
  remark: string;
  id: string;
  time_created: string;
}

export interface StatisticLink {
  to: string;
  label: string;
}

export interface StatisticViewModel {
  url: string;
  icon: string;
  name: string;
  to: Array<StatisticLink>;
}

export interface Hash {
  hash: string;
  type: string;
  hashcat_id: number;
  id: string;
  time_created: string;
  status: string;
  labels: Array<Label>;
}

export interface PlaybookStepModifier {
  regex: string;
  input_path: string;
  output_path: string;
  output_format: string;
  status: string;
  on_error: string;
  data: string;
  status_message: string;
  playbook_step_id: string;
  id: string;
  time_created: string;
}

export interface Highlight {
  file_id: string;
  c2_task_id: string;
  c2_task_output_id: string;
  proxy_job_output_id: string;
  parse_result_id: string;
  proxy_job_id: string;
  rule_id: number;
  rule_type: string;
  hit: string;
  start: string;
  end: string;
  line: number;
  id: string;
  time_created: string;
  labels: Array<string>;
}

export interface ParseResult {
  file_id: string;
  c2_task_id: string;
  c2_task_output_id: string;
  proxy_job_output_id: string;
  proxy_job_id: string;
  parser: string;
  log: string;
  id: string;
  time_created: string;
  labels: Array<string>;
}

export interface FilterOption {
  name: string;
  count: number;
  color: string;
}

export interface Filter {
  name: string;
  icon: string;
  type: string;
  multiple: boolean;
  query_name: string;
  options: Array<FilterOption>;
}

export interface HarbingerUser {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  password: string;
}

export interface Setting {
  name: string;
  type: string;
  category_id: string;
  value: unknown;
  id: string;
  description: string;
}

export interface Settings {
  name: string;
  description: string;
  icon: string;
  order: number;
  settings: Array<Setting>;
}

export interface SocksServer {
  id: string;
  type: string;
  hostname: string;
  operating_system: string;
  status: string;
  labels: Array<Setting>;
}

export interface Action {
  icon: string;
  name: string;
  description: string;
  status: string;
  id: string;
  time_created: string;
  time_updated: string;
  time_started: string;
  time_completed: string;
  labels: Array<Label>;
  playbook_templates: Array<PlaybookTemplate>;
}

export interface CertificateAuthority {
  id: string;
  ca_name: string;
  dns_name: string;
  certificate_subject: string;
  certificate_serial_number: string;
  certificate_validity_start: string;
  certificate_validity_end: string;
  web_enrollment: string;
  user_specified_san: string;
  request_disposition: string;
  enforce_encryption_for_requests: string;
  labels: Array<Label>;
}

export interface CertificateTemplate {
  id: string;
  template_name: string;
  display_name: string;
  enabled: boolean;
  client_authentication: boolean;
  enrollment_agent: boolean;
  any_purpose: boolean;
  enrollee_supplies_subject: boolean;
  requires_manager_approval: boolean;
  requires_manager_archival: boolean;
  authorized_signatures_required: number;
  validity_period: string;
  renewal_period: string;
  minimum_rsa_key_length: number;
  labels: Array<Label>;
}

export interface Issue {
  id: string;
  name: string;
  description: string;
  impact: string;
  exploitability: string;
  time_created: string;
  time_updated: string;
  label_id: string;
  labels: Array<Label>;
}

export interface C2ServerArguments {
  id: string;
  name: string;
  regex: string;
  error: string;
  type: string;
}

export interface C2ServerType {
  id: string;
  name: string;
  docker_image: string;
  command: string;
  icon: string;
  arguments: Array<C2ServerArguments>;
}

export type KeyValue = {
  [key: string]: number | string | boolean
}

export type KeyStringValue = {
  [key: string]: string
}

export interface Property {
  title: string, default?: string, filetype?: string, enum?: string[], type: string, description: string
}

export interface Schema {
  description: string,
  title: string;
  properties: { [key: string]: Property };
  required: string[];
}

export interface Checklist {
  id: string;
  domain_id: string;
  c2_implant_id: string;
  phase: string;
  name: string;
  status: string;
  time_created: string;
  time_updated: string;
  labels: Array<Label>;
}

export interface Objective {
  id: string;
  name: string;
  description: string;
  status: string;
  time_created: string;
  time_updated: string;
  labels: Array<Label>;
}
