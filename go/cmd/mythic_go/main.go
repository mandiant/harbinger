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
	"bufio"
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"strconv"
	"strings"
	"sync"

	"github.com/mandiant/harbinger/go/pkg/base_worker"     // Import the base worker
	"github.com/mandiant/harbinger/go/pkg/mythic"          // Mythic client library
	messagesv1 "github.com/mandiant/harbinger/go/proto/v1" // Corrected import for protobufs
	"google.golang.org/grpc"
)

// MythicBridge implements the base_worker.C2Bridge interface for Mythic.
type MythicBridge struct {
	base_worker.DefaultC2Bridge
	mythicClient           mythic.Mythic
	hostname               string
	taskChannel            chan mythic.Task
	callbackChannel        chan mythic.Callback
	callbackCheckinChannel chan mythic.CallbackCheckin
	outputChannel          chan mythic.TaskOutput
	proxyChannel           chan mythic.Proxy
	fileDownloadChannel    chan mythic.FileDownload
	subscriptions          []string // To store subscription IDs for cleanup
	activeDownloadsWg      sync.WaitGroup
}

// NewMythicBridge creates a new instance of MythicBridge.
func NewMythicBridge() *MythicBridge {
	return &MythicBridge{
		taskChannel:            make(chan mythic.Task, 100),
		proxyChannel:           make(chan mythic.Proxy, 100),
		callbackChannel:        make(chan mythic.Callback, 100),
		outputChannel:          make(chan mythic.TaskOutput, 100),
		callbackCheckinChannel: make(chan mythic.CallbackCheckin, 100),
		fileDownloadChannel:    make(chan mythic.FileDownload, 100),
		subscriptions:          make([]string, 0),
	}
}

// Name returns the name of this C2 integration.
func (m *MythicBridge) Name() string {
	return "mythic"
}

// InitializeC2 sets up the Mythic client using settings from Harbinger.
// It now directly receives the HarbingerClient and c2ServerID.
func (m *MythicBridge) InitializeC2(ctx context.Context, settings *messagesv1.SettingsResponse) error {
	m.hostname = settings.Hostname

	mythicClient, err := mythic.Login(settings.Hostname, int(settings.Port), settings.Username, settings.Password)
	if err != nil {
		return fmt.Errorf("failed to login to Mythic: %w", err)
	}
	m.mythicClient = mythicClient
	return nil
}

// RunC2SpecificReaders starts all Mythic-specific goroutines for reading data.
func (m *MythicBridge) RunC2SpecificReaders(ctx context.Context, wg *sync.WaitGroup) {

	wg.Add(1)
	go func() {
		defer wg.Done()
		m.read_tasks(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		m.read_callbacks(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		m.read_task_output(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		m.read_callback_checkins(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		m.read_proxies(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		m.read_file_downloads(ctx)
	}()

	// Register all Mythic subscriptions
	subscriptionID, err := m.mythicClient.TaskSubscription(m.taskChannel)
	if err != nil {
		log.Fatalf("failed to subscribe to Mythic tasks: %v", err)
	}
	m.subscriptions = append(m.subscriptions, subscriptionID)

	subscriptionID, err = m.mythicClient.TaskOutputSubscription(m.outputChannel)
	if err != nil {
		log.Fatalf("failed to subscribe to Mythic task output: %v", err)
	}
	m.subscriptions = append(m.subscriptions, subscriptionID)

	subscriptionID, err = m.mythicClient.CallbackSubscription(m.callbackChannel)
	if err != nil {
		log.Fatalf("failed to subscribe to Mythic callbacks: %v", err)
	}
	m.subscriptions = append(m.subscriptions, subscriptionID)

	subscriptionID, err = m.mythicClient.CallbackCheckinSubscription(m.callbackCheckinChannel)
	if err != nil {
		log.Fatalf("failed to subscribe to Mythic callback checkins: %v", err)
	}
	m.subscriptions = append(m.subscriptions, subscriptionID)

	subscriptionID, err = m.mythicClient.ProxySubscription(m.proxyChannel)
	if err != nil {
		log.Fatalf("failed to subscribe to Mythic proxies: %v", err)
	}
	m.subscriptions = append(m.subscriptions, subscriptionID)

	subscriptionID, err = m.mythicClient.FileDownloadSubscription(m.fileDownloadChannel)
	if err != nil {
		log.Fatalf("failed to subscribe to Mythic file downloads: %v", err)
	}
	m.subscriptions = append(m.subscriptions, subscriptionID)

	// Mythic subscriptions run in a separate goroutine managed by the mythic client library
	m.mythicClient.SubscriptionClient.RunWithContext(ctx)
}

// SyncAll performs an initial synchronization of Mythic data.
// This is now an explicit method required by the C2Bridge (via WorkflowActivities).
func (m *MythicBridge) SyncAll(ctx context.Context) error {
	callbacks, err := m.mythicClient.GetAllCallbacks(ctx)
	if err != nil {
		return err
	}
	for i := range callbacks {
		m.callbackChannel <- callbacks[i]
	}

	tasks, err := m.mythicClient.GetAllTasks(ctx)
	if err != nil {
		return err
	}
	for i := range tasks {
		m.taskChannel <- tasks[i]
		output, err := m.mythicClient.GetOutputForTask(ctx, tasks[i].Id)
		if err != nil {
			continue
		}
		for j := range output {
			m.outputChannel <- output[j]
		}
	}

	proxies, err := m.mythicClient.GetAllProxies(ctx)
	if err != nil {
		return err
	}
	for i := range proxies {
		m.proxyChannel <- proxies[i]
	}

	downloads, err := m.mythicClient.GetAllFileDownloads(ctx)
	if err != nil {
		return err
	}
	for i := range downloads {
		m.fileDownloadChannel <- downloads[i]
	}
	return nil
}

// RunJob is a Temporal activity that executes a job on Mythic.
// This is now an explicit method required by the C2Bridge (via WorkflowActivities).
func (m *MythicBridge) RunJob(ctx context.Context, job base_worker.RunJob) (base_worker.C2Task, error) {
	file_ids := make([]base_worker.InputFile, 0)
	log.Printf("Running job: %s\n", job.C2Job.Id)

	for _, file := range job.C2Job.InputFiles {
		stream, err := m.HarbingerClient.DownloadFile(ctx, &messagesv1.DownloadFileRequest{FileId: file.Id})
		if err != nil {
			log.Println(err)
			continue
		}

		buf := new(bytes.Buffer)

		for {
			data, err := stream.Recv()
			if err == io.EOF {
				break
			}
			buf.Write(data.Data)
		}
		result, err := m.mythicClient.RegisterFile(file.Filename, buf.Bytes())
		if err != nil {
			log.Println(err)
		}
		if result.Status == "success" {
			file_ids = append(file_ids, base_worker.InputFile{Id: result.AgentFileId, Name: file.Filename})
		} else {
			log.Println(result.Error)
		}
	}

	implant_id, err := strconv.Atoi(job.C2Implant.InternalId)
	if err != nil {
		return base_worker.C2Task{}, err
	}

	display_id, err := m.mythicClient.GetCallbackDisplayIdForId(ctx, implant_id)
	if err != nil {
		return base_worker.C2Task{}, err
	}

	tasks, err := m.BuildMythicTask(job, file_ids) // Call Mythic-specific task builder
	if err != nil {
		return base_worker.C2Task{}, err
	}

	status := ""
	internal_id := ""

	for i, task := range tasks {
		log.Printf("Running task %d '%s' with arguments '%s'\n", i, task.Command, task.Arguments)
		result_task, err := m.mythicClient.IssueTask(ctx, display_id, task.Command, task.Arguments)
		if err != nil {
			return base_worker.C2Task{}, err
		}
		status = result_task.Status
		internal_id = fmt.Sprintf("%d", result_task.Id)
		if i != len(tasks)-1 {
			log.Printf("Wait for intermediate task to complete: %s", internal_id)
			// Calling the WaitForTask activity directly here for intermediate tasks.
			// In a real Temporal workflow, this might be a child workflow or another activity call.
			_, err := m.WaitForTask(ctx, base_worker.C2Task{InternalId: internal_id})
			if err != nil {
				log.Printf("Warning: Failed to wait for intermediate task %s: %v", internal_id, err)
			}
		}
	}

	log.Printf("Job %s completed with status %s\n", job.C2Job.Id, status)
	return base_worker.C2Task{
		InternalId:        internal_id,
		InternalImplantId: job.C2Implant.InternalId,
		C2ServerId:        m.C2ServerID,
		Status:            status,
	}, nil
}

// WaitForTask is a Temporal activity that waits for a Mythic task to complete.
// This is now an explicit method required by the C2Bridge (via WorkflowActivities).
func (m *MythicBridge) WaitForTask(ctx context.Context, task base_worker.C2Task) (base_worker.WorkflowStepResult, error) {
	channel := make(chan mythic.Task)
	log.Printf("Waiting for task: %s", task.InternalId) // Use InternalId from the base_worker.C2Task

	taskID, err := strconv.Atoi(task.InternalId)
	if err != nil {
		return base_worker.WorkflowStepResult{}, err
	}

	subscriptionID, err := m.mythicClient.SpecificTaskSubscription(channel, taskID)
	if err != nil {
		return base_worker.WorkflowStepResult{}, err
	}

	defer m.mythicClient.SubscriptionClient.Unsubscribe(subscriptionID)
	result := mythic.Task{}

loop:
	for {
		select {
		case msg := <-channel:
			if msg.Completed {
				result = msg
				break loop
			}
		case <-ctx.Done():
			return base_worker.WorkflowStepResult{}, fmt.Errorf("interrupted")
		}
	}
	status := result.Status
	if status == "success" {
		status = "completed"
	}
	log.Printf("Task: %s completed with status: %s\n", task.InternalId, status)
	return base_worker.WorkflowStepResult{Id: task.Id, Status: status}, nil
}

// SendC2Status updates the C2 server's status in Harbinger.
func (m *MythicBridge) SendC2Status(ctx context.Context, status string) error {
	_, err := m.HarbingerClient.SetC2ServerStatus(ctx, &messagesv1.C2ServerStatusRequest{
		C2ServerId: m.C2ServerID,
		Status:     status,
		Name:       m.Name(),
	})
	return err
}

// RefreshC2Session attempts to refresh the Mythic session.
func (m *MythicBridge) RefreshC2Session() error {
	return m.mythicClient.RefreshSession()
}

// Stop performs Mythic-specific stop actions (e.g., unsubscribing).
func (m *MythicBridge) Stop() error {
	for _, subID := range m.subscriptions {
		err := m.mythicClient.SubscriptionClient.Unsubscribe(subID)
		if err != nil {
			log.Printf("ERROR: Failed to unsubscribe from Mythic subscription %s: %v\n", subID, err)
		}
	}
	m.mythicClient.SubscriptionClient.Close()
	log.Println("Mythic subscriptions closed.")
	return nil
}

func (m *MythicBridge) read_tasks(ctx context.Context) {
	for {
		select {
		case msg := <-m.taskChannel:
			m.HarbingerClient.SaveTask(ctx, &messagesv1.TaskRequest{
				InternalId:        fmt.Sprintf("%d", msg.Id),
				C2ServerId:        m.C2ServerID,
				Status:            msg.Status,
				OriginalParams:    msg.Original_Params,
				DisplayParams:     msg.Display_Params,
				TimeStarted:       msg.Status_Timestamp_Processing,
				TimeCompleted:     msg.Timestamp,
				CommandName:       msg.Command_Name,
				Operator:          msg.Operator.Username,
				InternalImplantId: fmt.Sprintf("%d", msg.Callback.Id),
			})
		case <-ctx.Done():
			return
		}
	}
}

func (m *MythicBridge) read_task_output(ctx context.Context) {
	for {
		select {
		case msg := <-m.outputChannel:
			message := msg.Response_Text
			for range 2 {
				decoded, err := base64.StdEncoding.DecodeString(message)
				if err == nil {
					message = string(decoded)
				} else {
					break
				}
			}
			processes := make([]*messagesv1.Process, 0)
			if msg.Task.Command_Name == "ps" {
				processesJSON := make([]base_worker.Process, 0)
				err := json.Unmarshal([]byte(message), &processesJSON)
				if err != nil {
					log.Printf("error processing processes: %v\n", err)
				} else {
					for _, process := range processesJSON {
						processes = append(processes, &messagesv1.Process{
							ProcessId:       process.ProcessId,
							Architecture:    process.Architecture,
							Name:            process.Name,
							User:            process.User,
							ParentProcessId: process.ParentProcessId,
							BinPath:         process.BinPath,
						})
					}
				}
			}
			resp := &messagesv1.TaskOutputRequest{
				InternalId:     fmt.Sprintf("%d", msg.Id),
				C2ServerId:     m.C2ServerID,
				ResponseText:   message,
				Timestamp:      msg.Timestamp,
				InternalTaskId: fmt.Sprintf("%d", msg.Task.Id),
				Processes:      processes,
			}

			if msg.Task.Command_Name == "ls" && strings.HasPrefix(message, "{") {
				fileResp := base_worker.FileResponse{}
				err := json.Unmarshal([]byte(message), &fileResp)
				if err != nil {
					log.Printf("error file list: %v\n", err)
				} else {
					fileList := messagesv1.FileList{
						Host:         fileResp.Host,
						Name:         fileResp.Name,
						ParentPath:   fileResp.ParentPath,
						Size:         fileResp.Size,
						LastAccessed: fmt.Sprintf("%d", fileResp.AccessTime),
						LastModified: fmt.Sprintf("%d", fileResp.ModifyTime),
						Created:      fmt.Sprintf("%d", fileResp.CreationTime),
					}
					for _, file := range fileResp.Files {
						filetype := "dir"
						if file.IsFile {
							filetype = "file"
						}
						fileList.Files = append(fileList.Files, &messagesv1.ShareFile{
							Type:         filetype,
							Size:         file.Size,
							LastAccessed: fmt.Sprintf("%d", fileResp.AccessTime),
							LastModified: fmt.Sprintf("%d", fileResp.ModifyTime),
							Created:      fmt.Sprintf("%d", fileResp.CreationTime),
							Name:         file.Name,
						})
					}
					resp.FileList = &fileList
				}
			}
			m.HarbingerClient.SaveTaskOutput(ctx, resp)

		case <-ctx.Done():
			return
		}
	}
}

func (m *MythicBridge) read_callbacks(ctx context.Context) {
	for {
		select {
		case msg := <-m.callbackChannel:
			m.HarbingerClient.SaveImplant(ctx, &messagesv1.ImplantRequest{
				C2ServerId:   m.C2ServerID,
				InternalId:   fmt.Sprintf("%d", msg.Id),
				C2Type:       "mythic",
				PayloadType:  msg.Payload.Payloadtype.Name,
				Hostname:     msg.Host,
				Description:  msg.Description,
				Os:           msg.Os,
				Pid:          int32(msg.Pid),
				Architecture: msg.Architecture,
				Process:      msg.Process_Name,
				Username:     msg.User,
				Ip:           msg.Ip,
				ExternalIp:   msg.External_Ip,
				Domain:       msg.Domain,
				LastCheckin:  msg.Last_Checkin,
			})
		case <-ctx.Done():
			return
		}
	}
}

func (m *MythicBridge) read_callback_checkins(ctx context.Context) {
	for {
		select {
		case msg := <-m.callbackCheckinChannel:
			m.HarbingerClient.SaveImplant(ctx, &messagesv1.ImplantRequest{
				C2ServerId:  m.C2ServerID,
				InternalId:  fmt.Sprintf("%d", msg.Id),
				LastCheckin: msg.Last_Checkin,
			})
		case <-ctx.Done():
			return
		}
	}
}

func (m *MythicBridge) read_proxies(ctx context.Context) {
	for {
		select {
		case msg := <-m.proxyChannel:
			status := "connected"
			if msg.Deleted {
				status = "disconnected"
			}
			m.HarbingerClient.SaveProxy(ctx, &messagesv1.ProxyRequest{
				Host:           m.hostname,
				Port:           int32(msg.Local_Port),
				Type:           "socks5",
				Status:         status,
				RemoteHostname: msg.Callback.Host,
				C2ServerId:     m.C2ServerID,
				InternalId:     fmt.Sprintf("%d", msg.Id),
			})
		case <-ctx.Done():
			return
		}
	}
}

func StreamFile(filename string, stream grpc.ClientStreamingClient[messagesv1.UploadFileRequest, messagesv1.UploadFileResponse]) (*messagesv1.UploadFileResponse, error) {
	f, err := os.Open(filename)
	if err != nil {
		return &messagesv1.UploadFileResponse{}, fmt.Errorf("error to read [file=%v]: %v", filename, err.Error())
	}

	nBytes, nChunks := int64(0), int64(0)
	r := bufio.NewReader(f)
	buf := make([]byte, 0, 1024*1024)
	for {
		n, err := r.Read(buf[:cap(buf)])
		buf = buf[:n]
		if n == 0 {
			if err == nil {
				continue
			}
			if err == io.EOF {
				break
			}
			return &messagesv1.UploadFileResponse{}, err
		}
		nChunks++
		nBytes += int64(len(buf))
		// process buf
		if err != nil && err != io.EOF {
			return &messagesv1.UploadFileResponse{}, err
		}
		stream.Send(&messagesv1.UploadFileRequest{Data: buf})
	}
	return stream.CloseAndRecv()
}

func (m *MythicBridge) download_file(ctx context.Context, msg mythic.FileDownload) error {
	log.Printf("Processing file %s\n", msg.Filename_Utf8)
	defer m.activeDownloadsWg.Done()

	file, err := os.CreateTemp("/tmp", "harbinger")
	if err != nil {
		log.Println(err)
		return err
	}
	defer os.Remove(file.Name())

	downloaded := false
	attempts := 3

	for i := range attempts {
		log.Printf("Attempt %d to download %s\n", i, msg.Filename_Utf8)
		err = m.mythicClient.DownloadFile(file.Name(), msg.Agent_File_Id)
		if err != nil {
			log.Println(err)
		} else {
			downloaded = true
			break
		}
	}

	if !downloaded {
		log.Printf("Unable to download %s after %d attempts\n", msg.Filename_Utf8, attempts)
		return err
	}

	stream, err := m.HarbingerClient.UploadFile(ctx)
	if err != nil {
		log.Printf("Unable to upload file: %v\n", err)
		return err
	}

	response, err := StreamFile(file.Name(), stream)
	if err != nil {
		log.Printf("Unable to stream file: %v\n", err)
		return err
	}
	_, err = m.HarbingerClient.SaveFile(ctx, &messagesv1.FileRequest{
		Filename:          msg.Filename_Utf8,
		InternalTaskId:    fmt.Sprintf("%d", msg.Task_Id),
		InternalImplantId: fmt.Sprintf("%d", msg.Task.Callback.Id),
		C2ServerId:        m.C2ServerID,
		UploadFileId:      response.UploadFileId,
	})
	if err != nil {
		log.Println(err)
		return err
	}
	log.Printf("Completed file %s\n", msg.Filename_Utf8)
	return nil
}

func (m *MythicBridge) read_file_downloads(ctx context.Context) {
	for {
		select {
		case msg := <-m.fileDownloadChannel:
			resp, err := m.HarbingerClient.CheckFileExists(ctx, &messagesv1.FileExistsRequest{Sha1: msg.Sha1})
			if err != nil {
				log.Println(err)
				continue
			}
			if resp.Exists {
				log.Printf("File with hash: %s already exists\n", msg.Sha1)
			} else {
				m.activeDownloadsWg.Add(1)
				go m.download_file(ctx, msg)
			}

		case <-ctx.Done():
			m.activeDownloadsWg.Wait()
			return
		}
	}
}

// BuildMythicTask is a Mythic-specific implementation of building tasks.
func (m *MythicBridge) BuildMythicTask(job base_worker.RunJob, files []base_worker.InputFile) ([]base_worker.Task, error) {
	switch payload := job.C2Implant.PayloadType; payload {
	case "apollo":
		return BuildApolloTask(job, files) // Assumes BuildApolloTask is defined elsewhere in this package or imported
	default:
		return []base_worker.Task{}, fmt.Errorf("could not find the mapping for payload: %s", payload)
	}
}

func main() {
	// Create the specific C2 bridge implementation
	mythicBridge := NewMythicBridge()

	// Initialize the generic base worker with the Mythic bridge
	worker, err := base_worker.NewWorker(mythicBridge)
	if err != nil {
		log.Fatalf("Failed to initialize base worker: %v", err)
	}

	// The base worker takes care of running everything
	worker.Run()
}
