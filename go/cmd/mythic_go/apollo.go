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

package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"github.com/mandiant/harbinger/go/pkg/base_worker"
)

type ApolloMythicArguments struct {
	File              string     `json:"file,omitempty"`
	Host              string     `json:"host,omitempty"`
	RemotePath        string     `json:"remote_path,omitempty"`
	Coff              string     `json:"coff_name,omitempty"`
	Function          string     `json:"function_name,omitempty"`
	Timeout           string     `json:"timeout,omitempty"`
	CoffArguments     [][]string `json:"coff_arguments,omitempty"`
	AssemblyName      string     `json:"assembly_name,omitempty"`
	AssemblyArguments string     `json:"assembly_arguments,omitempty"`
}

func BuildApolloTask(job base_worker.RunJob, file_ids []base_worker.InputFile) ([]base_worker.Task, error) {
	input_arguments := base_worker.HarbingerArguments{}
	tasks := []base_worker.Task{}
	err := json.Unmarshal([]byte(job.C2Job.Arguments), &input_arguments)
	if err != nil {
		return tasks, err
	}
	if len(file_ids) > 0 {
		input_arguments.File = file_ids[0].Id
	}
	arguments := ""
	command := job.C2Job.Command
	switch job.C2Job.Command {
	case "ps":
	case "ls":
		arguments = input_arguments.Path
	case "download":
		arguments = fmt.Sprintf("-Path %s", input_arguments.Path)
	case "sleep":
		arguments = fmt.Sprintf("%d %d", *input_arguments.Sleep, *input_arguments.Jitter)
	case "rm":
		arguments = input_arguments.Path
	case "upload":
		arguments_json := ApolloMythicArguments{
			File:       input_arguments.File,
			RemotePath: input_arguments.Remotename,
			Host:       input_arguments.Host,
		}
		arguments_bytes, err := json.Marshal(arguments_json)
		if err != nil {
			return tasks, err
		}
		arguments = string(arguments_bytes)
	case "runassembly":
		if len(file_ids) == 0 {
			return tasks, fmt.Errorf("no files provided to run task")
		}
		arguments_json := ApolloMythicArguments{
			File: input_arguments.File,
		}
		arguments_bytes, err := json.Marshal(arguments_json)
		if err != nil {
			return tasks, err
		}
		tasks = append(tasks, base_worker.Task{Command: "register_assembly", Arguments: string(arguments_bytes)})
		command = "execute_assembly"
		arguments_json = ApolloMythicArguments{
			AssemblyName:      file_ids[0].Name,
			AssemblyArguments: input_arguments.Arguments,
		}
		arguments_bytes, err = json.Marshal(arguments_json)
		if err != nil {
			return tasks, err
		}
		arguments = string(arguments_bytes)
	case "runbof":
		if len(file_ids) == 0 {
			return tasks, fmt.Errorf("no files provided to run task")
		}
		arguments_json := ApolloMythicArguments{
			File: input_arguments.File,
		}
		arguments_bytes, err := json.Marshal(arguments_json)
		if err != nil {
			return tasks, err
		}
		tasks = append(tasks, base_worker.Task{Command: "register_coff", Arguments: string(arguments_bytes)})
		command = "execute_coff"
		coff_arguments := make([][]string, 0)
		r := csv.NewReader(strings.NewReader(input_arguments.Arguments))
		r.Comma = ' '
		record, err := r.Read()
		if err == nil {
			for _, entry := range record {
				coff_arguments = append(coff_arguments, strings.SplitN(fmt.Sprintf("-%s", entry), ":", 2))
			}
		} else {
			log.Printf("error parsing arguments: %v", err)
		}

		arguments_json = ApolloMythicArguments{
			Coff:          file_ids[0].Name,
			Timeout:       "1200",
			Function:      "go",
			CoffArguments: coff_arguments,
		}
		arguments_bytes, err = json.Marshal(arguments_json)
		if err != nil {
			return tasks, err
		}
		arguments = string(arguments_bytes)
	case "cp":
		arguments = fmt.Sprintf("%s %s", input_arguments.Source, input_arguments.Destination)
	case "cd":
		arguments = input_arguments.Path
	case "mkdir":
		arguments = input_arguments.Path
	case "mv":
		arguments = fmt.Sprintf("%s %s", input_arguments.Source, input_arguments.Destination)
	case "pwd":
	case "runprocess":
		arguments = input_arguments.Command
	case "socks":
		arguments = fmt.Sprintf("%d", input_arguments.Port)
	case "exit":
	case "shell":
		arguments = input_arguments.Command
	case "disableetw":
	case "disableamsi":
	case "unhook":
	default:
	}

	tasks = append(tasks, base_worker.Task{Command: command, Arguments: arguments})

	return tasks, nil
}
