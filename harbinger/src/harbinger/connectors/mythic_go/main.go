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
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/mndt-proactive/Harbinger/mythic_go/mythic"
	messagesv1 "github.com/mndt-proactive/Harbinger/mythic_go/proto/v1"
	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/client"
	temporalworker "go.temporal.io/sdk/worker"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func (w *Worker) read_tasks(ctx context.Context) {
	for {
		select {
		case msg := <-w.TaskChannel:
			w.Client.SaveTask(ctx, &messagesv1.TaskRequest{
				InternalId:        fmt.Sprintf("%d", msg.Id),
				C2ServerId:        w.C2ServerId,
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

func (w *Worker) read_task_output(ctx context.Context) {
	for {
		select {
		case msg := <-w.OutputChannel:
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
				processes_json := make([]Process, 0)
				err := json.Unmarshal([]byte(message), &processes_json)
				if err != nil {
					log.Printf("error processing processes: %v\n", err)
				} else {
					for _, process := range processes_json {
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
				C2ServerId:     w.C2ServerId,
				ResponseText:   message,
				Timestamp:      msg.Timestamp,
				InternalTaskId: fmt.Sprintf("%d", msg.Task.Id),
				Processes:      processes,
			}

			if msg.Task.Command_Name == "ls" && strings.HasPrefix(message, "{") {
				file_resp := FileResponse{}
				err := json.Unmarshal([]byte(message), &file_resp)
				if err != nil {
					log.Printf("error file list: %v\n", err)
				} else {
					file_list := messagesv1.FileList{
						Host:         file_resp.Host,
						Name:         file_resp.Name,
						ParentPath:   file_resp.ParentPath,
						Size:         file_resp.Size,
						LastAccessed: fmt.Sprintf("%d", file_resp.AccessTime),
						LastModified: fmt.Sprintf("%d", file_resp.ModifyTime),
						Created:      fmt.Sprintf("%d", file_resp.CreationTime),
					}
					for _, file := range file_resp.Files {
						filetype := "dir"
						if file.IsFile {
							filetype = "file"
						}
						file_list.Files = append(file_list.Files, &messagesv1.ShareFile{
							Type:         filetype,
							Size:         file.Size,
							LastAccessed: fmt.Sprintf("%d", file_resp.AccessTime),
							LastModified: fmt.Sprintf("%d", file_resp.ModifyTime),
							Created:      fmt.Sprintf("%d", file_resp.CreationTime),
							Name:         file.Name,
						})
					}
					resp.FileList = &file_list
				}
			}
			w.Client.SaveTaskOutput(ctx, resp)

		case <-ctx.Done():
			return
		}
	}
}

func (w *Worker) read_callbacks(ctx context.Context) {
	for {
		select {
		case msg := <-w.CallbackChannel:
			w.Client.SaveImplant(ctx, &messagesv1.ImplantRequest{
				C2ServerId:   w.C2ServerId,
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

func (w *Worker) read_callback_checkins(ctx context.Context) {
	for {
		select {
		case msg := <-w.CallbackCheckinChannel:
			w.Client.SaveImplant(ctx, &messagesv1.ImplantRequest{
				C2ServerId:  w.C2ServerId,
				InternalId:  fmt.Sprintf("%d", msg.Id),
				LastCheckin: msg.Last_Checkin,
			})
		case <-ctx.Done():
			return
		}
	}
}

func (w *Worker) read_proxies(ctx context.Context) {
	for {
		select {
		case msg := <-w.ProxyChannel:
			status := "connected"
			if msg.Deleted {
				status = "disconnected"
			}
			w.Client.SaveProxy(ctx, &messagesv1.ProxyRequest{
				Host:           w.Hostname,
				Port:           int32(msg.Local_Port),
				Type:           "socks5",
				Status:         status,
				RemoteHostname: msg.Callback.Host,
				C2ServerId:     w.C2ServerId,
				InternalId:     fmt.Sprintf("%d", msg.Id),
			})
		case <-ctx.Done():
			return
		}
	}
}

func (w *Worker) send_status(ctx context.Context, status string) {
	w.Client.SetC2ServerStatus(ctx, &messagesv1.C2ServerStatusRequest{
		C2ServerId: w.C2ServerId,
		Status:     status,
		Name:       "mythic",
	})
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

func (w *Worker) download_file(ctx context.Context, msg mythic.FileDownload) error {
	log.Printf("Processing file %s\n", msg.Filename_Utf8)

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
		err = w.MythicClient.DownloadFile(file.Name(), msg.Agent_File_Id)
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

	stream, err := w.Client.UploadFile(ctx)
	if err != nil {
		log.Println(err)
		return err
	}

	response, err := StreamFile(file.Name(), stream)
	if err != nil {
		log.Println(err)
		return err
	}
	w.Client.SaveFile(ctx, &messagesv1.FileRequest{
		Filename:          msg.Filename_Utf8,
		InternalTaskId:    fmt.Sprintf("%d", msg.Task_Id),
		InternalImplantId: fmt.Sprintf("%d", msg.Task.Callback.Id),
		C2ServerId:        w.C2ServerId,
		UploadFileId:      response.UploadFileId,
	})
	log.Printf("Completed file %s\n", msg.Filename_Utf8)
	return nil
}

func (w *Worker) read_file_downloads(ctx context.Context) {
	for {
		select {
		case msg := <-w.FileDownloadChannel:
			resp, err := w.Client.CheckFileExists(ctx, &messagesv1.FileExistsRequest{Sha1: msg.Sha1})
			if err != nil {
				log.Println(err)
				continue
			}
			if resp.Exists {
				log.Printf("File with hash: %s already exists\n", msg.Sha1)
			} else {
				go w.download_file(ctx, msg)
			}

		case <-ctx.Done():
			return
		}
	}
}

func (w *Worker) SyncAll(ctx context.Context) error {
	callbacks, err := w.MythicClient.GetAllCallbacks(ctx)
	if err != nil {
		return err
	}
	for i := range callbacks {
		w.CallbackChannel <- callbacks[i]
	}

	tasks, err := w.MythicClient.GetAllTasks(ctx)
	if err != nil {
		return err
	}
	for i := range tasks {
		w.TaskChannel <- tasks[i]
		output, err := w.MythicClient.GetOutputForTask(ctx, tasks[i].Id)
		if err != nil {
			continue
		}
		for j := range output {
			w.OutputChannel <- output[j]
		}
	}

	proxies, err := w.MythicClient.GetAllProxies(ctx)
	if err != nil {
		return err
	}
	for i := range proxies {
		w.ProxyChannel <- proxies[i]
	}

	downloads, err := w.MythicClient.GetAllFileDownloads(ctx)
	if err != nil {
		return err
	}
	for i := range downloads {
		w.FileDownloadChannel <- downloads[i]
	}
	return nil
}

func (w *Worker) RunJob(ctx context.Context, job RunJob) (C2Task, error) {
	file_ids := make([]InputFile, 0)
	log.Printf("Running job: %s\n", job.C2Job.Id)

	for _, file := range job.C2Job.InputFiles {
		stream, err := w.Client.DownloadFile(ctx, &messagesv1.DownloadFileRequest{FileId: file.Id})
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
		result, err := w.MythicClient.RegisterFile(file.Filename, buf.Bytes())
		if err != nil {
			log.Println(err)
		}
		if result.Status == "success" {
			file_ids = append(file_ids, InputFile{Id: result.AgentFileId, Name: file.Filename})
		} else {
			log.Println(result.Error)
		}
	}

	implant_id, err := strconv.Atoi(job.C2Implant.InternalId)
	if err != nil {
		return C2Task{}, err
	}

	display_id, err := w.MythicClient.GetCallbackDisplayIdForId(ctx, implant_id)
	if err != nil {
		return C2Task{}, err
	}

	tasks, err := BuildTask(job, file_ids)
	if err != nil {
		return C2Task{}, err
	}

	status := ""
	internal_id := ""

	for i, task := range tasks {
		log.Printf("Running task %d '%s' with arguments '%s'\n", i, task.Command, task.Arguments)
		result_task, err := w.MythicClient.IssueTask(ctx, display_id, task.Command, task.Arguments)
		if err != nil {
			return C2Task{}, err
		}
		status = result_task.Status
		internal_id = fmt.Sprintf("%d", result_task.Id)
		if i != len(tasks)-1 {
			log.Printf("Wait for task to complete: %s", internal_id)
			w.WaitForTask(ctx, C2Task{InternalId: internal_id})
		}
	}

	log.Printf("Job %s completed with status %s\n", job.C2Job.Id, status)
	return C2Task{
		InternalId:        internal_id,
		InternalImplantId: job.C2Implant.InternalId,
		C2ServerId:        w.C2ServerId,
		Status:            status,
	}, nil
}

func (w *Worker) refresh_session(ctx context.Context, ticker time.Ticker) error {
	for {
		select {
		case <-ctx.Done():
			return nil
		case <-ticker.C:
			err := w.MythicClient.RefreshSession()
			if err != nil {
				log.Printf("error refreshing session: %v\n", err)
			}
		}
	}
}

type Task struct {
	Command   string
	Arguments string
}

type InputFile struct {
	Id   string
	Name string
}

func BuildTask(job RunJob, files []InputFile) ([]Task, error) {
	switch payload := job.C2Implant.PayloadType; payload {
	case "apollo":
		return BuildApolloTask(job, files)
	default:
		return []Task{}, fmt.Errorf("could not find the mapping for payload: %s", payload)
	}
}

func (w *Worker) WaitForTask(ctx context.Context, task C2Task) (WorkflowStepResult, error) {
	channel := make(chan mythic.Task)
	log.Printf("Waiting for task: %s", task.Id)

	task_id, err := strconv.Atoi(task.InternalId)
	if err != nil {
		return WorkflowStepResult{}, err
	}

	subscription_id, err := w.MythicClient.SpecificTaskSubscription(channel, task_id)

	if err != nil {
		return WorkflowStepResult{}, err
	}

	defer w.MythicClient.SubscriptionClient.Unsubscribe(subscription_id)
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
			break loop
		}
	}
	status := result.Status
	if status == "success" {
		status = "completed"
	}
	log.Printf("Task: %s completed with status: %s\n", task.Id, status)
	return WorkflowStepResult{Id: task.Id, Status: status}, nil
}

type Worker struct {
	Client                 messagesv1.HarbingerClient
	C2ServerId             string
	TaskChannel            chan mythic.Task
	CallbackChannel        chan mythic.Callback
	CallbackCheckinChannel chan mythic.CallbackCheckin
	OutputChannel          chan mythic.TaskOutput
	ProxyChannel           chan mythic.Proxy
	FileDownloadChannel    chan mythic.FileDownload
	MythicClient           mythic.Mythic
	Hostname               string
	Settings               *messagesv1.SettingsResponse
}

func main() {
	c2_server_id := os.Getenv("C2_SERVER_ID")
	if c2_server_id == "" {
		log.Fatalln("C2_SERVER_ID was not set.")
	}
	harbinger_grpc_host := os.Getenv("HARBINGER_GRPC_HOST")
	if harbinger_grpc_host == "" {
		log.Fatalln("HARBINGER_GRPC_HOST was not set.")
	}

	temporal_host := os.Getenv("TEMPORAL_HOST")
	if temporal_host == "" {
		log.Fatalln("Please set TEMPORAL_HOST env variable")
	}

	conn, err := grpc.NewClient(harbinger_grpc_host, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close()

	c := messagesv1.NewHarbingerClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()

	req := messagesv1.SettingsRequest{C2ServerId: c2_server_id}

	settings, err := c.GetSettings(ctx, &req)
	if err != nil {
		log.Fatalf("could get settings: %v", err)
	}
	log.Printf("Connected to server")

	m, err := mythic.Login(settings.Hostname, int(settings.Port), settings.Username, settings.Password)
	if err != nil {
		log.Fatal(err)
	}

	log.Printf("Successfully authenticated to: https://%v:%d as %s\n", settings.Hostname, settings.Port, settings.Username)

	worker := Worker{
		Client:                 c,
		C2ServerId:             c2_server_id,
		TaskChannel:            make(chan mythic.Task, 100),
		ProxyChannel:           make(chan mythic.Proxy, 100),
		CallbackChannel:        make(chan mythic.Callback, 100),
		OutputChannel:          make(chan mythic.TaskOutput, 100),
		CallbackCheckinChannel: make(chan mythic.CallbackCheckin, 100),
		FileDownloadChannel:    make(chan mythic.FileDownload, 100),
		MythicClient:           m,
		Hostname:               settings.Hostname,
		Settings:               settings,
	}

	ctx, cancel = context.WithCancel(context.Background())

	var wg sync.WaitGroup

	defer m.SubscriptionClient.Close()

	wg.Add(1)

	go func() {
		defer wg.Done()
		worker.read_tasks(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		worker.read_callbacks(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		worker.read_task_output(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		worker.read_callback_checkins(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		worker.read_proxies(ctx)
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		worker.read_file_downloads(ctx)
	}()

	ticker := time.NewTicker(1 * time.Hour)

	wg.Add(1)
	go func() {
		defer wg.Done()
		worker.refresh_session(ctx, *ticker)
	}()

	subscriptions := make([]string, 0)

	// tasks
	subscription_id, err := m.TaskSubscription(worker.TaskChannel)
	if err != nil {
		log.Fatal(err)
	}
	// log.Printf("tasks: %s\n", subscription_id)
	subscriptions = append(subscriptions, subscription_id)

	// Task output
	subscription_id, err = m.TaskOutputSubscription(worker.OutputChannel)
	if err != nil {
		log.Fatal(err)
	}
	// log.Printf("task output: %s\n", subscription_id)
	subscriptions = append(subscriptions, subscription_id)

	// implants
	subscription_id, err = m.CallbackSubscription(worker.CallbackChannel)
	if err != nil {
		log.Fatal(err)
	}
	// log.Printf("implants: %s\n", subscription_id)
	subscriptions = append(subscriptions, subscription_id)

	// implant checkins

	subscription_id, err = m.CallbackCheckinSubscription(worker.CallbackCheckinChannel)
	if err != nil {
		log.Fatal(err)
	}
	// log.Printf("callback checkin: %s\n", subscription_id)
	subscriptions = append(subscriptions, subscription_id)

	subscription_id, err = m.ProxySubscription(worker.ProxyChannel)
	if err != nil {
		log.Fatal(err)

	}
	// log.Printf("proxy: %s\n", subscription_id)
	subscriptions = append(subscriptions, subscription_id)

	subscription_id, err = m.FileDownloadSubscription(worker.FileDownloadChannel)
	if err != nil {
		log.Fatal(err)

	}
	// log.Printf("proxy: %s\n", subscription_id)
	subscriptions = append(subscriptions, subscription_id)

	go m.SubscriptionClient.Run()

	temporal_client, err := client.Dial(client.Options{HostPort: temporal_host})
	if err != nil {
		log.Fatalln("Unable to create Temporal client.", err)
	}
	defer temporal_client.Close()

	temporal_worker := temporalworker.New(temporal_client, fmt.Sprintf("%s_jobs", c2_server_id), temporalworker.Options{})
	temporal_worker.RegisterActivityWithOptions(worker.SyncAll, activity.RegisterOptions{Name: "sync_all"})
	temporal_worker.RegisterActivityWithOptions(worker.RunJob, activity.RegisterOptions{Name: "run_job"})
	temporal_worker.RegisterActivityWithOptions(worker.WaitForTask, activity.RegisterOptions{Name: "wait_for_task"})

	err = temporal_worker.Start()
	if err != nil {
		log.Fatalln("Unable to start Temporal worker.", err)
	}

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)
	done := make(chan bool, 1)

	go worker.SyncAll(ctx)

	worker.send_status(ctx, "running")
	defer worker.send_status(ctx, "exited")

	go func() {
		<-sigs
		done <- true
	}()
	log.Println("Everything started")
	<-done
	log.Println("Stopping")
	ticker.Stop()

	for i := range subscriptions {
		err = m.SubscriptionClient.Unsubscribe(subscriptions[i])
		if err != nil {
			log.Println(err)
		}
	}
	m.SubscriptionClient.Close()
	temporal_worker.Stop()

	cancel()
	wg.Wait()
}
