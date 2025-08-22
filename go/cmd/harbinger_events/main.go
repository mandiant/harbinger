package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/joho/godotenv"
	"github.com/redis/go-redis/v9"
)

// EventPayload defines the structure for unmarshalling the table_name from the JSON payload.
type EventPayload struct {
	TableName string `json:"table_name"`
}

// usefulTables is a set of database table names that are considered useful for the LLM's context.
// Events from other tables will be ignored.
var usefulTables = map[string]struct{}{
	// Core Environment
	"hosts":                            {},
	"ip_addresses":                     {},
	"domains":                          {},
	"credentials":                      {},
	"passwords":                        {},
	"kerberos":                         {},
	"hashes":                           {},
	"shares":                           {},
	"share_files":                      {},
	"processes":                        {},
	"situational_awareness":            {},
	// C2 & Operations
	"c2_servers":                       {},
	"c2_implants":                      {},
	"c2_tasks":                         {},
	"c2_task_output":                   {},
	"proxies":                          {},
	"proxy_jobs":                       {},
	"proxy_job_output":                 {},
	"socks_servers":                    {},
	"files":                            {},
	"playbooks":                        {},
	// Vulnerabilities & Findings
	"issues":                           {},
	"certificate_authorities":          {},
	"certificate_templates":            {},
	"certificate_template_permissions": {},
}

// listenAndPublishRawToRedis uses a single pgx connection to listen and then publish raw bytes to Redis.
func listenAndPublishRawToRedis(ctx context.Context, pgChannel string, redisClient *redis.Client, redisPubSubChannel string, redisStreamChannel string) error {
	pgDsn := os.Getenv("PG_DSN")
	if pgDsn == "" {
		return fmt.Errorf("PG_DSN environment variable not set")
	}
	pgDsn = strings.Replace(pgDsn, "+asyncpg", "", 1)
	pgDsn = fmt.Sprintf("%s?sslmode=disable", pgDsn)
	conn, err := pgx.Connect(ctx, pgDsn)
	if err != nil {
		return fmt.Errorf("failed to connect to PostgreSQL database: %w", err)
	}
	defer conn.Close(ctx)

	_, err = conn.Exec(ctx, fmt.Sprintf("LISTEN %s", pgx.Identifier{pgChannel}.Sanitize()))
	if err != nil {
		return fmt.Errorf("failed to LISTEN on PostgreSQL channel '%s': %w", pgChannel, err)
	}

	log.Printf("Subscribed to PostgreSQL channel: %s. Publishing raw bytes to Redis channel: %s", pgChannel, redisPubSubChannel)

	for {
		select {
		case <-ctx.Done():
			log.Println("Context cancelled, unsubscribing and closing connections.")
			return nil
		default:
			waitCtx, cancelWait := context.WithTimeout(ctx, 5*time.Second)
			notification, err := conn.WaitForNotification(waitCtx)
			cancelWait()

			if err != nil {
				if errors.Is(err, context.DeadlineExceeded) {
					continue
				}
				if err.Error() == "EOF" {
					log.Printf("PostgreSQL connection closed unexpectedly. Error: %v", err)
					return fmt.Errorf("PostgreSQL connection lost: %w", err)
				}
				return fmt.Errorf("failed to wait for PostgreSQL notification: %w", err)
			}

			// ALWAYS Publish to the legacy Pub/Sub channel for backward compatibility
			pubCmd := redisClient.Publish(ctx, redisPubSubChannel, notification.Payload)
			if pubCmd.Err() != nil {
				log.Printf("Failed to publish notification to Redis Pub/Sub channel '%s': %v", redisPubSubChannel, pubCmd.Err())
			}

			// --- Event Filtering Logic for the Supervisor Stream ---
			var payload EventPayload
			if err := json.Unmarshal([]byte(notification.Payload), &payload); err != nil {
				log.Printf("Failed to unmarshal notification payload for stream filtering, skipping stream publish: %v. Payload: %s", err, notification.Payload)
				continue
			}

			if _, ok := usefulTables[payload.TableName]; !ok {
				// log.Printf("Ignoring event from table for supervisor stream: %s", payload.TableName) // Optional: uncomment for debugging
				continue // Not a useful table, so we skip publishing it to the stream.
			}
			// --- End Filtering Logic ---

			// Publish the raw byte payload from PostgreSQL to the new Redis Stream
			streamCmd := redisClient.XAdd(ctx, &redis.XAddArgs{
				Stream: redisStreamChannel,
				Values: map[string]interface{}{"payload": notification.Payload},
			})
			if streamCmd.Err() != nil {
				log.Printf("Failed to publish notification to Redis Stream '%s': %v", redisStreamChannel, streamCmd.Err())
			}
		}
	}
}

func main() {
	if err := godotenv.Load(); err != nil {
		log.Printf("No .env file found or failed to load: %v", err)
	}

	// --- Redis Configuration ---
	var rdb *redis.Client
	var err error

	// Prioritize REDIS_DSN
	redisDSN := os.Getenv("REDIS_DSN")
	if redisDSN != "" {
		opt, parseErr := redis.ParseURL(redisDSN)
		if parseErr != nil {
			log.Fatalf("Invalid REDIS_DSN: %v", parseErr)
		}
		rdb = redis.NewClient(opt)
	} else {
		// Fallback to individual components if DSN not provided
		redisAddr := os.Getenv("REDIS_HOST") // Use REDIS_HOST directly as Addr
		if redisAddr == "" {
			redisAddr = "localhost:6379" // Default if no env vars are set
		}
		redisPassword := os.Getenv("REDIS_PASSWORD")
		redisDBStr := os.Getenv("REDIS_DB")
		redisDB := 0 // Default DB

		if redisDBStr != "" {
			_, err = fmt.Sscanf(redisDBStr, "%d", &redisDB)
			if err != nil {
				log.Printf("WARNING: Invalid REDIS_DB '%s', defaulting to 0: %v", redisDBStr, err)
				redisDB = 0
			}
		}

		rdb = redis.NewClient(&redis.Options{
			Addr:     redisAddr,
			Password: redisPassword,
			DB:       redisDB,
		})
	}

	// Ping Redis to ensure connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	_, err = rdb.Ping(ctx).Result()
	cancel()
	if err != nil {
		log.Fatalf("Could not connect to Redis: %v", err)
	}
	log.Printf("Successfully connected to Redis.")

	// Define the single PostgreSQL channel your Go app will listen on
	const pgNotificationChannel = "events"
	// Define the legacy Redis Pub/Sub channel your Go app will publish to
	const redisPubSubChannel = "app_events_stream"
	// Define the new Redis Stream for the supervisor
	const redisStreamChannel = "supervisor:events"

	ctx, cancel = context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		if err := listenAndPublishRawToRedis(ctx, pgNotificationChannel, rdb, redisPubSubChannel, redisStreamChannel); err != nil {
			log.Fatalf("PostgreSQL to Redis bridge goroutine exited with fatal error: %v", err)
		}
	}()

	<-sigChan
	log.Println("Received shutdown signal, shutting down bridge...")
	cancel()

	wg.Wait()
	log.Println("PostgreSQL to Redis bridge shut down. Exiting.")
}