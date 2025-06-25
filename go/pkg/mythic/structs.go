// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package mythic

type LoginMessage struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type RefreshMessage struct {
	RefreshToken string `json:"refresh_token"`
	AccessToken  string `json:"access_token"`
}

type User struct {
	CurrentOperation   string `json:"current_operation"`
	CurrentOperationId int    `json:"current_operation_id"`
	Id                 int    `json:"id"`
	UserId             int    `json:"user_id"`
	Username           string `json:"username"`
}

type AuthResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	User         User   `json:"user"`
}

type MythicResponse struct {
	AuthResponse AuthResponse
}

type PayloadType struct {
	Name string
}

type Payload struct {
	Os          string
	Payloadtype PayloadType
	Description string
	Uuid        string
}

type Callback struct {
	Id                int
	Architecture      string
	Description       string
	Domain            string
	External_Ip       string
	Host              string
	Display_Id        int
	Integrity_Level   int
	Ip                string
	Extra_Info        string
	Sleep_Info        string
	Pid               int
	Os                string
	User              string
	Agent_Callback_Id string
	Operation_Id      int
	Process_Name      string
	Payload           Payload
	Last_Checkin      string
}

type CallbackCheckin struct {
	Id           int
	Last_Checkin string
}

type CallbackHost struct {
	Host string
}

type AllCallbacks struct {
	Callback []Callback
}

type AllActiveCallbacks struct {
	Callback []Callback `graphql:"callback(where: {active: {_eq: true}})"`
}

type Operator struct {
	Username string
}

type CallbackIds struct {
	Id         int
	Display_Id int
}

type Token struct {
	Token_Id int
}

type Task struct {
	Callback                    CallbackIds
	Id                          int
	Display_Id                  int
	Operator                    Operator
	Status                      string
	Completed                   bool
	Original_Params             string
	Display_Params              string
	Timestamp                   string
	Status_Timestamp_Processing string
	Command_Name                string
	Token                       Token
}

type CurrentTasks struct {
	Task []Task `graphql:"task(order_by: {id: desc})"`
}

type TaskForCallback struct {
	Task []Task `graphql:"task(where: {callback: {display_id: {_eq: $callback_display_id}}}, order_by: {id: asc})"`
}

type TaskOutput struct {
	Id            int
	Timestamp     string
	Response_Text string
	Task          Task
}

type TaskOutputForTask struct {
	TaskOutput []TaskOutput `graphql:"response(order_by: {id: asc}, where: {task:{display_id: {_eq: $task_display_id}}})"`
}

type TaskSubscription struct {
	Task []Task `graphql:"task_stream(batch_size: $batch_size, cursor: {initial_value: {timestamp: $now}})"`
}

type Timestamp string

func (ti Timestamp) GetGraphQLType() string {
	return "timestamp"
}

type TaskStream struct {
	Stream []Task `graphql:"task_stream"`
}

type Proxy struct {
	Id         int
	Deleted    bool
	Local_Port int
	Port_Type  string
	Callback   CallbackHost
}

type FileTask struct {
	Callback CallbackIds
}

type FileDownload struct {
	Filename_Utf8 string
	Md5           string
	Sha1          string
	Task_Id       int
	Id            int
	Agent_File_Id string
	Task          FileTask
}

type CallbackSubscription struct {
	Callback []Callback `graphql:"callback_stream(where: {active: {_eq: true}}, cursor: {initial_value: { init_callback: $now}}, batch_size: $batch_size)"`
}

type CallbackStream struct {
	Stream []Callback `graphql:"callback_stream"`
}

type TaskOutputSubscription struct {
	TaskOutput []TaskOutput `graphql:"response_stream(cursor: {initial_value: {timestamp: $now}}, batch_size: $batch_size)"`
}

type TaskOutputStream struct {
	Stream []TaskOutput `graphql:"response_stream"`
}

type CallbackCheckinSubscription struct {
	Callback []CallbackCheckin `graphql:"callback(order_by: {last_checkin: desc}, limit: 1)"`
}

type CallbackCheckinStream struct {
	Stream []CallbackCheckin `graphql:"callback"`
}

type ProxySubscription struct {
	Proxy []Proxy `graphql:"callbackport(where: {port_type: {_eq: \"socks\"}})"`
}

type ProxyStream struct {
	Proxy []Proxy `graphql:"callbackport"`
}

type ProxyQuery struct {
	Proxy []Proxy `graphql:"callbackport(where: {port_type: {_eq: \"socks\"}})"`
}

type FileDownloadsQuery struct {
	Downloads []FileDownload `graphql:"filemeta(where: {is_download_from_agent: {_eq: true}, complete: {_eq: true}})"`
}

type FileDownloadSubscription struct {
	Downloads []FileDownload `graphql:"filemeta_stream(where: {is_download_from_agent: {_eq: true}, complete: {_eq: true}}, cursor: {initial_value: { timestamp: $now}}, batch_size: $batch_size)"`
}

type FileDownloadStream struct {
	Downloads []FileDownload `graphql:"filemeta_stream"`
}

type FileUploadResult struct {
	AgentFileId string `json:"agent_file_id"`
	Status      string `json:"status"`
	Error       string `json:"error"`
}

type CallbackDisplayId struct {
	Display_Id int
}

type CallbackByPk struct {
	CallbackDisplayId `graphql:"callback_by_pk(id: $id)"`
}

type CreatedTask struct {
	Status     string
	Id         int
	Display_Id int
	Error      string
}

type CreateTask struct {
	Task CreatedTask `graphql:"createTask(callback_id: $callback_id, command: $command, params: $params)"`
}

type SpecificTaskSubscription struct {
	Task []Task `graphql:"task_stream(cursor: {initial_value: {timestamp: \"1970-01-01\"}}, batch_size: 1, where: {id: {_eq: $task_id}})"`
}
