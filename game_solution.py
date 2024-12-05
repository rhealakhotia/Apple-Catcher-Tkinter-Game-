import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import random
import json
import time
import os
from PIL import Image, ImageTk, ImageFont, ImageDraw


class Game(tk.Frame):
    """Defines class Game and initialises variables and flags"""

    def __init__(
        self, master=None, player_name="Player"
    ):  # Automatically called when an instance of Game class is created
        tk.Frame.__init__(self, master)
        self.grid(
            sticky="nsew"
        )  # Makes grid expand in all directions to fit the window
        self.player_name = player_name
        self.score_value = 0
        self.lives_value = 5
        self.g_apple_counter = 0
        self.r_apple_counter = 0
        self.power_up_counter = 0
        # State flags
        self.game_over_flag = False
        self.boss_key_active = False
        self.invincibility = False
        self.is_paused = False
        self.game_started = False
        self.large_basket = False
        self.cheat_invincibility = False
        self.level = 1  # Sets initial game level
        self.createWidgets()
        self.start_game()
        self.master.bind(
            "<KeyPress>", self.key_pressed
        )  # Binds key press events to the method 'key_pressed'
        self.cheat_code_buffer = ""  # Buffer to store cheat code input

        # Create saves directory
        if not os.path.exists("saves"):
            os.makedirs("saves")

    def show_message(self, text):
        """Function to display message"""
        message = self.canvas.create_text(
            500, 300, text=text, font=("Arial", 24, "bold"), fill="white"
        )
        # Displays temporary message for 2s
        self.master.after(2000, lambda: self.canvas.delete(message))

    def save_game(self):
        """Allows user to save their game state in a JSON file"""
        game_state = {
            "player_name": self.player_name,
            "score": self.score_value,
            "lives": self.lives_value,
            "basket_position": self.canvas.coords(
                self.basket_image_id
            ),  # Saves basket coords
            "invincibility": self.invincibility,
            "large_basket": self.large_basket,
            "timestamp": time.time(),
        }  # To load recent save
        save_path = f"saves/{self.player_name}_save.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(game_state, f)  # Saves game

        # Prints message to confirm saved game
        self.show_message("Game Saved!")

    def load_game(self):
        """Allows user to load their saved game state"""
        try:
            with open(
                f"saves/{self.player_name}_save.json", "r", encoding="utf-8"
            ) as f:
                saved_state = json.load(f)  # Load the saved game state

            # Restore previous game state
            self.score_value = saved_state["score"]
            self.lives_value = saved_state["lives"]
            self.score_label.config(text=f"Score: {self.score_value}")
            self.lives_label.config(text=f"Lives: {self.lives_value}")

            # Restore previous basket position
            self.canvas.coords(
                self.basket_image_id,
                saved_state["basket_position"][0],
                saved_state["basket_position"][1],
            )

            # Restore power-ups
            if saved_state["invincibility"]:
                self.activate_invincibility()
            if saved_state["large_basket"]:
                self.toggle_basket_size()

            self.show_message(
                "Game Loaded!"
            )  # Prints message to confirm loaded saved game

        except FileNotFoundError:
            self.show_message(
                "No saved game found!"
            )  # Prints message if user tries to load unsaved game

    def show_game_help(self):
        """Displays game guide & instructions"""
        if not self.is_paused:
            self.toggle_pause()  # Pauses game when help button clicked

        help_window = tk.Toplevel(self.master)
        help_window.title("Game Guide")
        help_window.geometry("600x800")

        help_frame = tk.Frame(help_window)  # Uses frame to organise widgets
        help_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        title_label = tk.Label(
            help_frame,
            text="🍎 Apple Catcher Game Instructions",
            font=("Arial", 16, "bold"),
        )
        title_label.pack(pady=(0, 20))

        # Content for the game guide & instructions
        help_sections = [
            {
                "title": "🎯 Objective",
                "content": [
                    "Catch falling apples in your basket",
                    "Avoid missing red apples",
                    "Dodge rotten apples",
                    "Collect golden apples for bonus points",
                ],
            },
            {
                "title": "🕹️ Controls",
                "content": [
                    "Left/Right Arrow Keys: Move basket",
                    "P Key: Pause/Resume game",
                    "B Key: Boss key (quick hide)",
                    "S Key: Save current game progress",
                    "W Key: Load previously saved game",
                ],
            },
            {
                "title": "🍏 Apple Types",
                "content": [
                    "Red Apple: +1 point",
                    "Golden Apple: +10 points, gain a life",
                    "Rotten Apple: -1 point, lose a life",
                ],
            },
            {
                "title": "⚡ Power-Ups",
                "content": [
                    "Triangle: Collect for temporary invincibility",
                ],
            },
            {
                "title": "⭐ Cheat Codes",
                "content": [
                    "'mega': Toggle basket size",
                    "'god': Temporary invincibility",
                    "'life': Add extra lives",
                    "'cat': Gain 9 lives",
                ],
            },
        ]

        for section in help_sections:  # Create sections in game guide
            section_frame = tk.Frame(help_frame)
            section_frame.pack(fill=tk.X, pady=10, anchor="w")
            title_label = tk.Label(
                section_frame, text=section["title"], font=(
                    "Arial", 12, "bold"))
            title_label.pack(anchor="w")

            for i in section["content"]:
                content_label = tk.Label(
                    section_frame,
                    text=f"• {i}",
                    font=("Arial", 12),
                    anchor="w",
                    justify=tk.LEFT,
                )
                content_label.pack(anchor="w")

        close_button = tk.Button(
            help_frame, text="Got it!", command=help_window.destroy
        )
        close_button.pack(pady=20)

    def key_pressed(self, event):
        """Used to handle key press events"""
        if event.keysym == self.left_key:
            self.move_left()
        elif event.keysym == self.right_key:
            self.move_right()
        elif event.keysym == "p":  # 'P' key to pause/resume
            self.toggle_pause()
        elif event.keysym == "b":  # 'B' key for boss key
            self.toggle_boss_key()
        elif event.keysym == "s":  # 'S' key for save game
            self.save_game()
        elif event.keysym == "w":  # 'W' key for load game
            self.load_game()
        self.cheat_code_buffer += event.char  # Add key to buffer
        self.cheat_code_buffer = self.cheat_code_buffer[
            -10:
        ]  # Ensures buffer contains recent input
        # Check for cheat codes in buffer
        if "mega" in self.cheat_code_buffer.lower():
            self.toggle_basket_size()
            self.cheat_code_buffer = ""  # Clears buffer after cheat code used
        elif "god" in self.cheat_code_buffer.lower():
            self.toggle_cheat_invincibility()
            self.cheat_code_buffer = ""
        elif "life" in self.cheat_code_buffer.lower():
            self.add_extra_lives()
            self.cheat_code_buffer = ""
        elif "cat" in self.cheat_code_buffer.lower():
            self.cat_cheat_code()
            self.cheat_code_buffer = ""

    def toggle_basket_size(self):
        """Allows user to toggle between normal and large basket size"""
        self.large_basket = not self.large_basket
        if self.large_basket:
            # Resizes basket to larger size
            self.basket_image = self.basket_image.resize(
                (200, 120), Image.LANCZOS)
            self.basket_image_tk = ImageTk.PhotoImage(self.basket_image)
        else:
            # Resizes basket to original size
            self.basket_image = self.basket_image.resize(
                (150, 100), Image.LANCZOS)
            self.basket_image_tk = ImageTk.PhotoImage(self.basket_image)

        # Update basket size on canvas
        current_coords = self.canvas.coords(self.basket_image_id)
        self.canvas.delete(self.basket_image_id)
        self.basket_image_id = self.canvas.create_image(
            current_coords[0],
            current_coords[1],
            anchor="nw",
            image=self.basket_image_tk,
        )

        # Prints message to confirm toggled basket size
        self.show_cheat_message("Basket size toggled!")

    def cat_cheat_code(self):
        """Allows user to add +9 lives when 'cat' cheat code is used"""
        self.lives_value += 9
        self.lives_label.config(text=f"Lives: {self.lives_value}")
        self.show_cheat_message(
            "🐱 Meow! You now have +9 lives like a cat!"
        )  # Prints message to confirm activation of 'cat' cheat code

    def toggle_cheat_invincibility(self):
        """Allows user to add a god (invincibility) mode"""
        if not self.cheat_invincibility:
            self.cheat_invincibility = True
            self.invincibility = True

            # Prints message to confirm god mode active
            self.cheat_invincibility_indicator = self.canvas.create_text(
                500,
                50,
                text="🛡️ GOD MODE ACTIVE 🛡️",
                font=("Press Start 2P", 24, "bold"),
                fill="purple",
                tags="cheat_god_mode",
            )

            # Countdown timer for god mode for 10 seconds
            self.god_mode_timer = 10
            self.god_mode_countdown = self.canvas.create_text(
                500,
                80,
                text=f"Time Remaining: {self.god_mode_timer} s",
                font=("Press Start 2P", 16),
                fill="purple",
                tags="cheat_god_mode",
            )

            self.show_cheat_message("God Mode: 10 seconds!")

            self.update_god_cheat_countdown()  # Begin 10s countdown
        else:
            self.end_cheat_invincibility()

    def update_god_cheat_countdown(self):
        """Updates countdown timer by -1s"""
        if self.god_mode_timer > 0:
            self.god_mode_timer -= 1
            self.canvas.itemconfig(
                self.god_mode_countdown,
                text=f"Time Remaining: {self.god_mode_timer}",
            )  # Update display countdown timer
            self.master.after(
                1000, self.update_god_cheat_countdown
            )  # Call the method again in 1s
        else:
            self.end_cheat_invincibility()  # End it when countdown timer ends

    def end_cheat_invincibility(self):
        """Ends 'god' cheat code, ending invincibility"""
        self.cheat_invincibility = False
        self.invincibility = False

        # Remove message indicating god mode and countdown
        self.canvas.delete("cheat_god_mode")

        self.show_cheat_message(
            "God Mode Expired!"
        )  # Print message to confirm god mode expired

    def add_extra_lives(self):
        """Allows user to add +3 lives when 'life' cheat code is used"""
        self.lives_value += 3
        self.lives_label.config(text=f"Lives: {self.lives_value}")
        self.show_cheat_message(
            "+3 lives added!"
        )  # Prints message to confirm activation of 'life' cheat code

    def show_cheat_message(self, message):
        """Displays a temporary message to indicate cheat activation"""
        cheat_text = self.canvas.create_text(
            500,
            100,
            text=message,
            font=("Arial", 20, "bold"),
            fill="green",
            tags="cheat_message",
        )
        self.master.after(
            2000, lambda: self.canvas.delete(cheat_text)
        )  # Remove message after 2 seconds

    def hide_help_button(self):
        """Hides the help button if it exists"""
        if hasattr(self, "help_button") and self.help_button.winfo_exists():
            self.help_button.place_forget()

    def show_help_button(self):
        """Shows the help button if it exists"""
        if hasattr(self, "help_button") and self.help_button.winfo_exists():
            self.help_button.place(x=900, y=10)

    def hide_exit_button(self):
        """Hides the exit button if it exists"""
        if (
            hasattr(self, "exit_button") and
            self.exit_button and
            self.exit_button.winfo_exists()
        ):
            self.exit_button.place_forget()

    def show_exit_button(self):
        """Shows the exit button if it exists"""
        if (
            hasattr(self, "exit_button") and
            self.exit_button and
            self.exit_button.winfo_exists()
        ):
            self.exit_button.place(x=750, y=20)

    def toggle_boss_key(self):
        """Handles boss key functionality with proper game state management"""
        if self.boss_key_active:
            # Deactivate boss screen
            self.canvas.delete("boss_screen")
            self.boss_key_active = False
            self.status_frame.grid(row=0, column=0, columnspan=2, sticky="nw")

            # Restore previous pause state
            self.is_paused = self.previous_pause_state

            # Shows the buttons
            self.show_help_button()
            self.show_exit_button()

            # If game wasn't paused before boss key, resume game with delay
            if not self.is_paused:
                # Clear any existing scheduled falls
                if hasattr(self, "periodic_after_id"):
                    self.master.after_cancel(self.periodic_after_id)
                # Resume with delay to prevent apple buildup
                self.master.after(1000, self.periodic_falls)
        else:
            # Activate boss screen
            self.boss_key_active = True

            # Store current pause state
            self.previous_pause_state = self.is_paused
            self.is_paused = True

            # Cancel any scheduled falls
            if hasattr(self, "periodic_after_id"):
                self.master.after_cancel(self.periodic_after_id)

            # Clear any pause text that might be showing
            if hasattr(self, "pause_text"):
                self.canvas.delete(self.pause_text)

            # Hide game elements
            self.status_frame.grid_remove()

            # Display boss screen
            self.canvas.create_image(
                0, 0, anchor="nw", image=self.boss_image_tk, tags="boss_screen"
            )
            self.canvas.tag_raise("boss_screen")

            # Hide buttons
            self.hide_help_button()
            self.hide_exit_button()

    def toggle_pause(self):
        """Handles pause functionality with proper game state management"""
        if self.boss_key_active:
            return  # Ignore pause toggle if boss key is active

        self.is_paused = not self.is_paused

        if self.is_paused:
            # Cancel any scheduled falls
            if hasattr(self, "periodic_after_id"):
                self.master.after_cancel(self.periodic_after_id)

            # Display pause text
            self.pause_text = self.canvas.create_text(
                500,
                300,
                text="GAME PAUSED\nPress 'P' to continue",
                font=("Arial", 24, "bold"),
                fill="red",
                justify="center",
                tags="pause_text",
            )
        else:
            # Remove pause text
            self.canvas.delete("pause_text")

            # Clear any existing scheduled falls
            if hasattr(self, "periodic_after_id"):
                self.master.after_cancel(self.periodic_after_id)

            # Resume game with delay to prevent apple buildup
            self.master.after(1000, self.periodic_falls)

    def cleanup_game_state(self):
        """
        Helper method to clean up game state when pausing or using boss key
        """
        # Cancel any scheduled falls
        if hasattr(self, "periodic_after_id"):
            self.master.after_cancel(self.periodic_after_id)
            self.periodic_after_id = None

        self.canvas.delete("pause_text")

    def load_images(self):
        """Load and resize all game images using LANCZOS and PIL"""
        self.bg_image = Image.open("background.png")
        self.bg_image = self.bg_image.resize((1000, 600), Image.LANCZOS)
        self.bg_image_tk = ImageTk.PhotoImage(self.bg_image)

        self.apple_image = Image.open("apple.png")
        self.apple_image = self.apple_image.resize((35, 35), Image.LANCZOS)
        self.apple_image_tk = ImageTk.PhotoImage(self.apple_image)

        self.g_apple_image = Image.open("golden_apple.png")
        self.g_apple_image = self.g_apple_image.resize((40, 40), Image.LANCZOS)
        self.g_apple_image_tk = ImageTk.PhotoImage(self.g_apple_image)

        self.r_apple_image = Image.open("rotten_apple.png")
        self.r_apple_image = self.r_apple_image.resize((40, 40), Image.LANCZOS)
        self.r_apple_image_tk = ImageTk.PhotoImage(self.r_apple_image)

        self.basket_image = Image.open("basket.png")
        self.basket_image = self.basket_image.resize((150, 100), Image.LANCZOS)
        self.basket_image_tk = ImageTk.PhotoImage(self.basket_image)

        self.boss_image = Image.open("boss_screen.png")
        self.boss_image = self.boss_image.resize((1000, 600), Image.LANCZOS)
        self.boss_image_tk = ImageTk.PhotoImage(self.boss_image)

        self.help_icon = Image.open("question_mark.png")
        self.help_icon = self.help_icon.resize((70, 70), Image.LANCZOS)
        self.help_icon_tk = ImageTk.PhotoImage(self.help_icon)

    def createWidgets(self):
        """To create widgets and set up game screen"""
        self.load_images()
        self.canvas = tk.Canvas(
            self, width=1000, height=600
        )  # Creates game canvas with specified dimensions
        self.canvas.grid(row=0, column=0)
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image_tk)

        self.status_frame = tk.Frame(self, bg="black")
        self.status_frame.grid(row=0, column=0, sticky="nw")

        self.status_frame.grid_columnconfigure(
            0, weight=1
        )  # Left column for score label
        self.status_frame.grid_columnconfigure(
            2, weight=1
        )  # Middle column for lives label
        self.status_frame.grid_columnconfigure(
            4, weight=2
        )  # Right column for help button

        # Adds Score label
        self.score_label = tk.Label(
            self.status_frame,
            text=f"Score: {self.score_value}",
            font=("Arial", 18),
            fg="#add8e6",
            bg="black",
            relief="solid",
            bd=2,
            padx=10,
            pady=5,
        )
        self.score_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        # Adds Lives Label
        self.lives_label = tk.Label(
            self.status_frame,
            text=f"Lives: {self.lives_value}",
            font=("Arial", 18),
            fg="#add8e6",
            bg="black",
            relief="solid",
            bd=2,
            padx=10,
            pady=5,
        )
        self.lives_label.grid(row=0, column=2, sticky="e", padx=20, pady=15)

    def enhance_visuals(self, effect_type, x, y):
        """Add visual effects for different game events"""
        text = ""
        if effect_type == "golden_catch":
            text = "+10!"  # Display +10 for golden apple catch
        elif effect_type == "apple_catch":
            text = "+1"  # Display +1 for normal apple catch
        elif effect_type == "rotten_catch":
            text = "-1"  # Display -1 for rotten apple catch
        # Create text at specific coordinates
        txt_id = self.canvas.create_text(
            x,
            y,
            text=text,
            font=("Arial", 20),
            fill="yellow",
            anchor="center",
        )

        # Animate the text and fade out
        def animate_text(i=0):
            # Sets number of animation frames
            if i < 10:
                opacity = int(255 * (1 - i / 10))  # Fade out based on i
                hex_opacity = format(opacity, '02x')
                self.canvas.itemconfig(
                    txt_id, fill=f"#{hex_opacity}{hex_opacity}{hex_opacity}"
                )
                self.master.after(
                    50, lambda: animate_text(i + 1)
                )  # Call next frame after 50ms
            else:
                self.canvas.delete(txt_id)

        animate_text()

    def start_game(self):
        """Starts the game window main menu"""
        self.master.withdraw()
        # Close any existing game over window if it exists
        if hasattr(self, "game_over_window"):
            self.game_over_window.destroy()

        # Ensure main window is withdrawn
        self.master.withdraw()

        # Create start game window
        start_game_window = tk.Toplevel(self.master)
        start_game_window.title("Apple Catcher")
        start_game_window.geometry("1000x600")

        self.start_bg = Image.open("start_background.png").resize(
            (1000, 600), Image.LANCZOS
        )
        self.start_bg_tk = ImageTk.PhotoImage(self.start_bg)

        draw = ImageDraw.Draw(self.start_bg)
        font_path = "./PressStart2P-Regular.ttf"
        font_size = 30
        font = ImageFont.truetype(font_path, font_size)

        text = "Welcome to the\nApple Catcher!"
        text_position = (330, 50)
        draw.text(text_position, text, font=font, fill="black")
        self.start_bg_tk = ImageTk.PhotoImage(self.start_bg)

        canvas = tk.Canvas(start_game_window, width=1000, height=600)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=self.start_bg_tk)

        # Create canvas for the start screen
        canvas = tk.Canvas(start_game_window, width=1000, height=600)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=self.start_bg_tk)

        # Add text entry for player's name and movement keys
        tk.Label(
            start_game_window,
            text="Enter Your Name:",
            font=(
                "Arial",
                14)).place(
            x=350,
            y=250)
        self.name_entry = tk.Entry(start_game_window, font=("Arial", 14))
        self.name_entry.place(x=500, y=250, width=200, height=30)

        tk.Label(
            start_game_window,
            text="Movement key for Left Arrow:",
            font=("Arial", 14),
        ).place(x=350, y=300)
        self.left_arrow_entry = tk.Entry(start_game_window, font=("Arial", 14))
        self.left_arrow_entry.place(x=600, y=300, width=100, height=30)

        tk.Label(
            start_game_window,
            text="Movement key for Right Arrow:",
            font=("Arial", 14),
        ).place(x=350, y=350)
        self.right_arrow_entry = tk.Entry(
            start_game_window, font=("Arial", 14))
        self.right_arrow_entry.place(x=600, y=350, width=100, height=30)

        # Button to start game
        tk.Button(
            start_game_window,
            text="Start Game",
            font=("Arial", 14),
            command=lambda: self.initialize_main_game(start_game_window),
        ).place(x=350, y=400)

        # Button to view leaderboard
        tk.Button(
            start_game_window,
            text="Leaderboard",
            font=("Arial", 14),
            command=lambda: self.show_leaderboard(),
        ).place(x=470, y=400)

        # Button to exit game
        tk.Button(
            start_game_window,
            text="Exit Game",
            font=("Arial", 14),
            command=self.master.quit,
        ).place(x=600, y=400)

        # Button to view game instructions
        self.help_button = tk.Button(
            start_game_window,
            image=self.help_icon_tk,
            compound=tk.CENTER,
            command=self.show_game_help,
            borderwidth=0,
            highlightthickness=0,
        )

        self.show_help_button()

    def initialize_main_game(self, start_game_window):
        """Initializes main game screen"""
        # Check if player name is empty or contains only whitespace
        player_name = self.name_entry.get().strip()

        if not player_name:
            # Show an error message if name is not entered
            messagebox.showerror("Invalid Name", "Please enter a player name.")
            return  # Prevent proceeding to the game

        # Set player name
        self.player_name = player_name

        self.left_key = (
            self.left_arrow_entry.get().strip() or "Left"
        )  # Default is left arrow key
        self.right_key = (
            self.right_arrow_entry.get().strip() or "Right"
        )  # Default is right arrow key

        # Create basket and bind keys when game starts
        self.create_basket()
        self.master.bind("<KeyPress>", self.key_pressed)

        self.help_button = tk.Button(
            self.master,
            image=self.help_icon_tk,
            command=self.show_game_help,
            borderwidth=0,
            highlightthickness=0,
        )
        self.show_help_button()

        self.exit_button = tk.Button(
            self.master, text="Exit Game", command=self.master.quit
        )
        self.exit_button.place(x=750, y=20)

        self.show_exit_button()

        # Start the game loop
        self.game_started = True
        self.periodic_falls()

        start_game_window.destroy()
        self.master.deiconify()

    def start_leaderboard(self, score_value):
        """Reads leaderboard data and checks if player already exists"""
        leaderboard = self.read_leaderboard()

        # Check if player name exists
        existing_entry = next(
            (e for e in leaderboard if e["Name"] == self.player_name),
            None,
        )

        if existing_entry:
            # Updates high score if player exists
            if score_value > existing_entry["Score"]:
                existing_entry["Score"] = score_value
        else:
            # If player doesn't exist, add new entry
            new_entry = {
                "Rank": len(leaderboard) + 1,
                "Name": self.player_name,
                "Score": score_value,
            }
            leaderboard.append(new_entry)

        # Sort leaderboard according to ranks and update ranks
        leaderboard.sort(key=lambda x: x["Score"], reverse=True)
        for index, e in enumerate(leaderboard):
            e["Rank"] = index + 1

        self.write_leaderboard(leaderboard)

    def update_leaderboard(self, save_leaderboard):
        """Updates leaderboard and called during game_over"""
        leaderboard = self.read_leaderboard()

        # Check if the player already exists in the leaderboard
        player_found = False
        for entry_data in leaderboard:
            if entry_data["Name"] == self.player_name:
                # If the player's score is higher, update the score
                if self.score_value > entry_data["Score"]:
                    entry_data["Score"] = self.score_value
                player_found = True
                break

        # If the player is not found, add them as a new entry
        if not player_found:
            new_data = {
                "Rank": len(leaderboard) + 1,
                "Name": self.player_name,
                "Score": self.score_value,
            }
            leaderboard.append(new_data)

        # Sort the leaderboard by score in descending order and update ranks
        leaderboard.sort(key=lambda x: x["Score"], reverse=True)
        for index, entry_data in enumerate(leaderboard):
            entry_data["Rank"] = index + 1

        # Save the updated leaderboard
        save_leaderboard(leaderboard)

    def write_leaderboard(self, leaderboard):
        """Write the leaderboard data to a JSON file"""
        with open("leaderboard.json", "w") as file:
            json.dump(leaderboard, file)

    def read_leaderboard(self):
        """Read leaderboard data"""
        try:
            with open("leaderboard.json", "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []  # Return empty list

    def show_leaderboard(self):
        """Sets up leaderboard design"""
        leaderboard_window = tk.Toplevel()
        leaderboard_window.title("Leaderboard")
        leaderboard_window.geometry("600x400")

        # Style for the table
        style = ttk.Style()
        style.configure(
            "Leaderboard.Treeview", font=(
                "Arial", 10), rowheight=30)
        style.configure("Leaderboard.Treeview.Heading", font=("Arial", 12))

        # Create table
        tree = ttk.Treeview(
            leaderboard_window,
            style="Leaderboard.Treeview",
            columns=("Rank", "Name", "Score"),
            show="headings",
        )

        # Columns
        tree.heading("Rank", text="Rank")
        tree.heading("Name", text="Name")
        tree.heading("Score", text="Score")

        tree.column("Rank", width=100, anchor="center")
        tree.column("Name", width=300, anchor="center")
        tree.column("Score", width=200, anchor="center")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            leaderboard_window, orient="vertical", command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)

        # Packing the widgets
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Load and display data
        leaderboard = self.read_leaderboard()
        for entry in leaderboard:
            tree.insert(
                "",
                "end",
                values=(
                    entry["Rank"],
                    entry["Name"],
                    entry["Score"]))

    def start_main_game(self, start_game_window):
        """Loads game screen"""
        # Retrieves the player's name and key bindings for control
        self.player_name = self.name_entry.get()
        self.left_key = (
            self.left_arrow_entry.get().strip() or "Left"
        )  # Default to Left arrow key
        self.right_key = (
            self.right_arrow_entry.get().strip() or "Right"
        )  # Default to Right arrow key

        start_game_window.destroy()
        self.master.deiconify()

    def create_f1(self):
        """Creates a regular apple that falls from the top of the screen"""
        if self.is_paused or self.game_over_flag:
            return

        f1_range = random.randint(0, 970)
        f1_image = self.canvas.create_image(
            f1_range, 0, anchor="nw", image=self.apple_image_tk
        )

        # Add tag to track this apple's after IDs
        self.canvas.addtag_withtag(f"apple_{f1_image}", f1_image)

        def move_f1():  # Handles movement and collision detection
            try:
                # Check if canvas and image still exist
                if (
                    not self.canvas.winfo_exists() or
                    not self.canvas.type(f1_image)
                ):
                    return

                # Handle paused or game over state
                if self.is_paused or self.game_over_flag:
                    move_id = self.master.after(50, move_f1)
                    self.canvas.addtag_withtag(f"move_id_{move_id}", f1_image)
                    return

                # Calculate movement speed
                base_speed = 3 + (self.level * 0.5)
                speed_variation = random.uniform(0.8, 1.2)
                move_speed = base_speed * speed_variation

                # Move the apple
                self.canvas.move(f1_image, 0, move_speed)
                coords = self.canvas.coords(f1_image)

                if not coords:
                    self.cleanup_apple(f1_image)
                    return

                # Check if apple is still on screen
                if coords[1] < 600:
                    move_id = self.master.after(50, move_f1)
                    self.canvas.addtag_withtag(f"move_id_{move_id}", f1_image)
                else:
                    # Handle apple reaching bottom
                    if not self.check_collision(
                            f1_image, self.basket_image_id):
                        self.update_lives()
                    self.cleanup_apple(f1_image)
                    return

                # Check for collision with basket
                if coords[1] >= 525 and coords[1] <= 570:
                    if self.check_collision(f1_image, self.basket_image_id):
                        self.update_score()
                        self.cleanup_apple(f1_image)
                        return

            except tk.TclError:
                self.cleanup_apple(f1_image)
                return

        move_f1()

    def cleanup_apple(self, apple_image):
        """Removes an apple and its associated after calls"""
        try:
            tags = self.canvas.gettags(
                apple_image
            )  # Get the tags associated with this apple

            # Cancel any pending after calls
            for tag in tags:
                if tag.startswith("move_id_"):
                    try:
                        move_id = int(tag.split("_")[-1])
                        self.master.after_cancel(move_id)
                    except (ValueError, tk.TclError):
                        pass

            # Delete the apple image
            if self.canvas.type(apple_image):
                self.canvas.delete(apple_image)
        except tk.TclError:
            pass

    def create_g_f1(self):
        """Creates a golden apple that falls from the top of the screen"""
        # Check if the game is paused, exit if true
        if self.is_paused:
            return

        # Create the golden apple
        if self.g_apple_counter % 4 != 0:
            return

        # Random horizontal position
        g_f1_range = random.randint(0, 970)
        # Create golden apple on canvas
        g_f1_image = self.canvas.create_image(
            g_f1_range, 0, anchor="nw", image=self.g_apple_image_tk
        )
        move_id = None

        def move_g_f1():
            nonlocal move_id

            try:
                # Checks if the canvas or image exits
                if (
                    not self.canvas.winfo_exists() or not
                    self.canvas.type(g_f1_image)
                ):
                    return

                # Pause handling
                if self.is_paused:
                    move_id = self.master.after(100, move_g_f1)
                    return

                # Set the speed and movement variation for the golden apple
                base_horizontal = 1.5
                base_vertical = 7
                horizontal_variation = random.uniform(0.8, 1.2)
                vertical_variation = random.uniform(0.8, 1.2)
                horizontal_speed = base_horizontal * horizontal_variation
                vertical_speed = base_vertical * vertical_variation

                # Move the apple on the canvas
                self.canvas.move(g_f1_image, horizontal_speed, vertical_speed)
                coords = self.canvas.coords(g_f1_image)

                # If the apple's coords are invalid, exit
                if not coords:
                    return

                if coords[1] < 600:
                    move_id = self.master.after(100, move_g_f1)
                else:
                    # Delete the apple if it falls below the screen
                    if self.canvas.type(g_f1_image):
                        self.canvas.delete(g_f1_image)
                    return

                # Check if the apple is within the basket area for collection
                if coords[1] >= 525 and coords[1] <= 570:
                    if self.check_collision(g_f1_image, self.basket_image_id):
                        # Update score when golden apple is caught
                        self.update_score(golden_apple=True)
                        if move_id:
                            self.master.after_cancel(move_id)
                        if self.canvas.type(g_f1_image):
                            self.canvas.delete(g_f1_image)
                        return

            except tk.TclError:
                return

        move_g_f1()

    def create_r_f1(self):
        """Creates a rotten apple that falls from the top of the screen"""
        # Check if the game is paused, exit if true
        if self.is_paused:
            return

        # Random horizontal position for the rotten apple
        r_f1_range = random.randint(0, 970)
        # Create the rotten apple image on the canvas
        r_f1_image = self.canvas.create_image(
            r_f1_range, 0, anchor="nw", image=self.r_apple_image_tk
        )
        move_id = None

        def move_r_f1():
            nonlocal move_id

            try:
                # Check if the canvas doesn't exist
                if (
                    not self.canvas.winfo_exists() or not
                    self.canvas.type(r_f1_image)
                ):
                    return

                # Pause handling
                if self.is_paused:
                    move_id = self.master.after(50, move_r_f1)
                    return

                # Set the speed and movement variation for the rotten apple
                base_speed = 8
                score_penalty = min(2, self.score_value // 20)
                speed_variation = random.uniform(0.7, 1.3)
                move_speed = (base_speed + score_penalty) * speed_variation
                wobble = (
                    random.uniform(-0.5, 0.5) if random.random() < 0.3 else 0
                )  # Wobble effect for randomness

                # Move rotten apple on the canvas
                self.canvas.move(r_f1_image, wobble, move_speed)
                coords = self.canvas.coords(r_f1_image)

                # If apple's coordinates are invalid, exit
                if not coords:
                    return

                # Continue moving rotten apple if it's within the screen
                if coords[1] < 600:
                    move_id = self.master.after(50, move_r_f1)
                else:
                    # Delete the rotten apple if it falls below the screen
                    if self.canvas.type(r_f1_image):
                        self.canvas.delete(r_f1_image)
                    return

                # Check if rotten apple is within basket area for collision
                if coords[1] >= 525 and coords[1] <= 570:
                    if self.check_collision(r_f1_image, self.basket_image_id):
                        # Update score and lives when rotten apple is caught
                        if not self.invincibility:
                            self.update_score(rotten_apple=True)
                            self.update_lives(rotten_apple=True)
                        if move_id:
                            self.master.after_cancel(move_id)
                        if self.canvas.type(r_f1_image):
                            self.canvas.delete(r_f1_image)
                        return

            except tk.TclError:
                return

        move_r_f1()

    def create_power_up(self):
        """Creates a power up that falls from the top of the screen"""
        # Check if the game is paused, exit if true
        if self.is_paused:
            return

        # Random horizontal position for the power-up
        power_up_range = random.randint(20, 950)
        size = 10
        # Define the shape of the power-up as a triangle
        points = [
            power_up_range,
            0,
            power_up_range + size,
            size * 2,
            power_up_range - size,
            size * 2,
        ]

        # Create the power-up shape on the canvas
        power_up_shape = self.canvas.create_polygon(
            points, outline="gold", fill="yellow", width=2
        )
        move_id = None

        def move_power_up():
            nonlocal move_id

            try:
                # Check if the canvas doesn't exist
                if not self.canvas.winfo_exists() or not self.canvas.type(
                    power_up_shape
                ):
                    return

                # Pause handling
                if self.is_paused:
                    move_id = self.master.after(50, move_power_up)
                    return

                # Set the speed and movement variation for the power-up
                base_speed = 8
                score_boost = min(4, self.score_value // 15)
                speed_variation = random.uniform(0.9, 1.1)
                move_speed = (base_speed + score_boost) * speed_variation

                # Move the power-up on the canvas
                self.canvas.move(power_up_shape, 0, move_speed)
                coords = self.canvas.coords(power_up_shape)

                if not coords:
                    return

                # Continue moving the power-up if it's within the screen
                center_y = (
                    coords[1] + coords[3]
                ) / 2  # Get center y-coordinate of the power-up
                if center_y < 600:
                    move_id = self.master.after(50, move_power_up)
                else:
                    # Delete the power-up if it falls below the screen
                    if self.canvas.type(power_up_shape):
                        self.canvas.delete(power_up_shape)
                    return

                # Check if power-up is within basket area for collection
                if coords[1] >= 525 and coords[1] <= 570:
                    basket_coords = self.canvas.coords(self.basket_image_id)
                    power_up_center_x = (
                        coords[0] + coords[2]
                    ) / 2  # Get center x-coordinate of the power-up

                    # Activate the power-up if it's within the basket area
                    if (
                        basket_coords and
                        power_up_center_x >= basket_coords[0] and
                        power_up_center_x <= basket_coords[0] + 100
                    ):
                        self.activate_invincibility()
                        if move_id:
                            self.master.after_cancel(move_id)
                        if self.canvas.type(power_up_shape):
                            self.canvas.delete(power_up_shape)
                        return
            except tk.TclError:
                return

        move_power_up()

    def activate_invincibility(self):
        """Activates invincibility power-up"""
        self.invincibility = True
        # Making the invincibility indicator noticeable
        self.power_up_indicator = self.canvas.create_text(
            500,
            50,
            text="⭐ INVINCIBLE! ⭐",
            font=("Arial", 24, "bold"),
            fill="gold",
            tags="power_up",
        )
        # Flash the indicator
        self.flash_indicator()
        # Duration set to 5 seconds
        self.master.after(5000, self.end_invincibility)

    def flash_indicator(self):
        """Makes the invincibility indicator flash"""
        if self.invincibility:
            current = self.canvas.itemcget(self.power_up_indicator, "state")
            new_state = "hidden" if current == "normal" else "normal"
            self.canvas.itemconfig(self.power_up_indicator, state=new_state)
            # Continue flashing if still invincible
            self.master.after(500, self.flash_indicator)

    def end_invincibility(self):
        """End invincibility power-up"""
        self.invincibility = False
        if hasattr(self, "power_up_indicator"):
            self.canvas.delete(self.power_up_indicator)

    def implement_levels(self):
        """Handle level progression and difficulty adjustments"""
        old_level = self.level

        # More flexible level progression
        self.level = 1 + self.score_value // 15  # Level up slightly faster

        # When level increases:
        if self.level != old_level:
            self.show_level_transition()
            self.update_difficulty()

    def show_level_transition(self):
        """Used to show level transition animation"""
        # Create level up text
        txt_id = self.canvas.create_text(
            500,
            300,
            text=f"Level {self.level}!",
            font=("Arial", 36, "bold"),
            fill="white",
        )

        # Adds fade out animation
        def fade_out(alpha=1.0):  # Alpha determines the transparency
            if alpha > 0:
                # Fading effect by changing text color
                opacity = int(255 * alpha)
                hex_opacity = format(opacity, '02x')
                rgb = f"{hex_opacity}"
                color = f"#{rgb * 3}"
                self.canvas.itemconfig(txt_id, fill=color)
                self.master.after(50, lambda: fade_out(alpha - 0.1))
            else:
                self.canvas.delete(txt_id)

        fade_out()

    def update_difficulty(self):
        """Update game parameters based on current level"""
        # Slower speed reduction as level increases
        self.base_speed = max(7 - (self.level * 0.3), 3)

        # Apple spawn rate becomes more dynamic
        self.spawn_rate = max(10 - (self.level // 2), 4)

        # Add more difficulty modifiers
        # Decreases allowed misses
        self.max_missed_apples = max(5 - (self.level // 3), 2)

    def update_score(
            self,
            golden_apple=False,
            rotten_apple=False,
            power_up=False):
        """Updates the score based on apple type and power-ups"""

        if golden_apple:
            self.score_value += 10
            self.enhance_visuals(
                "golden_catch",
                self.canvas.coords(self.basket_image_id)[0] + 75,
                500,
            )
            self.update_lives(golden_apple=True)
        elif rotten_apple and not self.invincibility:
            self.score_value -= 1
            self.enhance_visuals(
                "rotten_catch",
                self.canvas.coords(self.basket_image_id)[0] + 75,
                500,
            )
        else:
            self.score_value += 1
            self.enhance_visuals(
                "apple_catch",
                self.canvas.coords(self.basket_image_id)[0] + 75,
                500,
            )

        self.score_label.config(text=f"Score: {self.score_value}")

        # Check for level progression
        self.implement_levels()

    def update_lives(self, golden_apple=False, rotten_apple=False):
        """Updates the lives based on apple type"""

        if self.invincibility:  # Don't update lives
            return

        # Adjust lives based on apple type
        if rotten_apple:
            self.lives_value -= 1  # -1 life for rotten apple
        elif golden_apple:
            self.lives_value += 1  # +1 life for golden apple
        else:
            if self.lives_value > 0:  # -1 life for missing regular apple
                self.lives_value -= 1

        # Ensures lives don't become negative (below 0)
        self.lives_value = max(0, self.lives_value)

        # Update the lives label display
        self.lives_label.config(text=f"Lives: {self.lives_value}")

        # If lives reach 0, trigger the game over process
        if self.lives_value <= 0 and not self.game_over_flag:
            self.game_over()

    def periodic_falls(self):
        """Handle periodic falling of objects"""
        # Don't call if game is over or not started
        if (self.game_over_flag or self.is_paused or
                self.boss_key_active or not self.game_started):
            return

        try:
            # Calculate base delay depending on the level
            delay = max(2000 - (self.level * 200), 500)

            # Schedules the next call
            self.periodic_after_id = self.master.after(
                delay, self.periodic_falls)

            # Updating counters
            self.g_apple_counter += 1
            self.r_apple_counter += 1
            self.power_up_counter += 1

            normal_apple_prob = min(0.7 + (self.level * 0.05), 0.95)

            # Spawn objects
            if random.random() < normal_apple_prob:
                self.create_f1()

            # Spawn golden apples
            if self.g_apple_counter % max(8 - (self.level // 2), 3) == 0:
                self.create_g_f1()

            # Spawn rotten apples
            if self.r_apple_counter % max(12 - (self.level // 2), 4) == 0:
                if random.random() < 0.3 + (self.level * 0.05):
                    self.create_r_f1()

            # Spawn power-ups
            if self.power_up_counter % max(15 - (self.level // 2), 6) == 0:
                if random.random() < 0.2 + (self.level * 0.03):
                    self.create_power_up()

        except tk.TclError:
            if hasattr(self, 'periodic_after_id'):
                self.master.after_cancel(self.periodic_after_id)
                self.periodic_after_id = None

    def cancel_all_after_calls(self):
        """Cancel all scheduled after calls"""
        if hasattr(self, 'periodic_after_id'):
            try:
                self.master.after_cancel(self.periodic_after_id)
            except tk.TclError:
                pass
            self.periodic_after_id = None

    def create_basket(self):
        """Create the basket image at the specified coordinates"""
        self.basket_image_id = self.canvas.create_image(
            450, 500, anchor="nw", image=self.basket_image_tk
        )

    def move_left(self):
        """Binds keys to move the basket to the left"""
        # Get the current coords of the basket
        coords = self.canvas.coords(self.basket_image_id)
        # Ensure the basket doesn't move beyond the left edge of the canvas
        if coords[0] > 0:
            self.canvas.move(self.basket_image_id, -40, 0)

    def move_right(self):
        """Binds keys to move the basket to the right"""
        # Get the current position of the basket
        coords = self.canvas.coords(self.basket_image_id)
        # Get the canvas width and basket width
        canvas_width = self.canvas.winfo_width()
        basket_width = self.basket_image_tk.width()

        # Ensures the basket doesn't move beyond the right edge of the canvas
        if coords[0] < canvas_width - basket_width:
            self.canvas.move(self.basket_image_id, 40, 0)

    def check_collision(self, falling_object, basket):
        """Checks collision of apples and power ups with basket"""
        # Get the bounding box coords of the falling object and the basket
        object_coords = self.canvas.bbox(falling_object)
        basket_coords = self.canvas.bbox(basket)

        # Check if the object and basket overlap
        if object_coords and basket_coords:
            if (
                object_coords[2] >= basket_coords[0] and
                object_coords[0] <= basket_coords[2]
            ):
                if (
                    object_coords[3] >= basket_coords[1] and
                    object_coords[1] <= basket_coords[3]
                ):
                    return True
        return False

    def game_over(self):
        """Handles game over state and display the game over screen"""
        if self.game_over_flag:
            return
        self.game_over_flag = True

        # Cancel any ongoing periodic actions
        if hasattr(self, "periodic_falls"):
            self.master.after_cancel(self.periodic_falls)

        self.update_leaderboard(
            self.write_leaderboard
        )  # Update and saves the leaderboard

        self.master.withdraw()  # Hides the main window

        # Create a new game over window
        self.game_over_window = tk.Toplevel(self.master)
        self.game_over_window.title("Game Over")
        self.game_over_window.geometry("1000x600")

        # Set up background image and display "GAME OVER" text
        self.start_bg = Image.open("game_over_background.png").resize(
            (1000, 600), Image.LANCZOS
        )
        self.start_bg_tk = ImageTk.PhotoImage(self.start_bg)
        draw = ImageDraw.Draw(self.start_bg)
        font_path = "./PressStart2P-Regular.ttf"
        font_size = 40
        font = ImageFont.truetype(font_path, font_size)
        text = "GAME OVER"
        text_position = (350, 250)
        draw.text(text_position, text, font=font, fill="red")
        self.start_bg_tk = ImageTk.PhotoImage(self.start_bg)

        # Create canvas for the game over window
        canvas = tk.Canvas(self.game_over_window, width=1000, height=600)
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, anchor="nw", image=self.start_bg_tk)

        # Display name and score
        tk.Label(
            self.game_over_window,
            text=f"Player: {self.player_name}",
            font=("Arial", 16),
        ).place(x=350, y=300)
        tk.Label(
            self.game_over_window,
            text=f"Your Score: {self.score_value}",
            font=("Arial", 16),
        ).place(x=350, y=350)

        # Buttons for leaderboard, restart, and exit
        tk.Button(
            self.game_over_window,
            text="Leaderboard",
            font=("Arial", 14),
            command=lambda: self.show_leaderboard(),
        ).place(x=350, y=400)

        tk.Button(
            self.game_over_window,
            text="Restart",
            font=("Arial", 14),
            command=self.restart_game,
        ).place(x=480, y=400)

        tk.Button(
            self.game_over_window,
            text="Exit Game",
            font=("Arial", 14),
            command=self.master.quit,
        ).place(x=610, y=400)

        # Help button for game instructions
        self.help_button = tk.Button(
            self.game_over_window,
            image=self.help_icon_tk,
            compound=tk.CENTER,
            command=self.show_game_help,
            borderwidth=0,
            highlightthickness=0,
        )
        self.help_button.place(x=900, y=10)

    def restart_game(self):
        """Reset game state and return to the start game window"""
        self.score_value = 0
        self.lives_value = 5
        self.g_apple_counter = 0
        self.r_apple_counter = 0
        self.power_up_counter = 0
        self.game_over_flag = False
        self.invincibility = False
        self.is_paused = False
        self.game_started = False
        self.level = 1
        self.large_basket = False
        self.cheat_invincibility = False
        self.cheat_code_buffer = ""

        # Cancel any periodic actions
        if hasattr(self, "periodic_after_id"):
            self.master.after_cancel(self.periodic_after_id)
            self.periodic_after_id = None

        # Update score and lives labels
        self.score_label.config(text=f"Score: {self.score_value}")
        self.lives_label.config(text=f"Lives: {self.lives_value}")

        # Close the game over window
        self.game_over_window.destroy()

        # Clear the canvas and reset background
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.bg_image_tk)

        # Unbind previous key events
        self.master.unbind("<KeyPress>")

        # Call start_game to show the initial setup screen
        self.start_game()


if __name__ == "__main__":
    window = tk.Tk()
    window.title("Apple Catcher")
    window.geometry("1000x600")
    window.resizable(False, False)

    game = Game(window)
    window.mainloop()
