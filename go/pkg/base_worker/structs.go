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

package base_worker

type File struct {
	Id       string `json:"id"`
	Filename string `json:"filename"`
	Bucket   string `json:"bucket"`
	Path     string `json:"path"`
}

type Task struct {
	Command   string
	Arguments string
}

type InputFile struct {
	Id   string
	Name string
}

type C2Job struct {
	Id         string `json:"id"`
	Command    string `json:"command"`
	Arguments  string `json:"arguments"`
	InputFiles []File `json:"input_files"`
}

type C2Implant struct {
	InternalId   string `json:"internal_id"`
	Architecture string `json:"architecture"`
	C2Type       string `json:"c2_type"`
	OS           string `json:"os"`
	PayloadType  string `json:"payload_type"`
}

type RunJob struct {
	C2Job     C2Job     `json:"c2_job"`
	C2Implant C2Implant `json:"c2_implant"`
}

type C2Task struct {
	InternalId        string `json:"internal_id"`
	InternalImplantId string `json:"internal_implant_id"`
	Id                string `json:"id"`
	Status            string `json:"status"`
	C2ServerId        string `json:"c2_server_id"`
}

type WorkflowStepResult struct {
	Id      string `json:"id"`
	Status  string `json:"status"`
	ProxyId string `json:"proxy_id"`
	Output  string `json:"output"`
	Label   string `json:"label"`
}

type Process struct {
	ProcessId       int32  `json:"process_id"`
	Architecture    string `json:"architecture"`
	Name            string `json:"name"`
	User            string `json:"user"`
	BinPath         string `json:"bin_path"`
	ParentProcessId int32  `json:"parent_process_id"`
}

type FileEntry struct {
	IsFile       bool     `json:"is_file"`
	Name         string   `json:"name"`
	Permissions  struct{} `json:"-"`
	AccessTime   int64    `json:"access_time"`
	CreationTime int64    `json:"creation_time"`
	ModifyTime   int64    `json:"modify_time"`
	Size         int64    `json:"size"`
}

type FileResponse struct {
	Host         string      `json:"host"`
	IsFile       bool        `json:"is_file"`
	Success      bool        `json:"success"`
	Permissions  struct{}    `json:"-"`
	AccessTime   int64       `json:"access_time"`
	CreationTime int64       `json:"creation_time"`
	ModifyTime   int64       `json:"modify_time"`
	Size         int64       `json:"size"`
	Name         string      `json:"name"`
	ParentPath   string      `json:"parent_path"`
	Files        []FileEntry `json:"files"`
}

type HarbingerArguments struct {
	Sleep       *int   `json:"sleep,omitempty"`
	Jitter      *int   `json:"jitter,omitempty"`
	File        string `json:"file,omitempty"`
	Remotename  string `json:"remotename,omitempty"`
	Path        string `json:"path,omitempty"`
	Host        string `json:"host,omitempty"`
	Arguments   string `json:"arguments_str,omitempty"`
	Safe        bool   `json:"safe,omitempty"`
	Source      string `json:"source,omitempty"`
	Dest        string `json:"dest,omitempty"`
	Port        int    `json:"port,omitempty"`
	Action      string `json:"action,omitempty"`
	Command     string `json:"command,omitempty"`
	Folder      string `json:"folder,omitempty"`
	Destination string `json:"destination,omitempty"`
	Filename    string `json:"filename,omitempty"`
	Cmdline     string `json:"cmdline,omitempty"`
	Hwbp        bool   `json:"hwbp,omitempty"`
}
