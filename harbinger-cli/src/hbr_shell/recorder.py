# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import subprocess
import tempfile
import requests
import datetime
import json
import inquirer

# --- Debug Logging ---
DEBUG = os.environ.get("HBR_SHELL_DEBUG") == "1"

def log_debug(message):
    if DEBUG:
        print(f"[DEBUG] {message}", file=sys.stderr)

def parse_cast_file(path):
    """Parses an asciinema .cast file and extracts command chunks."""
    with open(path, 'r') as f:
        lines = f.readlines()

    if DEBUG:
        log_debug("--- Raw .cast file content ---")
        for line in lines:
            log_debug(line.strip())
        log_debug("------------------------------")

    if len(lines) < 2:
        log_debug("No events found in .cast file.")
        return json.loads(lines[0]) if lines else {}, []

    header = json.loads(lines[0])
    events = [json.loads(line) for line in lines[1:]]

    commands = []
    current_input = ""
    current_outputs = []
    start_time = None
    
    for i, event in enumerate(events):
        timestamp, event_type, content = event
        log_debug(f"Processing event {i}: type='{event_type}', content='{repr(content)}'")

        if event_type == 'i':
            if start_time is None:
                start_time = timestamp
            current_input += content
            if '\r' in content or '\n' in content:
                if current_input.strip():
                    log_debug(f"Detected command end. Input: '{current_input.strip()}'")
                    commands.append({
                        "input": current_input,
                        "outputs": current_outputs,
                        "start_time": start_time
                    })
                current_input = ""
                current_outputs = []
                start_time = None
        
        elif event_type == 'o':
            if start_time is not None:
                current_outputs.append(content)

    log_debug(f"Parsing complete. Found {len(commands)} command(s).")
    return header, commands

def synthesize_cast_file(header, command_chunk):
    """Creates a new .cast file for a single command."""
    with tempfile.NamedTemporaryFile(suffix=".cast", delete=False, mode='w') as tmpfile:
        tmpfile.write(json.dumps(header) + '\n')
        
        time_offset = 0.0
        
        tmpfile.write(json.dumps([time_offset, "i", command_chunk["input"]]) + '\n')
        time_offset += 0.1
        
        for output in command_chunk["outputs"]:
            tmpfile.write(json.dumps([time_offset, "o", output]) + '\n')
            time_offset += 0.01
            
        log_debug(f"Synthesized cast file for command '{command_chunk['input'].strip()}' at: {tmpfile.name}")
        return tmpfile.name

def main():
    """
    Main function for the hbr-shell tool.
    """
    api_url = os.environ.get("HBR_API_URL")
    api_token = os.environ.get("HBR_API_TOKEN")

    if not api_url or not api_token:
        print("Error: HBR_API_URL and HBR_API_TOKEN environment variables must be set.", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run(["asciinema", "--version"], capture_output=True, check=True, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: asciinema is not installed or not in the system's PATH.", file=sys.stderr)
        sys.exit(1)

    with tempfile.NamedTemporaryFile(suffix=".cast", delete=False) as tmpfile:
        recording_path = tmpfile.name
    log_debug(f"Temporary recording file created at: {recording_path}")

    try:
        print("Starting Harbinger shell recording. Type 'exit' or press Ctrl+D to stop.")
        title = f"Harbinger Shell Session - {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
        shell = os.environ.get("SHELL", "bash")
        command = ["asciinema", "rec", "--title", title, "--stdin", "--quiet", f"--command={shell}", recording_path]
        log_debug(f"Executing command: {' '.join(command)}")
        
        time_started = datetime.datetime.now(datetime.timezone.utc)
        process = subprocess.run(command)
        time_completed = datetime.datetime.now(datetime.timezone.utc)

        if process.returncode != 0:
            print("Recording exited with an error.", file=sys.stderr)
            return

        print("Recording finished. Parsing session...")
        header, commands = parse_cast_file(recording_path)

        if not commands:
            print("No valid commands were found in the recording. Nothing to upload.")
            return

        questions = [
            inquirer.Checkbox(
                'selected_commands',
                message="Select commands to upload to Harbinger (space to select, enter to confirm)",
                choices=[(cmd['input'].strip().replace('\r\n', ' '), i) for i, cmd in enumerate(commands)],
            ),
            inquirer.Text('description', message="Enter a description for this set of actions"),
        ]
        answers = inquirer.prompt(questions)
        
        if not answers or not answers.get('selected_commands'):
            print("No commands selected. Aborting.")
            return

        selected_indices = answers['selected_commands']
        description = answers['description']

        for index in selected_indices:
            command_chunk = commands[index]
            command_input = command_chunk['input'].strip().replace('\r\n', ' ')
            
            print(f"\nProcessing command: {command_input}")

            single_cast_path = synthesize_cast_file(header, command_chunk)

            try:
                timeline_url = f"{api_url.rstrip('/')}/manual_timeline_tasks/"
                headers = {
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                }
                timeline_payload = {
                    "name": f"Command: {command_input}",
                    "description": description,
                    "time_started": time_started.isoformat(),
                    "time_completed": time_completed.isoformat(),
                    "status": "completed",
                    "command_name": command_input.split(' ')[0],
                    "arguments": ' '.join(command_input.split(' ')[1:]),
                }

                timeline_response = requests.post(timeline_url, headers=headers, data=json.dumps(timeline_payload))

                if timeline_response.status_code != 200:
                    print(f"  Error creating timeline event: {timeline_response.status_code} - {timeline_response.text}", file=sys.stderr)
                    continue

                timeline_task_id = timeline_response.json().get("id")
                print(f"  Timeline event created with ID: {timeline_task_id}")

                upload_url = f"{api_url.rstrip('/')}/upload_file/"
                upload_headers = {"Authorization": f"Bearer {api_token}"}
                
                with open(single_cast_path, "rb") as f:
                    files = {"file": ("output.cast", f, "application/octet-stream")}
                    data = {
                        "file_type": "cast",
                        "manual_timeline_task_id": timeline_task_id,
                    }
                    upload_response = requests.post(upload_url, headers=upload_headers, data=data, params=data, files=files)

                if upload_response.status_code == 200:
                    file_data = upload_response.json()
                    print(f"  Upload successful! File ID: {file_data.get('id')}")
                else:
                    print(f"  Error uploading file: {upload_response.status_code} - {upload_response.text}", file=sys.stderr)

            finally:
                if os.path.exists(single_cast_path):
                    os.remove(single_cast_path)

    finally:
        if os.path.exists(recording_path):
            os.remove(recording_path)

if __name__ == "__main__":
    main()