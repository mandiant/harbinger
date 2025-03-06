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

import (
	"context"
	"log"
	"net/http"
	"time"

	"github.com/hasura/go-graphql-client"
	"github.com/hasura/go-graphql-client/pkg/jsonutil"
)

type Mythic struct {
	Client             *graphql.Client
	Auth               AuthResponse
	SubscriptionClient *graphql.SubscriptionClient
	HttpClient         *http.Client
	ServerIp           string
	ServerPort         int
	Username           string
	Password           string
}

func (s *Mythic) GetAllCallbacks(ctx context.Context) ([]Callback, error) {
	q := AllCallbacks{}
	err := s.Client.Query(ctx, &q, nil)
	return q.Callback, err
}

func (s *Mythic) GetAllActiveCallbacks(ctx context.Context) ([]Callback, error) {
	q := AllActiveCallbacks{}
	err := s.Client.Query(ctx, &q, nil)
	return q.Callback, err
}

func (s *Mythic) GetAllTasks(ctx context.Context) ([]Task, error) {
	q := CurrentTasks{}
	err := s.Client.Query(ctx, &q, nil)
	return q.Task, err
}

func (s *Mythic) GetAllTasksForCallback(ctx context.Context, display_id int) ([]Task, error) {
	q := TaskForCallback{}
	variables := map[string]interface{}{
		"callback_display_id": display_id,
	}
	err := s.Client.Query(ctx, &q, variables)
	return q.Task, err
}

func (s *Mythic) GetOutputForTask(ctx context.Context, task_display_id int) ([]TaskOutput, error) {
	q := TaskOutputForTask{}
	variables := map[string]interface{}{
		"task_display_id": task_display_id,
	}
	err := s.Client.Query(ctx, &q, variables)
	return q.TaskOutput, err
}

func (s *Mythic) GetAllProxies(ctx context.Context) ([]Proxy, error) {
	q := ProxyQuery{}
	err := s.Client.Query(ctx, &q, nil)
	return q.Proxy, err
}

func (s *Mythic) GetAllFileDownloads(ctx context.Context) ([]FileDownload, error) {
	q := FileDownloadsQuery{}
	err := s.Client.Query(ctx, &q, nil)
	return q.Downloads, err
}

func (s *Mythic) TaskSubscription(task_channel chan Task) (string, error) {
	ts := TaskSubscription{}
	variables := map[string]interface{}{
		"now":        Timestamp(time.Now().UTC().Format(time.DateTime)),
		"batch_size": 1,
	}

	return s.SubscriptionClient.Subscribe(&ts, variables, func(dataValue []byte, errValue error) error {
		if errValue != nil {
			return nil
		}
		data := TaskStream{}
		err := jsonutil.UnmarshalGraphQL(dataValue, &data)
		if err != nil {
			log.Println(err)
		}
		for _, task := range data.Stream {
			task_channel <- task
		}
		return nil
	})
}

func (s *Mythic) CallbackSubscription(channel chan Callback) (string, error) {
	ts := CallbackSubscription{}
	variables := map[string]interface{}{
		"now":        Timestamp(time.Now().UTC().Format(time.DateTime)),
		"batch_size": 1,
	}

	return s.SubscriptionClient.Subscribe(&ts, variables, func(dataValue []byte, errValue error) error {
		if errValue != nil {
			return nil
		}
		data := CallbackStream{}
		err := jsonutil.UnmarshalGraphQL(dataValue, &data)
		if err != nil {
			log.Printf("1: %s\n", err)
			return nil
		}
		for _, callback := range data.Stream {
			channel <- callback
			// channel <- data.Callback
		}
		return nil
	})
}

func (s *Mythic) CallbackCheckinSubscription(channel chan CallbackCheckin) (string, error) {
	ts := CallbackCheckinSubscription{}
	variables := map[string]interface{}{}

	return s.SubscriptionClient.Subscribe(&ts, variables, func(dataValue []byte, errValue error) error {
		if errValue != nil {
			return nil
		}
		data := CallbackCheckinStream{}
		err := jsonutil.UnmarshalGraphQL(dataValue, &data)
		if err != nil {
			return nil
		}
		for _, callback := range data.Stream {
			channel <- callback
		}
		return nil
	})
}

func (s *Mythic) TaskOutputSubscription(channel chan TaskOutput) (string, error) {
	ts := TaskOutputSubscription{}
	variables := map[string]interface{}{
		"now":        Timestamp(time.Now().UTC().Format(time.DateTime)),
		"batch_size": 1,
	}

	return s.SubscriptionClient.Subscribe(&ts, variables, func(dataValue []byte, errValue error) error {
		if errValue != nil {
			return nil
		}
		data := TaskOutputStream{}
		err := jsonutil.UnmarshalGraphQL(dataValue, &data)
		if err != nil {
			log.Println(err)
		}
		for _, output := range data.Stream {
			channel <- output
		}
		return nil
	})
}

func (s *Mythic) ProxySubscription(channel chan Proxy) (string, error) {
	ts := ProxySubscription{}

	variables := map[string]interface{}{}

	return s.SubscriptionClient.Subscribe(&ts, variables, func(dataValue []byte, errValue error) error {
		if errValue != nil {
			return nil
		}
		data := ProxyStream{}
		err := jsonutil.UnmarshalGraphQL(dataValue, &data)
		if err != nil {
			log.Println(err)
		}
		for _, proxy := range data.Proxy {
			channel <- proxy
		}
		return nil
	})
}

func (s *Mythic) FileDownloadSubscription(channel chan FileDownload) (string, error) {
	ts := FileDownloadSubscription{}

	variables := map[string]interface{}{
		"now":        Timestamp(time.Now().UTC().Format(time.DateTime)),
		"batch_size": 1,
	}

	return s.SubscriptionClient.Subscribe(&ts, variables, func(dataValue []byte, errValue error) error {
		if errValue != nil {
			return nil
		}
		data := FileDownloadStream{}
		err := jsonutil.UnmarshalGraphQL(dataValue, &data)
		if err != nil {
			log.Println(err)
		}
		for _, download := range data.Downloads {
			channel <- download
		}
		return nil
	})
}

func (s *Mythic) GetCallbackDisplayIdForId(ctx context.Context, callback_id int) (int, error) {
	q := CallbackByPk{}
	variables := map[string]interface{}{
		"id": callback_id,
	}
	err := s.Client.Query(ctx, &q, variables)
	return q.Display_Id, err
}

func (s *Mythic) IssueTask(ctx context.Context, callback_id int, command_name string, parameters string) (CreatedTask, error) {
	q := CreateTask{}
	variables := map[string]interface{}{
		"callback_id": callback_id,
		"command":     command_name,
		"params":      parameters,
	}
	err := s.Client.Mutate(context.Background(), &q, variables)
	return q.Task, err
}

func (s *Mythic) SpecificTaskSubscription(task_channel chan Task, task_id int) (string, error) {
	ts := SpecificTaskSubscription{}
	variables := map[string]interface{}{
		"task_id": task_id,
	}

	return s.SubscriptionClient.Subscribe(&ts, variables, func(dataValue []byte, errValue error) error {
		if errValue != nil {
			return nil
		}
		data := TaskStream{}
		err := jsonutil.UnmarshalGraphQL(dataValue, &data)
		if err != nil {
			log.Println(err)
			return nil
		}
		for _, task := range data.Stream {
			task_channel <- task
		}
		return nil
	})
}
