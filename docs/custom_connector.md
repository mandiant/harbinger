# Custom Connectors

Harbinger is designed with a modular architecture to seamlessly integrate with various C2 (Command and Control) servers. This document guides you through implementing your own custom connector, leveraging the Go `base_worker` library. This library handles common infrastructure concerns, allowing you to focus purely on the unique interactions with your chosen C2 server.

After you create your code, make sure to build it into a container and [configure it in harbinger](./configuration.md#c2-connectors).

## Environment Variables

Your custom connector's Docker image should start automatically and will receive the following environment variables:

  * `C2_SERVER_ID`: A unique identifier for your C2 server instance within Harbinger. You'll use this ID to retrieve server-specific settings and when sending data to the Harbinger gRPC server.
  * `HARBINGER_GRPC_HOST`: The address of the Harbinger gRPC server. Your connector will communicate with this server to retrieve configuration, send C2 data (implants, tasks, output), and update its operational status.
  * `TEMPORAL_HOST`: The address of the Temporal server. Harbinger uses Temporal to orchestrate and schedule long-running operations (jobs and tasks) on your C2 connector, ensuring reliability and fault tolerance.

## Core Architecture: Base Worker and C2 Bridge (Go)

To simplify connector development in Go, we provide a generic `base_worker` package located at `github.com/mandiant/harbinger/go/pkg/base_worker`. This package abstracts away the boilerplate of gRPC client connections, Temporal worker setup, environment variable parsing, and graceful shutdown.

To implement a custom connector, you need to create a Go package that defines a struct that implements the `base_worker.C2Bridge` interface. This interface defines the contract for how your connector interacts with its specific C2 server and exposes the required activities for Temporal workflows.

For a reference implementation, check the source code of our [mythic connector](../go/cmd/mythic_go/main.go) and its corresponding [mythic client library](../go/pkg/mythic/mythic.go).

## Implementing the `base_worker.C2Bridge` Interface
Your custom Go connector will implement the `base_worker.C2Bridge` interface. This section focuses on the essential methods you **must** provide.

Your custom connector struct (e.g., `YourC2Bridge`) should **embed `base_worker.DefaultC2Bridge`**. This gives you access to `b.HarbingerClient` (your connection to Harbinger's gRPC server), `b.C2ServerID`, and `b.Settings` (your C2's configuration from Harbinger).

```go
package main

import (
	"context"
	"log"
	"sync"
	"time"

	"github.com/mandiant/harbinger/go/pkg/base_worker"
	"your_c2_client" // Your C2-specific client library
	messagesv1 "github.com/mandiant/harbinger/go/proto/v1" // Generated Protobufs
)

// YourC2Bridge implements the base_worker.C2Bridge interface.
type YourC2Bridge struct {
	base_worker.DefaultC2Bridge // Embed this to get HarbingerClient, C2ServerID, Settings

	yourC2Client *your_c2_client.YourC2Client // Your actual C2 client instance
	// Add other C2-specific fields like channels or state here
}

// NewYourC2Bridge creates a new instance of your custom C2Bridge.
func NewYourC2Bridge() *YourC2Bridge {
	return &YourC2Bridge{}
}

// --- Required C2Bridge Methods ---

// Name returns the name of your C2. Used for logging and identification.
func (b *YourC2Bridge) Name() string {
	return "my_custom_c2"
}

// InitializeC2 sets up your C2-specific client using settings from Harbinger.
// It's called once during startup.
func (b *YourC2Bridge) InitializeC2(ctx context.Context, harbingerClient messagesv1.HarbingerClient, c2ServerID string, settings *messagesv1.SettingsResponse) error {
	b.yourC2Client = &your_c2_client.YourC2Client{}
  // For example login or anything like that.
	return b.yourC2Client.Login(b.Settings.Hostname, int(b.Settings.Port), b.Settings.Username, b.Settings.Password)
}

// RunC2SpecificReaders starts all background goroutines that read data
// (tasks, outputs, implants, etc.) from your C2 and send it to Harbinger.
// Each goroutine *must* call `wg.Add(1)` and `defer wg.Done()`, and check `ctx.Done()`.
func (b *YourC2Bridge) RunC2SpecificReaders(ctx context.Context, wg *sync.WaitGroup) {
	wg.Add(1)
	go func() {
		defer wg.Done()
		for {
			select {
			case <-ctx.Done(): // Essential for graceful shutdown
				log.Println("YourC2 reader exiting.")
				return
			case c2Task := <-b.yourC2Client.GetTaskChannel(): // Example: Get data from your C2
				// Map c2Task to messagesv1.TaskRequest and save via b.HarbingerClient.SaveTask(ctx, ...)
				log.Printf("Received task %s from C2.", c2Task.ID)
			}
		}
	}()
	// Add other reader goroutines here (e.g., for outputs, implants, files)
}

// SyncAll performs a full, forced data synchronization from your C2 to Harbinger.
// This is a Temporal Activity, so it's resilient to failures.
func (b *YourC2Bridge) SyncAll(ctx context.Context) error {
	log.Println("Performing full synchronization with YourC2.")
	// Fetch all current implants, tasks, outputs, etc., from your C2
	// and save them to Harbinger using b.HarbingerClient.SaveImplant(), SaveTask(), etc.
	return nil // Return actual error if sync fails
}

// RunJob initiates a specific job/command on your C2 server.
// This is a Temporal Activity; it should return quickly after initiating the task.
func (b *YourC2Bridge) RunJob(ctx context.Context, job base_worker.RunJob) (base_worker.C2Task, error) {
	log.Printf("Running job %s for implant %s.", job.C2Job.Id, job.C2Implant.InternalId)
	// 1. Process job.C2Job (command, arguments, input files) and job.C2Implant.InternalId.
	// 2. Issue the command via your C2 client (e.g., b.yourC2Client.IssueCommand(...)).
	// 3. Return a base_worker.C2Task with your C2's native task ID.
	c2TaskID := "your_c2_task_id" // Replace with actual ID
	return base_worker.C2Task{InternalId: c2TaskID, InternalImplantId: job.C2Implant.InternalId, C2ServerId: b.C2ServerID, Status: "submitted"}, nil
}

// WaitForTask monitors a task on your C2 until it completes.
// This is a Temporal Activity and can be retried.
func (b *YourC2Bridge) WaitForTask(ctx context.Context, task base_worker.C2Task) (base_worker.WorkflowStepResult, error) {
	log.Printf("Waiting for task %s (internal: %s) to complete.", task.Id, task.InternalId)
	for {
		select {
		case <-ctx.Done(): // Essential for graceful shutdown
			return base_worker.WorkflowStepResult{}, ctx.Err()
		case <-time.After(5 * time.Second): // Poll your C2 for task status
			status := "completed" // Replace with b.yourC2Client.GetTaskStatus(ctx, task.InternalId)
			if status == "completed" {
				return base_worker.WorkflowStepResult{Id: task.InternalId, Status: status}, nil
			}
		}
	}
}

// SendC2Status sends the connector's operational status to Harbinger.
func (b *YourC2Bridge) SendC2Status(ctx context.Context, status string) error {
	log.Printf("Sending status '%s' to Harbinger.", status)
	_, err := b.HarbingerClient.SetC2ServerStatus(ctx, &messagesv1.C2ServerStatusRequest{C2ServerId: b.C2ServerID, Status: status, Name: b.Name()})
	return err
}

// RefreshC2Session attempts to refresh authentication/session with your C2.
// Called periodically by the base worker.
func (b *YourC2Bridge) RefreshC2Session() error {
	log.Println("Refreshing C2 session.")
	return b.yourC2Client.RefreshAuthentication()
}

// Cleanup performs final cleanup, closing connections/subscriptions to your C2.
// Called during graceful shutdown.
func (b *YourC2Bridge) Cleanup() {
	log.Println("Performing cleanup for C2.")
	if b.yourC2Client != nil {
		b.yourC2Client.CloseConnections()
	}
}

// --- Main Application Entry Point ---

// The `main` function simply initializes your custom bridge and runs the base worker.
func main() {
	yourC2Bridge := NewYourC2Bridge()
	worker, err := base_worker.NewWorker(yourC2Bridge)
	if err != nil {
		log.Fatalf("Failed to initialize base worker: %v", err)
	}
	worker.Run() // This starts everything and manages graceful shutdown.
}
```
