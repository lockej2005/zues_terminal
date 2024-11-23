import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pyautogui
import mss
import json
from openai import OpenAI
from imgur_upload import upload_to_imgur  # Import the Imgur upload function
from overlay import apply_grid_overlay  # Import the grid overlay function

# Initialize OpenAI client
client = OpenAI(api_key="sk-proj-5MN52DibgpFgQfMKAJiVT3BlbkFJktsJW2uQhIuIGvE24viw")  # Replace with your OpenAI API key

class ZeusTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("Zeus Terminal")
        self.root.geometry("1200x800")
        self.root.configure(bg="black")  # Retro black background

        # Style settings
        self.text_color = "#00BFFF"  # Retro blue text
        self.frame_bg = "#101010"  # Dark gray frame background
        self.text_area_bg = "#202020"  # Subtle gray for text areas

        # Input Section (Left, Top)
        self.input_frame = tk.Frame(self.root, bg=self.frame_bg)
        self.input_frame.place(x=20, y=20, width=580, height=400)

        input_header = tk.Frame(self.input_frame, bg=self.frame_bg)
        input_header.pack(fill="x", padx=10, pady=5)

        tk.Label(input_header, text="JSON Input", bg=self.frame_bg, fg=self.text_color, font=("Consolas", 16)).pack(side="left")

        self.send_button = tk.Button(
            input_header, text="Send", command=self.handle_request, bg="#005f87", fg="white", font=("Consolas", 12), relief="ridge"
        )
        self.send_button.pack(side="right", padx=5)

        self.input_text = tk.Text(
            self.input_frame, wrap="word", height=20, width=60, bg=self.text_area_bg, fg=self.text_color, insertbackground=self.text_color, font=("Consolas", 12)
        )
        self.input_text.pack(padx=10, pady=10)

        # Log History Section (Right, Top)
        self.log_frame = tk.Frame(self.root, bg=self.frame_bg)
        self.log_frame.place(x=620, y=20, width=560, height=400)

        tk.Label(self.log_frame, text="Log History", bg=self.frame_bg, fg=self.text_color, font=("Consolas", 16)).pack(anchor="w", padx=10, pady=10)

        self.log_text = tk.Text(self.log_frame, wrap="word", height=20, width=55, bg=self.text_area_bg, fg=self.text_color, state="disabled", font=("Consolas", 12))
        self.log_text.pack(padx=10, pady=10)

        # Picture Display Section (Bottom, Full Width)
        self.picture_frame = tk.Canvas(self.root, bg="black", width=1160, height=340)
        self.picture_frame.place(x=20, y=440)

        tk.Label(self.root, text="Picture Display", bg=self.frame_bg, fg=self.text_color, font=("Consolas", 16)).place(x=20, y=420)

    def log_action(self, message):
        """Log actions to the log history."""
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")

    def take_screenshot_with_grid(self):
        """Capture a screenshot of the entire display and overlay a grid with labeled coordinates."""
        with mss.mss() as sct:
            raw_screenshot_path = "raw_screenshot.png"
            screenshot_with_grid_path = "screenshot_with_grid.png"

            # Capture a raw screenshot
            sct.shot(mon=-1, output=raw_screenshot_path)

            # Apply the grid overlay to the screenshot
            apply_grid_overlay(raw_screenshot_path, screenshot_with_grid_path, step=500)

            return screenshot_with_grid_path

    def display_screenshot(self, screenshot_path):
        """Display the screenshot in the picture section."""
        img = Image.open(screenshot_path)
        img_resized = img.resize((1120, 300))
        img_tk = ImageTk.PhotoImage(img_resized)

        self.picture_frame.delete("all")  # Clear previous canvas content
        self.picture_frame.create_image(20, 20, anchor="nw", image=img_tk)
        self.picture_frame.image = img_tk

    def handle_request(self):
        """Send user input and screenshot to ChatGPT, and process the response."""
        user_input = self.input_text.get("1.0", "end").strip()
        if not user_input:
            messagebox.showerror("Error", "Please enter a request.")
            return

        # Take a screenshot with the grid overlay
        screenshot_path = self.take_screenshot_with_grid()
        self.display_screenshot(screenshot_path)

        # Upload the screenshot to Imgur
        try:
            screenshot_url = upload_to_imgur(screenshot_path)
            self.log_action(f"Uploaded Screenshot to Imgur: {screenshot_url}")
        except Exception as e:
            self.log_action(f"Failed to upload screenshot: {e}")
            messagebox.showerror("Error", f"Failed to upload screenshot:\n{e}")
            return

        # Define JSON schema for strict ChatGPT response
        json_schema = """
        The response must be a JSON object named 'actions' containing multiple individual action objects. Each action object can have the following keys:
        - "action" (string): The action type. Can be one of ["mouse_click", "mouse_move", "press_key", "type_text"].
        - "x" (integer): The x-coordinate for "mouse_move" (optional, required if action is "mouse_move").
        - "y" (integer): The y-coordinate for "mouse_move" (optional, required if action is "mouse_move").
        - "key" (string): The key to press for "press_key" (optional, required if action is "press_key").
        - "text" (string): The text to type for "type_text" (optional, required if action is "type_text").
        Example:
        {
            "actions": [
                {"action": "mouse_move", "x": 100, "y": 200},
                {"action": "mouse_click"},
                {"action": "type_text", "text": "Hello, World!"}
            ]
        }
        """

        # Send the request to ChatGPT
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a helpful assistant that generates a strict JSON object for GUI automation. "
                                   f"Follow this schema:\n\n{json_schema}\n\n"
                                   f"Always return a JSON object named 'actions'. Do not include text outside the JSON."
                                   f"You will be given a screenshot of what the user sees. Use this as a direct reference as to what the user wants you to do and how you can achieve it. On top of the screenshot, there will be a coordinates reference that will help you estimate the coordinates of where you want to click."
                                   f"The max y axis is 1000 and the max x axis is 4000. There are two screens in the screenshot."
                    },
                    {
                        "role": "user",
                        "content": f"Instructions: {user_input}\n\nScreenshot URL: {screenshot_url}"
                    }
                ],
                response_format={ "type": "json_object" }
            )
            chat_gpt_response = response.choices[0].message.content

            if not chat_gpt_response:
                raise ValueError("ChatGPT returned an empty response.")

            # Strip backticks and parse JSON
            chat_gpt_response = chat_gpt_response.strip("").strip()
            self.log_action(f"ChatGPT Response:\n{chat_gpt_response}")

            # Process the JSON response
            self.process_instructions(json.loads(chat_gpt_response))
        except json.JSONDecodeError as e:
            self.log_action(f"Error: ChatGPT response was not valid JSON.\nDetails: {e}")
            messagebox.showerror("Error", "ChatGPT response was not valid JSON.")
        except Exception as e:
            self.log_action(f"Error: {e}")
            messagebox.showerror("Error", f"Failed to process the request:\n{e}")

    def process_instructions(self, instructions):
        """Process JSON instructions."""
        if not isinstance(instructions, dict) or "actions" not in instructions:
            self.log_action("Instructions should be a JSON object with an 'actions' key.")
            return

        actions = instructions["actions"]
        for action in actions:
            action_type = action.get("action")
            if action_type == "mouse_click":
                pyautogui.click()
                self.log_action("Mouse clicked.")
            elif action_type == "mouse_move":
                x = action.get("x")
                y = action.get("y")
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y)
                    self.log_action(f"Mouse moved to ({x}, {y}).")
                else:
                    self.log_action("Invalid mouse_move action: x and y are required.")
            elif action_type == "press_key":
                key = action.get("key")
                if key:
                    pyautogui.press(key)
                    self.log_action(f"Key '{key}' pressed.")
                else:
                    self.log_action("Invalid press_key action: key is required.")
            elif action_type == "type_text":
                text = action.get("text")
                if text:
                    pyautogui.typewrite(text)
                    self.log_action(f"Text '{text}' typed.")
                else:
                    self.log_action("Invalid type_text action: text is required.")
            else:
                self.log_action(f"Unknown action: {action_type}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ZeusTerminal(root)
    root.mainloop()