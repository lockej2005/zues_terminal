import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import pyautogui
import mss
import json
from openai import OpenAI
from imgur_upload import upload_to_imgur
from overlay import apply_grid_overlay
from supabase import create_client, Client
from auto_processor import AutoProcessor

# Initialize clients
client = OpenAI(api_key="sk-proj-5MN52DibgpFgQfMKAJiVT3BlbkFJktsJW2uQhIuIGvE24viw")
supabase: Client = create_client(
    "https://aavaqbqugbiqklvtsmsj.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdmFxYnF1Z2JpcWtsdnRzbXNqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE4MTUzMDYsImV4cCI6MjA0NzM5MTMwNn0.1604HS5mtk22B6bmdeIS7-F_sDvpYiC1aVkC4h9rMuk"
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
        
        # Initialize auto processor
        self.auto_processor = AutoProcessor(
            supabase=supabase,
            process_task_fn=self.process_task,
            log_action_fn=self.log_action
        )

        # Create main sections
        self.create_control_panel()
        self.create_input_section()
        self.create_log_section()
        self.create_picture_section()

    def create_control_panel(self):
        self.control_frame = tk.Frame(self.root, bg=self.frame_bg)
        self.control_frame.place(x=20, y=20, width=1160, height=50)

        self.auto_button = tk.Button(
            self.control_frame,
            text="Start Auto Processing",
            command=self.toggle_auto_processing,
            bg="#005f87",
            fg="white",
            font=("Consolas", 12)
        )
        self.auto_button.pack(side="left", padx=10, pady=5)

        self.status_label = tk.Label(
            self.control_frame,
            text="Status: Manual Mode",
            bg=self.frame_bg,
            fg=self.text_color,
            font=("Consolas", 12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        # Add task counter
        self.task_counter = tk.Label(
            self.control_frame,
            text="Tasks Processed: 0",
            bg=self.frame_bg,
            fg=self.text_color,
            font=("Consolas", 12)
        )
        self.task_counter.pack(side="right", padx=10, pady=5)

    def create_input_section(self):
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
        self.picture_frame = tk.Canvas(self.root, bg="black", width=1160, height=340)
        self.picture_frame.place(x=20, y=510)
        tk.Label(self.root, text="Picture Display", bg=self.frame_bg, fg=self.text_color, font=("Consolas", 16)).place(x=20, y=490)

    def toggle_auto_processing(self):
        if not self.auto_processor.is_running:
            self.auto_button.config(text="Stop Auto Processing", bg="#8B0000")
            self.status_label.config(text="Status: Auto Mode")
            self.send_button.config(state="disabled")
            self.input_text.config(state="disabled")
            self.auto_processor.start()
        else:
            self.auto_button.config(text="Start Auto Processing", bg="#005f87")
            self.status_label.config(text="Status: Manual Mode")
            self.send_button.config(state="normal")
            self.input_text.config(state="normal")
            self.auto_processor.stop()

    def process_task(self, task):
        """Process a single task from the database"""
        try:
            # Take and upload screenshot
            screenshot_path = self.take_screenshot_with_grid()
            self.display_screenshot(screenshot_path)
            screenshot_url = upload_to_imgur(screenshot_path)

            # Get instructions from ChatGPT
            instructions = self.get_gpt_instructions(task['title'], screenshot_url)
            
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
            raise Exception(f"Task processing error: {str(e)}")

    def handle_manual_request(self):
        user_input = self.input_text.get("1.0", "end").strip()
        if not user_input:
            messagebox.showerror("Error", "Please enter a request.")
            return

        screenshot_path = self.take_screenshot_with_grid()
        self.display_screenshot(screenshot_path)

        try:
            screenshot_url = upload_to_imgur(screenshot_path)
            self.log_action(f"Screenshot uploaded: {screenshot_url}")
            
            instructions = self.get_gpt_instructions(user_input, screenshot_url)
            if instructions:
                self.process_instructions(instructions)
                
        except Exception as e:
            self.log_action(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to process request:\n{str(e)}")

    def get_gpt_instructions(self, user_input, screenshot_url):
        json_schema = """
        {
            "actions": [
                {"action": "mouse_move", "x": 100, "y": 200},
                {"action": "mouse_click"},
                {"action": "type_text", "text": "Hello, World!"}
            ]
        }
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a GUI automation assistant. Return ONLY JSON following this schema:\n{json_schema}\n"
                                 f"Reference the screenshot for coordinates. Max coordinates: x=4000, y=1000."
                    },
                    {
                        "role": "user",
                        "content": f"Instructions: {user_input}\nScreenshot: {screenshot_url}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.log_action(f"GPT Error: {str(e)}")
            return None

    def take_screenshot_with_grid(self):
        with mss.mss() as sct:
            raw_screenshot_path = "raw_screenshot.png"
            screenshot_with_grid_path = "screenshot_with_grid.png"
            sct.shot(mon=-1, output=raw_screenshot_path)
            apply_grid_overlay(raw_screenshot_path, screenshot_with_grid_path, step=500)
            return screenshot_with_grid_path

    def display_screenshot(self, screenshot_path):
        img = Image.open(screenshot_path)
        img_resized = img.resize((1120, 300))
        img_tk = ImageTk.PhotoImage(img_resized)
        self.picture_frame.delete("all")
        self.picture_frame.create_image(20, 20, anchor="nw", image=img_tk)
        self.picture_frame.image = img_tk

    def log_action(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

    def update_task_counter(self):
        self.task_counter.config(text=f"Tasks Processed: {len(self.auto_processor.tasks_processed)}")

    def process_instructions(self, instructions):
        if not isinstance(instructions, dict) or "actions" not in instructions:
            self.log_action("Invalid instructions format")
            return

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
                    pyautogui.press(key)
                    self.log_action(f"Pressed key: {key}")
            elif action_type == "type_text":
                text = action.get("text")
                if text:
                    pyautogui.typewrite(text)
                    self.log_action(f"Typed: {text}")
            else:
                self.log_action(f"Unknown action: {action_type}")

    def run(self):
        """Start the application with error handling"""
        try:
            self.root.mainloop()
        except Exception as e:
            self.log_action(f"Critical error: {str(e)}")
            messagebox.showerror("Critical Error", f"Application error:\n{str(e)}")
        finally:
            if self.auto_processor.is_running:
                self.auto_processor.stop()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ZeusTerminal(root)
        app.run()
    except Exception as e:
        print(f"Failed to start application: {str(e)}")
