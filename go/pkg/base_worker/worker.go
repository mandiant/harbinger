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

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	messagesv1 "github.com/mandiant/harbinger/go/proto/v1" // Corrected import path for protobufs
	"go.temporal.io/sdk/activity"
	"go.temporal.io/sdk/client"
	temporalworker "go.temporal.io/sdk/worker"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// DefaultC2Bridge provides common fields and a default InitializeC2 implementation.
// Concrete C2Bridge implementations can embed this struct.
type DefaultC2Bridge struct {
	HarbingerClient messagesv1.HarbingerClient
	C2ServerID      string
	Settings        *messagesv1.SettingsResponse // The fetched settings
}

// Initialize sets the common fields, no need to implement this yourself.
func (d *DefaultC2Bridge) Initialize(
	ctx context.Context, // Keep context for future extensibility if this default needs it
	harbingerClient messagesv1.HarbingerClient,
	c2ServerID string,
	settings *messagesv1.SettingsResponse,
) error {
	log.Println("INITIALIZE!")
	d.HarbingerClient = harbingerClient
	d.C2ServerID = c2ServerID
	d.Settings = settings
	return nil
}

// Workflow activities common to all C2 integrations.
// These methods will be directly called and registered by the base worker.
type WorkflowActivities interface {
	SyncAll(ctx context.Context) error
	RunJob(ctx context.Context, job RunJob) (C2Task, error)
	WaitForTask(ctx context.Context, task C2Task) (WorkflowStepResult, error)
}

// C2Bridge defines the interface that any specific C2 integration must implement.
// This decouples the generic worker logic from C2-specific interactions.
// It embeds the WorkflowActivities interface, meaning any C2Bridge must also
// implement SyncAll, RunJob, and WaitForTask.
type C2Bridge interface {
	WorkflowActivities // Embed the common workflow activities
	// Name returns the name of the C2 server (e.g., "mythic", "cobaltstrike").
	Name() string

	// Initialize stores the client and other fields.
	Initialize(ctx context.Context, harbingerClient messagesv1.HarbingerClient, c2ServerID string, settings *messagesv1.SettingsResponse) error
	// InitializeC2 sets up the C2-specific client and performs any initial login/setup.
	// SettingsResponse is provided by the base worker.
	InitializeC2(ctx context.Context, settings *messagesv1.SettingsResponse) error

	// RunC2SpecificReaders starts all C2-specific goroutines for reading data (tasks, outputs, etc.).
	// It should use the provided context for cancellation and the WaitGroup for graceful shutdown.
	RunC2SpecificReaders(ctx context.Context, wg *sync.WaitGroup)

	// SendC2Status updates the C2 server's status.
	// (This can be handled by the base worker, but kept here if C2-specific logic is needed).
	SendC2Status(ctx context.Context, status string) error

	// RefreshC2Session attempts to refresh the C2 session (e.g., re-authenticate).
	RefreshC2Session() error

	// Stop performs any necessary stop actions for the C2 bridge (e.g., closing subscriptions).
	Stop() error
}

// Worker represents the generic base worker for a C2 integration.
type Worker struct {
	HarbingerClient messagesv1.HarbingerClient   // Client to the main Harbinger gRPC service
	C2ServerID      string                       // Unique ID for this C2 server instance
	Hostname        string                       // Hostname where this worker is running (optional, but useful)
	Settings        *messagesv1.SettingsResponse // Settings fetched from Harbinger for this C2
	C2              C2Bridge                     // The specific C2 implementation (e.g., MythicBridge)
	temporalClient  client.Client
	temporalWorker  temporalworker.Worker
	grpcConn        *grpc.ClientConn // Store for proper closing
}

// NewWorker initializes a new generic Worker.
// The `c2Bridge` parameter is the concrete implementation for a specific C2.
func NewWorker(c2Bridge C2Bridge) (*Worker, error) {
	c2ServerID := os.Getenv("C2_SERVER_ID")
	if c2ServerID == "" {
		return nil, fmt.Errorf("C2_SERVER_ID was not set")
	}
	harbingerGRPCHost := os.Getenv("HARBINGER_GRPC_HOST")
	if harbingerGRPCHost == "" {
		return nil, fmt.Errorf("HARBINGER_GRPC_HOST was not set")
	}
	temporalHost := os.Getenv("TEMPORAL_HOST")
	if temporalHost == "" {
		return nil, fmt.Errorf("please set TEMPORAL_HOST env variable")
	}

	// 1. Setup gRPC client to Harbinger
	conn, err := grpc.NewClient(harbingerGRPCHost, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Harbinger gRPC: %w", err)
	}

	harbingerClient := messagesv1.NewHarbingerClient(conn)

	// Fetch settings for this C2 server
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second) // Increased timeout slightly
	defer cancel()

	settingsReq := messagesv1.SettingsRequest{C2ServerId: c2ServerID}
	settings, err := harbingerClient.GetSettings(ctx, &settingsReq)
	if err != nil {
		conn.Close() // Close connection if settings fetch fails
		return nil, fmt.Errorf("failed to get settings for C2 server %s: %w", c2ServerID, err)
	}
	log.Printf("Connected to Harbinger server and fetched settings for C2: %s", c2Bridge.Name())

	// 1. Initialize the specific C2 bridge
	err = c2Bridge.Initialize(ctx, harbingerClient, c2ServerID, settings)
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("failed to initialize C2 bridge (%s): %w", c2Bridge.Name(), err)
	}
	// 2. Initialize the specific C2 bridge, passing the HarbingerClient and settings
	err = c2Bridge.InitializeC2(ctx, settings)
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("failed to initialize C2 bridge (%s): %w", c2Bridge.Name(), err)
	}
	log.Printf("Successfully initialized C2: %s", c2Bridge.Name())

	// 3. Setup Temporal client
	temporalClient, err := client.Dial(client.Options{HostPort: temporalHost})
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("unable to create Temporal client: %w", err)
	}

	// 4. Create the worker struct
	w := &Worker{
		HarbingerClient: harbingerClient,
		C2ServerID:      c2ServerID,
		Hostname:        settings.Hostname, // Using settings.Hostname as worker hostname
		Settings:        settings,
		C2:              c2Bridge,
		temporalClient:  temporalClient,
		grpcConn:        conn, // Store the connection to close later
	}

	// 5. Register Temporal worker and specific activities
	temporalWorker := temporalworker.New(temporalClient, fmt.Sprintf("%s_jobs", c2ServerID), temporalworker.Options{})
	w.temporalWorker = temporalWorker

	// Directly register the required activities from the C2Bridge implementation
	temporalWorker.RegisterActivityWithOptions(w.C2.SyncAll, activity.RegisterOptions{Name: "sync_all"})
	temporalWorker.RegisterActivityWithOptions(w.C2.RunJob, activity.RegisterOptions{Name: "run_job"})
	temporalWorker.RegisterActivityWithOptions(w.C2.WaitForTask, activity.RegisterOptions{Name: "wait_for_task"})

	return w, nil
}

// Run starts the base worker, managing goroutines, signal handling, and Temporal worker.
func (w *Worker) Run() {
	defer func() {
		if w.grpcConn != nil {
			if err := w.grpcConn.Close(); err != nil {
				log.Printf("ERROR: Failed to close Harbinger gRPC connection: %v\n", err)
			}
		}
	}()
	defer w.temporalClient.Close()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	var wg sync.WaitGroup

	// Start C2-specific data readers (e.g., Mythic subscriptions)
	wg.Add(1)
	go func() {
		defer wg.Done()
		w.C2.RunC2SpecificReaders(ctx, &wg)
	}()

	// Start C2 session refresh ticker
	ticker := time.NewTicker(1 * time.Hour) // This should perhaps be configurable via settings
	wg.Add(1)
	go func() {
		defer wg.Done()
		defer ticker.Stop() // Ensure ticker is stopped on exit
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				err := w.C2.RefreshC2Session()
				if err != nil {
					log.Printf("ERROR: C2 session refresh failed for %s: %v\n", w.C2.Name(), err)
				}
			}
		}
	}()

	// Start Temporal worker
	err := w.temporalWorker.Start()
	if err != nil {
		log.Fatalf("Unable to start Temporal worker: %v", err)
	}
	log.Println("Temporal worker started.")

	// Initial sync of C2 data
	go func() {
		err := w.C2.SyncAll(ctx)
		if err != nil {
			log.Printf("WARNING: Initial C2 sync failed for %s: %v\n", w.C2.Name(), err)
		} else {
			log.Printf("Initial C2 sync for %s completed.", w.C2.Name())
		}
	}()

	// Send "running" status to Harbinger
	err = w.C2.SendC2Status(ctx, "running")
	if err != nil {
		log.Printf("WARNING: Failed to send 'running' status for %s: %v\n", w.C2.Name(), err)
	}
	defer func() {
		// Send "exited" status to Harbinger on graceful shutdown
		statusCtx, statusCancel := context.WithTimeout(context.Background(), 5*time.Second) // Small timeout for status update
		defer statusCancel()
		if err := w.C2.SendC2Status(statusCtx, "exited"); err != nil {
			log.Printf("WARNING: Failed to send 'exited' status for %s: %v\n", w.C2.Name(), err)
		}
	}()

	// Handle OS signals for graceful shutdown
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)
	done := make(chan bool, 1)

	go func() {
		<-sigs
		done <- true
	}()

	log.Printf("Base worker for %s started. Waiting for shutdown signal...", w.C2.Name())
	<-done // Block until a signal is received
	log.Printf("Shutdown signal received. Stopping base worker for %s...", w.C2.Name())
	w.C2.Stop() // Perform C2-specific cleanup
	w.temporalWorker.Stop()
	log.Println("Temporal worker stopped.")

	// Cancel context to signal goroutines to exit
	cancel()

	// Wait for all goroutines to finish
	wg.Wait()
	log.Printf("All goroutines for %s stopped. Base worker exited gracefully.", w.C2.Name())
}
