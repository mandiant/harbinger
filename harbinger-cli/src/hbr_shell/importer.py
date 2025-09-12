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

import argparse
import datetime
import json
import os
import sys
import tempfile

import inquirer
import requests

# --- Debug Logging ---
DEBUG = os.environ.get("HBR_SHELL_DEBUG") == "1"


def log_debug(message):
    if DEBUG:
        print(f"[DEBUG] {message}", file=sys.stderr)


def parse_cast_file(path):
    """Parses an asciinema .cast file and extracts command chunks by detecting
    the shell prompt's reappearance.
    """
    with open(path) as f:
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

    initial_output = ""
    first_input_index = -1
    for i, event in enumerate(events):
        if event[1] == "i":
            first_input_index = i
            break
        elif event[1] == "o":
            initial_output += event[2]

    if first_input_index == -1:
        log_debug("No user input found in recording.")
        return header, []

    prompt_lines = [line for line in initial_output.splitlines() if line.strip()]
    prompt_signature = prompt_lines[-1] if prompt_lines else ""
    log_debug(f"Detected prompt signature: '{prompt_signature}'")

    if not prompt_signature:
        log_debug("Could not determine a prompt signature.")

    commands = []
    current_command_events = []
    in_command = False

    for event in events[first_input_index:]:
        timestamp, event_type, content = event

        if not in_command:
            if event_type == "i":
                in_command = True
                current_command_events.append(event)
        else:
            current_command_events.append(event)
            if event_type == "o":
                output_lines = content.splitlines()
                if output_lines and output_lines[-1].endswith(prompt_signature):
                    log_debug("Detected end of command via prompt.")

                    command_input = "".join(
                        [e[2] for e in current_command_events if e[1] == "i"],
                    )
                    command_outputs = [
                        e[2] for e in current_command_events if e[1] == "o"
                    ]
                    start_time = current_command_events[0][0]
                    end_time = timestamp

                    if command_input.strip():
                        commands.append(
                            {
                                "input": command_input,
                                "outputs": command_outputs,
                                "start_time": start_time,
                                "end_time": end_time,
                                "events": current_command_events,
                            },
                        )

                    in_command = False
                    current_command_events = []

    if current_command_events:
        log_debug("Saving final command chunk from remaining events.")
        command_input = "".join([e[2] for e in current_command_events if e[1] == "i"])
        command_outputs = [e[2] for e in current_command_events if e[1] == "o"]
        start_time = current_command_events[0][0]
        end_time = current_command_events[-1][0]
        if command_input.strip():
            commands.append(
                {
                    "input": command_input,
                    "outputs": command_outputs,
                    "start_time": start_time,
                    "end_time": end_time,
                    "events": current_command_events,
                },
            )

    log_debug(f"Parsing complete. Found {len(commands)} command(s).")
    return header, commands


def synthesize_cast_file(header, command_chunk):
    """Creates a new .cast file for a single command, preserving original timing."""
    with tempfile.NamedTemporaryFile(suffix=".cast", delete=False, mode="w") as tmpfile:
        chunk_start_time = command_chunk["start_time"]
        chunk_end_time = command_chunk["end_time"]
        new_header = header.copy()
        new_header["duration"] = chunk_end_time - chunk_start_time

        tmpfile.write(json.dumps(new_header) + "\n")

        for event in command_chunk["events"]:
            original_timestamp, event_type, content = event
            relative_timestamp = original_timestamp - chunk_start_time
            tmpfile.write(json.dumps([relative_timestamp, event_type, content]) + "\n")

        log_debug(
            f"Synthesized cast file for command '{command_chunk['input'].splitlines()[0].strip()}' at: {tmpfile.name}",
        )
        return tmpfile.name


def main():
    """Main function for the hbr-import tool."""
    parser = argparse.ArgumentParser(
        description="Import an asciinema .cast file into Harbinger.",
    )
    parser.add_argument("cast_file", help="Path to the .cast file to import.")
    args = parser.parse_args()

    api_url = os.environ.get("HBR_API_URL")
    api_token = os.environ.get("HBR_API_TOKEN")

    if not api_url or not api_token:
        print(
            "Error: HBR_API_URL and HBR_API_TOKEN environment variables must be set.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.exists(args.cast_file):
        print(f"Error: File not found at '{args.cast_file}'", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing session from '{args.cast_file}'...")
    header, commands = parse_cast_file(args.cast_file)

    if not commands:
        print("No valid commands were found in the recording. Nothing to upload.")
        return

    # The start time of the session is in the header's timestamp field.
    time_started = datetime.datetime.fromtimestamp(
        header.get("timestamp", 0),
        tz=datetime.timezone.utc,
    )

    choices = [
        (cmd["input"].splitlines()[0].strip(), i)
        for i, cmd in enumerate(commands)
        if cmd["input"].strip()
    ]
    extended_choices = [
        "---",
        ("Select All (overrides other selections)", "all"),
        ("Select None (overrides other selections)", "none"),
        "---",
    ] + choices

    questions = [
        inquirer.Checkbox(
            "selected_commands",
            message="Select commands to upload. 'Select All' or 'Select None' will override individual selections.",
            choices=extended_choices,
        ),
        inquirer.Text(
            "description",
            message="Enter a description for this set of actions",
        ),
    ]
    answers = inquirer.prompt(questions)

    if not answers:
        print("Aborting.")
        return

    selected_options = answers.get("selected_commands", [])

    if "all" in selected_options:
        selected_indices = list(range(len(commands)))
        print("Processing 'Select All', all commands will be uploaded.")
    elif "none" in selected_options:
        selected_indices = []
    else:
        selected_indices = [opt for opt in selected_options if isinstance(opt, int)]

    if not selected_indices:
        if "none" in selected_options:
            print("'Select None' chosen. Aborting.")
        else:
            print("No commands selected. Aborting.")
        return

    description = answers["description"]

    for index in selected_indices:
        command_chunk = commands[index]
        initial_command = command_chunk["input"].splitlines()[0].strip()

        print(f"\nProcessing command: {initial_command}")

        single_cast_path = synthesize_cast_file(header, command_chunk)

        try:
            timeline_url = f"{api_url.rstrip('/')}/manual_timeline_tasks/"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            }

            relative_start = command_chunk["start_time"]
            relative_end = command_chunk["end_time"]
            absolute_start = time_started + datetime.timedelta(seconds=relative_start)
            absolute_end = time_started + datetime.timedelta(seconds=relative_end)

            command_parts = initial_command.split(" ")
            command_name = command_parts[0]
            arguments = " ".join(command_parts[1:])

            timeline_payload = {
                "name": f"Command: {initial_command}",
                "description": description,
                "time_started": absolute_start.isoformat(),
                "time_completed": absolute_end.isoformat(),
                "status": "completed",
                "command_name": command_name,
                "arguments": arguments,
            }

            timeline_response = requests.post(
                timeline_url,
                headers=headers,
                data=json.dumps(timeline_payload),
                verify=False,
            )

            if timeline_response.status_code != 200:
                print(
                    f"  Error creating timeline event: {timeline_response.status_code} - {timeline_response.text}",
                    file=sys.stderr,
                )
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
                upload_response = requests.post(
                    upload_url,
                    headers=upload_headers,
                    data=data,
                    params=data,
                    files=files,
                    verify=False,
                )

            if upload_response.status_code == 200:
                file_data = upload_response.json()
                print(f"  Upload successful! File ID: {file_data.get('id')}")
            else:
                print(
                    f"  Error uploading file: {upload_response.status_code} - {upload_response.text}",
                    file=sys.stderr,
                )

        finally:
            if os.path.exists(single_cast_path):
                os.remove(single_cast_path)


if __name__ == "__main__":
    main()
