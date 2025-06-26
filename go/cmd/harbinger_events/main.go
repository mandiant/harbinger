package main

import (
	"context"
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

// listenAndPublishRawToRedis uses a single pgx connection to listen and then publish raw bytes to Redis.
func listenAndPublishRawToRedis(ctx context.Context, pgChannel string, redisClient *redis.Client, redisPubSubChannel string) error {
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

			// Publish the raw byte payload from PostgreSQL to Redis
			cmd := redisClient.Publish(ctx, redisPubSubChannel, notification.Payload)
			if cmd.Err() != nil {
				log.Printf("Failed to publish raw notification to Redis channel '%s': %v", redisPubSubChannel, cmd.Err())
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
	// Define the single Redis Pub/Sub channel your Go app will publish to
	const redisPubSubChannel = "app_events_stream" // This will be the channel your FastAPI app subscribes to

	ctx, cancel = context.WithCancel(context.Background())
	defer cancel()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		if err := listenAndPublishRawToRedis(ctx, pgNotificationChannel, rdb, redisPubSubChannel); err != nil {
			log.Fatalf("PostgreSQL to Redis bridge goroutine exited with fatal error: %v", err)
		}
	}()

	<-sigChan
	log.Println("Received shutdown signal, shutting down bridge...")
	cancel()

	wg.Wait()
	log.Println("PostgreSQL to Redis bridge shut down. Exiting.")
}
