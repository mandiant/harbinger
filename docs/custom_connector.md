# Custom connectors

The docker_image should automatically start and will get the following set in the environment variables:

* `C2_SERVER_ID`: This is the id of the server and that you can give to the harbinger grpc server to retrieve the settings of your server.
* `HARBINGER_GRPC_HOST`: The harbinger grpc server, where you can retrieve the server settings.
* `TEMPORAL_HOST`: We use [temporal](https://temporal.io/) to schedule tasks on the c2 connector.

For a reference implementation check the source code of our [mythic connector](../harbinger/src/harbinger/connectors/mythic_go/).

## GRPC server

See the [protobuf files](../proto/v1/message.proto) for the specific grpc servers that are exposed.

For example to get the settings for th c2 server:

```go
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

```


## Temporal

To implement jobs and tasks on the C2 server make sure to implement the next three functions:

* SyncAll: called from the interface to force sync all data. Function name should be `sync_all` without any arguments.
* RunJob: run a job on the C2 Implant, should return a task id of that represents the task just being created. Function name should be `run_job` with a object `RunJob` as the argument. This should return a `C2Task` object.
* WaitForTask: this will give you a task id and the information from RunJob and you should return with the status after the task is completed. This should return an object like `WorkflowStepResult`.

`RunJob` and `WaitForTask` are split up to recover from outages in the client or server. This means that `RunJob` should be executed only once but `WaitForTask` can occur more often. You should listen on the queue called `{c2_server_id}_jobs`.

In go you can register the functions like this:

```go
temporal_worker := temporalworker.New(temporal_client, fmt.Sprintf("%s_jobs", c2_server_id), temporalworker.Options{})
temporal_worker.RegisterActivityWithOptions(worker.SyncAll, activity.RegisterOptions{Name: "sync_all"})
temporal_worker.RegisterActivityWithOptions(worker.RunJob, activity.RegisterOptions{Name: "run_job"})
temporal_worker.RegisterActivityWithOptions(worker.WaitForTask, activity.RegisterOptions{Name: "wait_for_task"})
```

### Function parameters

The following go structs are used in the mythic_go implementation. You should use similar structures for your chosen language and fields.

```go
type File struct {
	Id       string `json:"id"`
	Filename string `json:"filename"`
	Bucket   string `json:"bucket"`
	Path     string `json:"path"`
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
```

The `C2Task` object contains the data related to the task that was just created. Use `InternalId` and `InternalImplantId` to reference the task and implant for your server.

```go
type C2Task struct {
	InternalId        string `json:"internal_id"`
	InternalImplantId string `json:"internal_implant_id"`
	Id                string `json:"id"`
	Status            string `json:"status"`
	C2ServerId        string `json:"c2_server_id"`
}
```

The `WorkflowStepResult` indicates that the step was completed with a certain status. Use the `Id` field of the `C2Task` object as `Id` in this field.

```go
type WorkflowStepResult struct {
	Id      string `json:"id"`
	Status  string `json:"status"`
}
```
