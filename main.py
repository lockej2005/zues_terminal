import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import pyautogui
import mss
import json
import base64
from anthropic import Anthropic
from imgur_upload import upload_to_imgur
from overlay import apply_grid_overlay
from supabase import create_client  # Removed Client import
import threading
import time

# Initialize clients
from dotenv import load_dotenv
import os

load_dotenv()
anthropic = Anthropic(api_key=os.getenv('insert key'))

# Initialize Supabase client directly
supabase = create_client(
    supabase_url="https://aavaqbqugbiqklvtsmsj.supabase.co",
    supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdmFxYnF1Z2JpcWtsdnRzbXNqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE4MTUzMDYsImV4cCI6MjA0NzM5MTMwNn0.1604HS5mtk22B6bmdeIS7-F_sDvpYiC1aVkC4h9rMuk"
)

class ZeusTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("Zeus Terminal")
        self.root.geometry("1200x800")
        self.root.configure(bg="black")

        # Style settings
        self.text_color = "#00BFFF"
        self.frame_bg = "#101010"
        self.text_area_bg = "#202020"
        
        # Auto-task processing control
        self.auto_processing = False
        self.auto_process_thread = None

        # Create main sections
        self.create_control_panel()
        self.create_input_section()
        self.create_log_section()
        self.create_picture_section()
        
        # Task processing status
        self.currently_processing = False
        self.tasks_processed = set()  # Keep track of processed tasks

    def create_control_panel(self):
        """Create control panel for auto-processing toggle"""
        self.control_frame = tk.Frame(self.root, bg=self.frame_bg)
        self.control_frame.place(x=20, y=20, width=1160, height=50)

        # Auto-processing toggle
        self.auto_button = tk.Button(
            self.control_frame,
            text="Start Auto Processing",
            command=self.toggle_auto_processing,
            bg="#005f87",
            fg="white",
            font=("Consolas", 12)
        )
        self.auto_button.pack(side="left", padx=10, pady=5)

        # Status label
        self.status_label = tk.Label(
            self.control_frame,
            text="Status: Manual Mode",
            bg=self.frame_bg,
            fg=self.text_color,
            font=("Consolas", 12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        # Task counter
        self.task_counter = tk.Label(
            self.control_frame,
            text="Tasks Processed: 0",
            bg=self.frame_bg,
            fg=self.text_color,
            font=("Consolas", 12)
        )
        self.task_counter.pack(side="right", padx=10, pady=5)

    def create_input_section(self):
        """Create manual input section"""
        self.input_frame = tk.Frame(self.root, bg=self.frame_bg)
        self.input_frame.place(x=20, y=90, width=580, height=400)

        input_header = tk.Frame(self.input_frame, bg=self.frame_bg)
        input_header.pack(fill="x", padx=10, pady=5)

        tk.Label(input_header, text="Manual Input", bg=self.frame_bg, fg=self.text_color, font=("Consolas", 16)).pack(side="left")

        self.send_button = tk.Button(
            input_header,
            text="Send",
            command=self.handle_manual_request,
            bg="#005f87",
            fg="white",
            font=("Consolas", 12),
            relief="ridge"
        )
        self.send_button.pack(side="right", padx=5)

        self.input_text = tk.Text(
            self.input_frame,
            wrap="word",
            height=20,
            width=60,
            bg=self.text_area_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            font=("Consolas", 12)
        )
        self.input_text.pack(padx=10, pady=10)

    def create_log_section(self):
        """Create log history section"""
        self.log_frame = tk.Frame(self.root, bg=self.frame_bg)
        self.log_frame.place(x=620, y=90, width=560, height=400)

        log_header = tk.Frame(self.log_frame, bg=self.frame_bg)
        log_header.pack(fill="x", padx=10, pady=5)

        tk.Label(log_header, text="Log History", bg=self.frame_bg, fg=self.text_color, font=("Consolas", 16)).pack(side="left")

        # Add clear log button
        clear_button = tk.Button(
            log_header,
            text="Clear Log",
            command=self.clear_log,
            bg="#005f87",
            fg="white",
            font=("Consolas", 10)
        )
        clear_button.pack(side="right", padx=5)

        self.log_text = tk.Text(
            self.log_frame,
            wrap="word",
            height=20,
            width=55,
            bg=self.text_area_bg,
            fg=self.text_color,
            state="disabled",
            font=("Consolas", 12)
        )
        self.log_text.pack(padx=10, pady=10)

    def create_picture_section(self):
        """Create picture display section"""
        self.picture_frame = tk.Canvas(self.root, bg="black", width=1160, height=340)
        self.picture_frame.place(x=20, y=510)
        tk.Label(self.root, text="Picture Display", bg=self.frame_bg, fg=self.text_color, font=("Consolas", 16)).place(x=20, y=490)

    def toggle_auto_processing(self):
        """Toggle automatic task processing"""
        self.auto_processing = not self.auto_processing
        if self.auto_processing:
            self.auto_button.config(text="Stop Auto Processing", bg="#8B0000")
            self.status_label.config(text="Status: Auto Mode")
            self.send_button.config(state="disabled")
            self.input_text.config(state="disabled")
            self.start_auto_processing()
        else:
            self.auto_button.config(text="Start Auto Processing", bg="#005f87")
            self.status_label.config(text="Status: Manual Mode")
            self.send_button.config(state="normal")
            self.input_text.config(state="normal")
            if self.auto_process_thread:
                self.auto_process_thread = None

    def start_auto_processing(self):
        """Start the auto-processing thread"""
        if not self.auto_process_thread:
            self.auto_process_thread = threading.Thread(target=self.auto_process_loop, daemon=True)
            self.auto_process_thread.start()

    def auto_process_loop(self):
        """Main loop for automatic task processing"""
        while self.auto_processing:
            try:
                # Fetch pending tasks
                response = supabase.table('tasks').select('*').eq('status', 'pending').execute()
                tasks = response.data

                if not tasks:
                    self.log_action("No pending tasks found. Waiting...")
                    time.sleep(5)
                    continue

                for task in tasks:
                    if not self.auto_processing:
                        break

                    if task['id'] not in self.tasks_processed and not self.currently_processing:
                        self.log_action(f"Processing task: {task['title']}")
                        self.process_task(task)
                        self.tasks_processed.add(task['id'])

                time.sleep(2)  # Small delay between processing cycles

            except Exception as e:
                self.log_action(f"Error in auto-processing loop: {str(e)}")
                time.sleep(5)

    def process_task(self, task):
        """Process a single task from the database"""
        self.currently_processing = True
        try:
            # Take and upload screenshot
            screenshot_path = self.take_screenshot_with_grid()
            self.display_screenshot(screenshot_path)
            screenshot_url = upload_to_imgur(screenshot_path)

            # Update task status to in_progress
            supabase.table('tasks').update({'status': 'in_progress'}).eq('id', task['id']).execute()

            # Get instructions from Claude
            instructions = self.get_gpt_instructions(task['title'], screenshot_path)
            
            # Process the instructions
            if instructions:
                self.process_instructions(instructions)
                
                # Update task status and add screenshot URL
                supabase.table('tasks').update({
                    'status': 'completed',
                    'agent_message': screenshot_url
                }).eq('id', task['id']).execute()
            
            self.log_action(f"Task completed: {task['title']}")
            self.update_task_counter()
            
        except Exception as e:
            self.log_action(f"Error processing task: {str(e)}")
            supabase.table('tasks').update({
                'status': 'failed',
                'agent_message': f"Error: {str(e)}"
            }).eq('id', task['id']).execute()
        finally:
            self.currently_processing = False

    def handle_manual_request(self):
        """Handle manual input request"""
        user_input = self.input_text.get("1.0", "end").strip()
        if not user_input:
            messagebox.showerror("Error", "Please enter a request.")
            return

        screenshot_path = self.take_screenshot_with_grid()
        self.display_screenshot(screenshot_path)

        try:
            screenshot_url = upload_to_imgur(screenshot_path)
            self.log_action(f"Screenshot uploaded: {screenshot_url}")
            
            instructions = self.get_gpt_instructions(user_input, screenshot_path)
            if instructions:
                self.process_instructions(instructions)
                
        except Exception as e:
            self.log_action(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to process request:\n{str(e)}")

    def get_gpt_instructions(self, user_input, screenshot_path):
        """Get instructions from Claude"""
        try:
            # Convert the screenshot to base64
            with open(screenshot_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            # Fetch task history
            try:
                response = supabase.table('tasks').select('*').order('created_at', desc=True).limit(10).execute()
                task_history = response.data
                task_history_str = "\nTask History:\n"
                for task in task_history:
                    task_history_str += f"- {task['title']} (Status: {task['status']})\n"
            except Exception as e:
                task_history_str = "\nTask History: Unable to fetch task history\n"
                self.log_action(f"Failed to fetch task history: {str(e)}")

            # Create the system prompt
            system_prompt = f"""You are a GUI automation assistant. You will receive a screenshot with a coordinate grid overlay and instructions. 
                Return ONLY JSON following this schema:
                {{
                    "actions": [
                        {{"action": "mouse_move", "x": 100, "y": 200}},
                        {{"action": "mouse_click"}},
                        {{"action": "type_text", "text": "Hello, World!"}},
                        {{"action": "keydown", "key": "ctrl"}},  // For holding down a key
                        {{"action": "press_key", "key": "c"}},   // For single key press
                        {{"action": "keyup", "key": "ctrl"}}     // For releasing a held key
                    ]
                }}
                Reference the screenshot grid for coordinates.
                Be precise with coordinates based on the grid overlay.
                Refer to the screenshot for exact coordinates, and make judgements based off of the grid reference.
                The coordinates and relative lines are black and white for clear visibility, look at them and identify what you are trying to locate, and use the lines to determine the coordinates. 
                The user is on a MacOS computer with a single screen.

                {task_history_str}
                """

            # Make the API call to Claude with correct system parameter
            response = anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": f"Instructions: {user_input}"
                            }
                        ]
                    }
                ]
            )
            
            # Get the response content
            return json.loads(response.content[0].text)

        except Exception as e:
            self.log_action(f"Claude Error: {str(e)}")
            return None

    def take_screenshot_with_grid(self):
        """Take screenshot with grid overlay - Mac version"""
        with mss.mss() as sct:
            # On Mac, we might need to handle Retina display scaling
            monitor = sct.monitors[0]  # Main monitor
            screenshot_path = "screenshot_with_grid.png"
            sct.shot(output=screenshot_path)
            
            # Apply grid overlay accounting for Mac's scaling
            apply_grid_overlay(screenshot_path, screenshot_path, step=75)

            # Compress the image
            img = Image.open(screenshot_path)
            # Resize to a smaller size while maintaining aspect ratio
            width, height = img.size
            new_width = 1920  # or any reasonable size that works for your needs
            new_height = int(height * (new_width/width))
            img = img.resize((new_width, new_height), Image.LANCZOS)
            # Save with compression
            img.save(screenshot_path, "PNG", optimize=True, quality=85)
            
            return screenshot_path

    def display_screenshot(self, screenshot_path):
        """Display screenshot in the UI"""
        img = Image.open(screenshot_path)
        img_resized = img.resize((1120, 300))
        img_tk = ImageTk.PhotoImage(img_resized)
        self.picture_frame.delete("all")
        self.picture_frame.create_image(20, 20, anchor="nw", image=img_tk)
        self.picture_frame.image = img_tk

    def log_action(self, message):
        """Log actions to history"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")

    def clear_log(self):
        """Clear the log history"""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

    def update_task_counter(self):
        """Update the task counter display"""
        self.task_counter.config(text=f"Tasks Processed: {len(self.tasks_processed)}")

    def process_instructions(self, instructions):
        """Process JSON instructions for automation - Mac version"""
        if not isinstance(instructions, dict) or "actions" not in instructions:
            self.log_action("Invalid instructions format")
            return

        # Add Mac-specific fail-safe
        pyautogui.FAILSAFE = True
        
        for action in instructions["actions"]:
            action_type = action.get("action")
            if action_type == "mouse_click":
                pyautogui.click()
                self.log_action("Mouse clicked")
            elif action_type == "mouse_move":
                x, y = action.get("x"), action.get("y")
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y)
                    self.log_action(f"Mouse moved to ({x}, {y})")
            elif action_type == "press_key":
                key = action.get("key")
                if key:
                    mac_key = self.convert_to_mac_key(key)
                    pyautogui.press(mac_key)
                    self.log_action(f"Pressed key: {mac_key}")
            elif action_type == "keydown":
                key = action.get("key")
                if key:
                    mac_key = self.convert_to_mac_key(key)
                    pyautogui.keyDown(mac_key)
                    self.log_action(f"Holding key: {mac_key}")
            elif action_type == "keyup":
                key = action.get("key")
                if key:
                    mac_key = self.convert_to_mac_key(key)
                    pyautogui.keyUp(mac_key)
                    self.log_action(f"Released key: {mac_key}")
            elif action_type == "type_text":
                text = action.get("text")
                if text:
                    pyautogui.write(text)
                    self.log_action(f"Typed: {text}")
            else:
                self.log_action(f"Unknown action: {action_type}")
            
            time.sleep(0.5)  # Small delay between actions

    def open_mac_app(self, app_name):
        """Open a Mac application by name"""
        try:
            import subprocess
            
            # Convert common names to Mac app names
            app_mapping = {
                "music": "Music",
                "safari": "Safari",
                "chrome": "Google Chrome",
                "firefox": "Firefox",
                "terminal": "Terminal",
                "settings": "System Settings",
                # Add more mappings as needed
            }
            
            actual_app_name = app_mapping.get(app_name.lower(), app_name)
            try:
                subprocess.run(["open", "-a", actual_app_name])
                self.log_action(f"Opened {actual_app_name}")
            except Exception as e:
                self.log_action(f"Error opening app {app_name}: {str(e)}")
        except Exception as e:
            self.log_action(f"Error in open_mac_app: {str(e)}")

    def run(self):
        """Start the application with error handling"""
        try:
            # Schedule periodic task processing status updates
            def update_status():
                if self.auto_processing:
                    pending_count = len(supabase.table('tasks')
                        .select('id')
                        .eq('status', 'pending')
                        .execute()
                        .data)
                    self.status_label.config(
                        text=f"Status: Auto Mode - {pending_count} pending tasks"
                    )
                self.root.after(5000, update_status)  # Update every 5 seconds

            update_status()
            self.root.mainloop()
        except Exception as e:
            self.log_action(f"Critical error: {str(e)}")
            messagebox.showerror("Critical Error", f"Application error:\n{str(e)}")
        finally:
            if self.auto_processing:
                self.auto_processing = False
                if self.auto_process_thread:
                    self.auto_process_thread = None

def main():
    try:
        root = tk.Tk()
        app = ZeusTerminal(root)
        app.run()
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
        messagebox.showerror("Startup Error", f"Failed to start application:\n{str(e)}")

if __name__ == "__main__":
    main()