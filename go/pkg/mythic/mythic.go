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
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"net/url"
	"os"

	"github.com/hasura/go-graphql-client"
)

var Header = ""

func Login(server_ip string, server_port int, username string, password string) (Mythic, error) {
	base_url := fmt.Sprintf("https://%s:%d", server_ip, server_port)
	wss_url := fmt.Sprintf("wss://%s:%d/graphql", server_ip, server_port)

	m := Mythic{}

	auth := LoginMessage{Username: username, Password: password}

	data, err := json.Marshal(auth)

	if err != nil {
		return m, fmt.Errorf("[login] json error: %w", err)
	}

	request, err := http.NewRequest(http.MethodPost, fmt.Sprintf("%s/auth", base_url), bytes.NewBuffer(data))

	if err != nil {
		return m, fmt.Errorf("[login] new request error: %w", err)
	}

	request.Header.Set("Content-Type", "application/json; charset=UTF-8")

	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	client := &http.Client{Transport: tr}
	response, err := client.Do(request)

	if err != nil {
		return m, fmt.Errorf("[login] request do error: %w", err)
	}

	defer response.Body.Close()

	if response.StatusCode != 200 {
		return m, fmt.Errorf("[login] incorrect username or password")
	}

	body, _ := io.ReadAll(response.Body)
	auth_response := AuthResponse{}
	err = json.Unmarshal(body, &auth_response)
	if err != nil {
		return m, fmt.Errorf("[login] json unmarshal error: %w", err)
	}

	Header = fmt.Sprintf("Bearer %s", auth_response.AccessToken)

	httpClient := &http.Client{
		Transport: &http.Transport{
			Proxy: func(r *http.Request) (*url.URL, error) {
				r.Header.Set("Authorization", Header)
				return nil, nil
			},
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		},
	}

	graphql_client := graphql.NewClient(fmt.Sprintf("%s/graphql/", base_url), httpClient)
	subscription_client := graphql.NewSubscriptionClient(wss_url).
		WithWebSocketOptions(graphql.WebsocketOptions{HTTPClient: httpClient}).
		WithConnectionParams(map[string]interface{}{
			"headers": map[string]string{
				"Authorization": Header,
			},
		}) //.WithLog(log.Print)

	m = Mythic{
		Client:             graphql_client,
		Auth:               auth_response,
		SubscriptionClient: subscription_client,
		HttpClient:         httpClient,
		ServerIp:           server_ip,
		ServerPort:         server_port,
		Password:           password,
		Username:           username,
	}

	return m, nil
}

func (m *Mythic) RefreshSession() error {
	url := fmt.Sprintf("https://%s:%d/refresh", m.ServerIp, m.ServerPort)

	auth := RefreshMessage{RefreshToken: m.Auth.RefreshToken, AccessToken: m.Auth.AccessToken}

	data, err := json.Marshal(auth)

	if err != nil {
		return fmt.Errorf("[refreshsession] marshal error: %w", err)
	}

	request, err := http.NewRequest(http.MethodPost, url, bytes.NewBuffer(data))

	if err != nil {
		return fmt.Errorf("[refreshsession] new request error: %w", err)
	}

	request.Header.Set("Content-Type", "application/json; charset=UTF-8")

	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	client := &http.Client{Transport: tr}
	response, err := client.Do(request)

	if err != nil {
		return fmt.Errorf("[refreshsession] request do error: %w", err)
	}

	defer response.Body.Close()

	body, _ := io.ReadAll(response.Body)
	auth_response := AuthResponse{}
	err = json.Unmarshal(body, &auth_response)
	if err != nil {
		return err
	}

	if auth_response.AccessToken != "" {
		m.Auth.AccessToken = auth_response.AccessToken
		m.Auth.RefreshToken = auth_response.RefreshToken
		Header = fmt.Sprintf("Bearer %s", auth_response.AccessToken)
	} else {
		log.Println("[warning] no access token received, trying to log in again")
		new_m, err := Login(m.ServerIp, m.ServerPort, m.Username, m.Password)
		if err != nil {
			log.Println("[warning] login failed.")
			return err
		}
		m.Auth.AccessToken = new_m.Auth.AccessToken
		m.Auth.RefreshToken = new_m.Auth.RefreshToken
	}
	return nil
}

func (m *Mythic) DownloadFile(filepath string, agent_file_id string) error {
	// Create the file
	out, err := os.Create(filepath)
	if err != nil {
		return err
	}
	defer out.Close()

	// url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/direct/download/{file_uuid}"
	url := fmt.Sprintf("https://%s:%d/direct/download/%s", m.ServerIp, m.ServerPort, agent_file_id)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}

	resp, err := m.HttpClient.Do(req)
	if err != nil {
		return err
	}

	defer resp.Body.Close()

	// Check server response
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("bad status: %s", resp.Status)
	}

	// Writer the body to file
	_, err = io.Copy(out, resp.Body)
	if err != nil {
		return err
	}

	return nil
}

func (m *Mythic) RegisterFile(filename string, data []byte) (FileUploadResult, error) {
	// Create the file
	result := FileUploadResult{}
	buf := new(bytes.Buffer)
	w := multipart.NewWriter(buf)

	// url = f"{mythic.http}{mythic.server_ip}:{mythic.server_port}/direct/download/{file_uuid}"
	url := fmt.Sprintf("https://%s:%d/api/v1.4/task_upload_file_webhook", m.ServerIp, m.ServerPort)

	part, err := w.CreateFormFile("file", filename)
	if err != nil {
		return result, err
	}

	part.Write(data)

	err = w.Close()
	if err != nil {
		return result, err
	}

	req, err := http.NewRequest("POST", url, buf)
	if err != nil {
		return result, err
	}

	req.Header.Add("Content-Type", w.FormDataContentType())

	resp, err := m.HttpClient.Do(req)
	if err != nil {
		return result, err
	}

	defer resp.Body.Close()

	// Check server response
	if resp.StatusCode != http.StatusOK {
		return result, fmt.Errorf("bad status: %s", resp.Status)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return result, err
	}

	err = json.Unmarshal(body, &result)
	return result, err
}
