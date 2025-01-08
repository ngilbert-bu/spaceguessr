import requests
import random
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from io import BytesIO
from openai import OpenAI
from config import NASA_API_KEY, OPENAI_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# API URLs
APOD_URL = "https://api.nasa.gov/planetary/apod"

def get_random_date(start_date, end_date):
    """Generate a random date between start_date and end_date."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def fetch_random_apod():
    """Fetch a random Astronomy Picture of the Day (APOD) and return metadata."""
    start_date = datetime(1995, 6, 16)  # APOD's launch date
    end_date = datetime.today()

    random_date = get_random_date(start_date, end_date)
    params = {"api_key": NASA_API_KEY, "date": random_date.strftime("%Y-%m-%d")}
    response = requests.get(APOD_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        title = data.get("title", "No Title Available")
        image_url = data.get("url", None)
        return title, image_url
    else:
        print(f"Failed to fetch APOD. Error code: {response.status_code}")
        return None, None

def generate_answers(title):
    """Generate one correct and three false answers for the image title."""
    prompt = f"""
    The title of the Astronomy Picture of the Day image is: '{title}'. 
    Generate one correct answer and three false answers to the question: What location is shown in this image?.
    The three false locations should be random and related to the true location.
    Do not use commas except to separate the answer choices. For example, instead of Mount Fiji, Japan use Mount Fiji Japan
    Do not use any special characters and do not use quotation marks.
    Example format:
    [correct location, false location 1, false location 2, false location 3]
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content.strip('[]')
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def generate_description(title):
    """Generate one correct and three false answers for the image title."""
    prompt = f"""
    The title of the Astronomy Picture of the Day image is: '{title}'.
    The photo is part of the nasa.gov apod collection. 
    Write a two sentence description of this image. Do not use the term 'Astronomy Photo of the Day'.
    """
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def resize_image_with_aspect_ratio(image, max_width, max_height):
    """Resize the image while maintaining its aspect ratio."""
    original_width, original_height = image.size
    aspect_ratio = original_width / original_height

    if original_width > original_height:
        new_width = min(max_width, original_width)
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(max_height, original_height)
        new_width = int(new_height * aspect_ratio)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def update_game(root, title_label, image_label, button_frame):
    """Update the game content for a new round."""
    title, image_url = fetch_random_apod()
    if not (title and image_url):
        messagebox.showerror("Error", "Failed to fetch new data. Exiting the game.")
        root.quit()
        return

    answers_text = generate_answers(title)
    if not answers_text:
        messagebox.showerror("Error", "Failed to generate answers. Exiting the game.")
        root.quit()
        return

    # Generate image description
    description = generate_description(title)
    if not description:
        description = "Description not available."

    # Update the title
    title_label.config(text="Where am I in space?")

    # Fetch and update the image
    response = requests.get(image_url)
    img_data = Image.open(BytesIO(response.content))
    img_data = resize_image_with_aspect_ratio(img_data, max_width=500, max_height=350)
    img = ImageTk.PhotoImage(img_data)
    image_label.config(image=img)
    image_label.image = img

    # Update the buttons
    answers = [answer.strip() for answer in answers_text.split(",")]
    correct_answer = answers[0]
    options = answers
    random.shuffle(options)

    # Clear old buttons and create new ones
    for widget in button_frame.winfo_children():
        widget.destroy()

    def check_answer(answer):
        if answer == correct_answer:
            messagebox.showinfo("Correct!", f"You guessed the correct location!\n\nDescription:\n{description}")
        else:
            messagebox.showinfo("Wrong!", f"The correct answer was: {correct_answer}\n\nDescription:\n{description}")
        # Start a new round without closing the window
        update_game(root, title_label, image_label, button_frame)

    for option in options:
        btn = tk.Button(button_frame, text=option, font=("Arial", 14), command=lambda opt=option: check_answer(opt))
        btn.pack(pady=5)

def display_game():
    """Create a GUI to display the image and allow the user to guess."""
    # GUI setup
    root = tk.Tk()
    root.title("Astronomy Picture of the Day Quiz")

    # Title label
    title_label = tk.Label(root, text="Where am I in space?", font=("Arial", 16, "bold"), wraplength=500)
    title_label.pack(pady=10)

    # Image label
    image_label = tk.Label(root)
    image_label.pack()

    # Button frame
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    # Start the first game
    update_game(root, title_label, image_label, button_frame)

    root.mainloop()

# Main Program Flow
display_game()
