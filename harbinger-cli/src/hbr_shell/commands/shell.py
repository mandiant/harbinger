import os
import sys
import subprocess
import tempfile
import requests
import datetime
import json
import inquirer
import configparser
from pathlib import Path

# --- Debug Logging ---
DEBUG = os.environ.get("HBR_SHELL_DEBUG") == "1"

def log_debug(message):
    if DEBUG:
        print(f"[DEBUG] {message}", file=sys.stderr)

def get_auth_config():
    """Get API URL and cookie from config file."""
    config_dir = Path.home() / ".harbinger"
    config_file = config_dir / "config"
    
    if not config_file.exists():
        return None, None

    config = configparser.ConfigParser()
    config.read(config_file)
    
    api_url = config.get('auth', 'api_url', fallback=None)
    cookie = config.get('auth', 'cookie', fallback=None)
    
    return api_url, cookie

def parse_cast_file(path):
    """
    Parses an asciinema .cast file and extracts command chunks by detecting
    the shell prompt's reappearance.
    """
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

    # --- 1. Find the initial prompt signature ---
    initial_output = ""
    first_input_index = -1
    for i, event in enumerate(events):
        if event[1] == 'i':
            first_input_index = i
            break
        elif event[1] == 'o':
            initial_output += event[2]

    if first_input_index == -1:
        log_debug("No user input found in recording.")
        return header, []

    # The prompt is assumed to be the last non-empty line of output before the first input.
    # This is a heuristic but should be reliable for most shell prompts (bash, zsh, etc.).
    prompt_lines = [line for line in initial_output.splitlines() if line.strip()]
    prompt_signature = prompt_lines[-1] if prompt_lines else ""
    log_debug(f"Detected prompt signature: '{prompt_signature}'")

    if not prompt_signature:
        log_debug("Could not determine a prompt signature. Falling back to simple parsing.")
        # This fallback can be implemented if needed, for now we'll proceed.

    # --- 2. Group commands based on prompt appearances ---
    commands = []
    current_command_events = []
    in_command = False

    # Start processing from the first input event.
    for event in events[first_input_index:]:
        timestamp, event_type, content = event

        if not in_command:
            # A new command must start with an input event.
            if event_type == 'i':
                in_command = True
                current_command_events.append(event)
        else:
            current_command_events.append(event)
            # A command is considered finished when the prompt signature appears in an output event.
            # We check if the last line of the current output matches the prompt.
            if event_type == 'o':
                output_lines = content.splitlines()
                if output_lines and output_lines[-1].endswith(prompt_signature):
                    log_debug("Detected end of command via prompt.")
                    
                    # Finalize the current command chunk
                    command_input = "".join([e[2] for e in current_command_events if e[1] == 'i'])
                    command_outputs = [e[2] for e in current_command_events if e[1] == 'o']
                    start_time = current_command_events[0][0]
                    end_time = timestamp # Capture the timestamp of the last event

                    if command_input.strip():
                        commands.append({
                            "input": command_input,
                            "outputs": command_outputs,
                            "start_time": start_time,
                            "end_time": end_time,
                            "events": current_command_events,
                        })

                    # Reset for the next command
                    in_command = False
                    current_command_events = []

    # Add any remaining events as the last command if the recording was cut off
    if current_command_events:
        log_debug("Saving final command chunk from remaining events.")
        command_input = "".join([e[2] for e in current_command_events if e[1] == 'i'])
        command_outputs = [e[2] for e in current_command_events if e[1] == 'o']
        start_time = current_command_events[0][0]
        end_time = current_command_events[-1][0] # Timestamp of the last event
        if command_input.strip():
            commands.append({
                "input": command_input,
                "outputs": command_outputs,
                "start_time": start_time,
                "end_time": end_time,
                "events": current_command_events,
            })

    log_debug(f"Parsing complete. Found {len(commands)} command(s).")
    return header, commands

def synthesize_cast_file(header, command_chunk):
    """Creates a new .cast file for a single command, preserving original timing."""
    with tempfile.NamedTemporaryFile(suffix=".cast", delete=False, mode='w') as tmpfile:
        # The header needs to be modified to reflect the new duration.
        chunk_start_time = command_chunk['start_time']
        chunk_end_time = command_chunk['end_time']
        new_header = header.copy()
        new_header['duration'] = chunk_end_time - chunk_start_time
        
        tmpfile.write(json.dumps(new_header) + '\n')
        
        # Write events with timestamps relative to the start of the chunk
        for event in command_chunk["events"]:
            original_timestamp, event_type, content = event
            relative_timestamp = original_timestamp - chunk_start_time
            tmpfile.write(json.dumps([relative_timestamp, event_type, content]) + '\n')
            
        log_debug(f"Synthesized cast file for command '{command_chunk['input'].splitlines()[0].strip()}' at: {tmpfile.name}")
        return tmpfile.name

def setup(subparsers):
    """Setup the shell command."""
    parser = subparsers.add_parser("shell", help="Record a shell session")
    parser.set_defaults(func=run)

def run(args):
    """
    Main function for the hbr-shell tool.
    """
    api_url, cookie = get_auth_config()

    if not api_url or not cookie:
        print("Error: Not logged in. Please run 'hbr login' first.", file=sys.stderr)
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

        # The display choice for each command is its first line of input.
        choices = [
            (cmd['input'].splitlines()[0].strip(), i) 
            for i, cmd in enumerate(commands) if cmd['input'].strip()
        ]
        extended_choices = [
            "---",
            ("Select All (overrides other selections)", "all"),
            ("Select None (overrides other selections)", "none"),
            "---",
        ] + choices

        questions = [
            inquirer.Checkbox(
                'selected_commands',
                message="Select commands to upload. 'Select All' or 'Select None' will override individual selections.",
                choices=extended_choices,
            ),
            inquirer.Text('description', message="Enter a description for this set of actions"),
        ]
        answers = inquirer.prompt(questions)

        if not answers:
            print("Aborting.")
            return

        selected_options = answers.get('selected_commands', [])

        if 'all' in selected_options:
            selected_indices = list(range(len(commands)))
            print("Processing 'Select All', all commands will be uploaded.")
        elif 'none' in selected_options:
            selected_indices = []
        else:
            selected_indices = [opt for opt in selected_options if isinstance(opt, int)]

        if not selected_indices:
            if 'none' in selected_options:
                print("'Select None' chosen. Aborting.")
            else:
                print("No commands selected. Aborting.")
            return
        
        description = answers['description']

        for index in selected_indices:
            command_chunk = commands[index]
            
            # The initial command is the first line of the input chunk.
            initial_command = command_chunk['input'].splitlines()[0].strip()
            
            print(f"\nProcessing command: {initial_command}")

            single_cast_path = synthesize_cast_file(header, command_chunk)

            try:
                timeline_url = f"{api_url.rstrip('/')}/manual_timeline_tasks/"
                headers = { "Content-Type": "application/json" }
                cookies = { "fastapiusersauth": cookie }

                # Calculate the absolute start and end times for the command.
                relative_start = command_chunk['start_time']
                relative_end = command_chunk['end_time']
                absolute_start = time_started + datetime.timedelta(seconds=relative_start)
                absolute_end = time_started + datetime.timedelta(seconds=relative_end)

                # Split the initial command into the command name and its arguments.
                command_parts = initial_command.split(' ')
                command_name = command_parts[0]
                arguments = ' '.join(command_parts[1:])

                timeline_payload = {
                    "name": f"Command: {initial_command}",
                    "description": description,
                    "time_started": absolute_start.isoformat(),
                    "time_completed": absolute_end.isoformat(),
                    "status": "completed",
                    "command_name": command_name,
                    "arguments": arguments,
                }

<<<<<<< HEAD
                timeline_response = requests.post(timeline_url, headers=headers, cookies=cookies, data=json.dumps(timeline_payload))
=======
                timeline_response = requests.post(timeline_url, headers=headers, cookies=cookies, data=json.dumps(timeline_payload), verify=False)
>>>>>>> main

                if timeline_response.status_code != 200:
                    print(f"  Error creating timeline event: {timeline_response.status_code} - {timeline_response.text}", file=sys.stderr)
                    continue

                timeline_task_id = timeline_response.json().get("id")
                print(f"  Timeline event created with ID: {timeline_task_id}")

                upload_url = f"{api_url.rstrip('/')}/upload_file/"
                
                with open(single_cast_path, "rb") as f:
                    files = {"file": ("output.cast", f, "application/octet-stream")}
                    data = {
                        "file_type": "cast",
                        "manual_timeline_task_id": timeline_task_id,
                    }
<<<<<<< HEAD
                    upload_response = requests.post(upload_url, cookies=cookies, data=data, params=data, files=files)
=======
                    upload_response = requests.post(upload_url, cookies=cookies, data=data, params=data, files=files, verify=False)
>>>>>>> main

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
