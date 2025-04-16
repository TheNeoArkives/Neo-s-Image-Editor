import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps
import threading
import io  # For handling image data in memory

class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Neo's Image Editor")
        self.root.geometry("1200x800")

        self.img = None
        self.img_path = None
        self.tk_img = None
        self.original_image = None
        self.zoom_level = 1.0
        self.crop_start_x = 0
        self.crop_start_y = 0
        self.cropping = False

        # Main container frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill="both", expand=True)

        # Canvas for image display
        self.canvas = tk.Canvas(self.main_frame, width=800, height=600, bg="gray", cursor="crosshair")
        self.canvas.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="nsew")
        self.image_on_canvas = None
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Zoom

        # Control panel frame
        self.control_panel = ttk.Frame(self.main_frame)
        self.control_panel.grid(row=1, column=0, sticky="w")

        # File operations
        ttk.Button(self.control_panel, text="Open", command=self.open_image).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(self.control_panel, text="Save", command=self.save_image).grid(row=0, column=1, padx=5, pady=5)
        self.save_format_var = tk.StringVar(value="PNG")
        ttk.OptionMenu(self.control_panel, self.save_format_var, "PNG", "JPEG", "BMP", "TIFF").grid(row=0, column=2, padx=5, pady=5)

        # Basic transformations
        ttk.Button(self.control_panel, text="Grayscale", command=self.apply_grayscale).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(self.control_panel, text="Blur", command=self.apply_blur).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.control_panel, text="Rotate", command=self.rotate_image).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(self.control_panel, text="Resize", command=self.resize_image).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(self.control_panel, text="Flip Horizontally", command=self.flip_horizontal).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(self.control_panel, text="Flip Vertically", command=self.flip_vertical).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(self.control_panel, text="Crop", command=self.start_crop).grid(row=2, column=2, padx=5, pady=5)
        ttk.Button(self.control_panel, text="Reset", command=self.reset_image).grid(row=2, column=3, padx=5, pady=5)

        # Filters Frame
        self.filter_frame = ttk.Frame(self.main_frame, padding="10")
        self.filter_frame.grid(row=1, column=1, sticky="nw")
        ttk.Label(self.filter_frame, text="Filters:", font=("Arial", 12)).pack(pady=5)
        ttk.Button(self.filter_frame, text="Sharpen", command=self.apply_sharpen).pack(pady=2, fill="x")
        ttk.Button(self.filter_frame, text="Edge Enhance", command=self.apply_edge_enhance).pack(pady=2, fill="x")
        ttk.Button(self.filter_frame, text="Emboss", command=self.apply_emboss).pack(pady=2, fill="x")
        ttk.Button(self.filter_frame, text="Find Edges", command=self.apply_find_edges).pack(pady=2, fill="x")

        # Enhancement controls frame
        self.enhance_frame = ttk.Frame(self.main_frame, padding="10")
        self.enhance_frame.grid(row=1, column=2, sticky="ne")
        ttk.Label(self.enhance_frame, text="Enhancements:", font=("Arial", 12)).pack(pady=5)
        self.brightness_label = ttk.Label(self.enhance_frame, text="Brightness:")
        self.brightness_label.pack()
        self.brightness_scale = ttk.Scale(self.enhance_frame, from_=0.1, to=3.0, value=1.0, command=self.adjust_brightness)
        self.brightness_scale.pack(pady=5)
        self.contrast_label = ttk.Label(self.enhance_frame, text="Contrast:")
        self.contrast_label.pack()
        self.contrast_scale = ttk.Scale(self.enhance_frame, from_=0.1, to=3.0, value=1.0, command=self.adjust_contrast)
        self.contrast_scale.pack(pady=5)
        self.sharpness_label = ttk.Label(self.enhance_frame, text="Sharpness:")
        self.sharpness_label.pack()
        self.sharpness_scale = ttk.Scale(self.enhance_frame, from_=0.0, to=5.0, value=1.0, command=self.adjust_sharpness)
        self.sharpness_scale.pack(pady=5)

        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief="sunken", anchor="w", font=("Arial", 10))
        self.status_bar.pack(side="bottom", fill="x")
        self.status_text = tk.StringVar()
        self.status_bar.config(textvariable=self.status_text)

        # Make the main frame resizable
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.root.bind("<Configure>", self.on_resize)

    def display_status(self, text):
        self.status_text.set(text)
        self.root.update_idletasks()

    def open_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.img_path = file_path
            try:
                self.display_status("Loading image...")
                threading.Thread(target=self._load_image, args=(file_path,)).start()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {e}")
                self.display_status("Ready")

    def _load_image(self, file_path):
        try:
            img = Image.open(file_path)
            self.original_image = img.copy()
            self.img = img
            self.zoom_level = 1.0  # Reset zoom
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Image loaded"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error loading image: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def _update_image_display(self, resize=True):
        if self.img:
            size = (int(self.img.width * self.zoom_level), int(self.img.height * self.zoom_level))
            if resize:
                img = self.img.copy() #important, avoid modifying the original image.
                img.thumbnail(size)
                self.tk_img = ImageTk.PhotoImage(img)
            else:
                 img = self.img.resize(size, Image.Resampling.LANCZOS)
                 self.tk_img = ImageTk.PhotoImage(img)

            if self.image_on_canvas:
                self.canvas.itemconfig(self.image_on_canvas, image=self.tk_img)
            else:
                self.image_on_canvas = self.canvas.create_image(self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2, image=self.tk_img)
            self.canvas.config(scrollregion=self.canvas.bbox("all")) #update the scrollable region
    def save_image(self):
        if self.img:
            file_path = filedialog.asksaveasfilename(defaultextension="." + self.save_format_var.get().lower())
            if file_path:
                try:
                    self.display_status("Saving image...")
                    # Use a thread for saving
                    threading.Thread(target=self._save_image, args=(file_path,)).start()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not save image: {e}")
                    self.display_status("Ready")
        else:
            messagebox.showerror("Error", "No image loaded to save.")

    def _save_image(self, file_path):
        try:
            format = self.save_format_var.get()
            if format == "JPEG":
                self.img.save(file_path, format="JPEG", quality=95)  # Specify quality
            else:
                self.img.save(file_path, format=format)
            self.root.after(0, lambda: messagebox.showinfo("Image Saved", "Image has been saved successfully!"))
            self.root.after(0, lambda: self.display_status("Ready"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error saving image: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def apply_grayscale(self):
        if self.img:
            self.display_status("Applying grayscale filter...")
            threading.Thread(target=self._apply_grayscale).start()

    def _apply_grayscale(self):
        try:
            self.img = self.img.convert("L").convert("RGB")
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Grayscale applied"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error applying filter: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def apply_blur(self):
        if self.img:
            self.display_status("Applying blur filter...")
            threading.Thread(target=self._apply_blur).start()

    def _apply_blur(self):
        try:
            self.img = self.img.filter(ImageFilter.BLUR)
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Blur applied"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error applying filter: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def rotate_image(self):
        if self.img:
            self.display_status("Rotating image...")
            threading.Thread(target=self._rotate_image).start()

    def _rotate_image(self):
        try:
            angle = simpledialog.askinteger("Rotation Angle", "Enter rotation angle in degrees:", parent=self.root, initialvalue=90)
            if angle is not None:
                self.img = self.img.rotate(angle, expand=True)
                self.root.after(0, self._update_image_display, True)
                self.root.after(0, lambda: self.display_status(f"Image rotated by {angle} degrees"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error rotating image: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def resize_image(self):
        if self.img:
            self.display_status("Resizing image...")
            threading.Thread(target=self._resize_image).start()

    def _resize_image(self):
        try:
            width = simpledialog.askinteger("Width", "Enter new width:", parent=self.root, initialvalue=self.img.width)
            height = simpledialog.askinteger("Height", "Enter new height:", parent=self.root, initialvalue=self.img.height)
            if width is not None and height is not None:
                self.img = self.img.resize((width, height))
                self.root.after(0, self._update_image_display)
                self.root.after(0, lambda: self.display_status(f"Image resized to {width}x{height}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error resizing image: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def flip_horizontal(self):
        if self.img:
            self.display_status("Flipping horizontally...")
            threading.Thread(target=self._flip_horizontal).start()

    def _flip_horizontal(self):
        try:
            self.img = self.img.transpose(Image.FLIP_LEFT_RIGHT)
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Flipped horizontally"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error flipping image: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def flip_vertical(self):
        if self.img:
            self.display_status("Flipping vertically...")
            threading.Thread(target=self._flip_vertical).start()

    def _flip_vertical(self):
        try:
            self.img = self.img.transpose(Image.FLIP_TOP_BOTTOM)
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Flipped vertically"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error flipping image: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def apply_sharpen(self):
        if self.img:
            self.display_status("Applying sharpen filter...")
            threading.Thread(target=self._apply_sharpen).start()

    def _apply_sharpen(self):
        try:
            self.img = self.img.filter(ImageFilter.SHARPEN)
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Sharpen filter applied"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error applying filter: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def apply_edge_enhance(self):
        if self.img:
            self.display_status("Applying edge enhance filter...")
            threading.Thread(target=self._apply_edge_enhance).start()

    def _apply_edge_enhance(self):
        try:
            self.img = self.img.filter(ImageFilter.EDGE_ENHANCE)
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Edge enhance filter applied"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error applying filter: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def apply_emboss(self):
        if self.img:
            self.display_status("Applying emboss filter...")
            threading.Thread(target=self._apply_emboss).start()

    def _apply_emboss(self):
        try:
            self.img = self.img.filter(ImageFilter.EMBOSS)
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Emboss filter applied"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error applying filter: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def apply_find_edges(self):
        if self.img:
            self.display_status("Applying find edges filter...")
            threading.Thread(target=self._apply_find_edges).start()

    def _apply_find_edges(self):
        try:
            self.img = self.img.filter(ImageFilter.FIND_EDGES)
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Find edges filter applied"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error applying filter: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))
    def adjust_brightness(self, value):
        if self.img:
            self.display_status("Adjusting brightness...")
            threading.Thread(target=self._adjust_brightness, args=(value,)).start()

    def _adjust_brightness(self, value):
        try:
            enhancer = ImageEnhance.Brightness(self.img)
            self.img = enhancer.enhance(float(value))
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Brightness adjusted"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error adjusting brightness: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def adjust_contrast(self, value):
        if self.img:
            self.display_status("Adjusting contrast...")
            threading.Thread(target=self._adjust_contrast, args=(value,)).start()

    def _adjust_contrast(self, value):
        try:
            enhancer = ImageEnhance.Contrast(self.img)
            self.img = enhancer.enhance(float(value))
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Contrast adjusted"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error adjusting contrast: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def adjust_sharpness(self, value):
        if self.img:
            self.display_status("Adjusting sharpness...")
            threading.Thread(target=self._adjust_sharpness, args=(value,)).start()

    def _adjust_sharpness(self, value):
        try:
            enhancer = ImageEnhance.Sharpness(self.img)
            self.img = enhancer.enhance(float(value))
            self.root.after(0, self._update_image_display)
            self.root.after(0, lambda: self.display_status("Sharpness adjusted"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error adjusting sharpness: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def reset_image(self):
        if self.original_image:
            self.display_status("Resetting image to original...")
            threading.Thread(target=self._reset_image).start()

    def _reset_image(self):
        try:
            self.img = self.original_image.copy()
            self.zoom_level = 1.0
            self.root.after(0, self._update_image_display, True)
            self.root.after(0, lambda: self.display_status("Image reset to original"))
            self.brightness_scale.set(1.0)
            self.contrast_scale.set(1.0)
            self.sharpness_scale.set(1.0)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error resetting image: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

    def on_resize(self, event):
        new_width = event.width - 400
        new_height = event.height - 300
        new_width = max(new_width, 300)
        new_height = max(new_height, 200)
        self.canvas.config(width=new_width, height=new_height)
        self._update_image_display(resize=False)

    def on_mousewheel(self, event):
        if self.img:
            if event.delta > 0:
                self.zoom_level *= 1.1
            else:
                self.zoom_level /= 1.1
            self.zoom_level = max(0.1, min(self.zoom_level, 5.0))  # Limit zoom
            self._update_image_display(resize=False)

    def on_canvas_click(self, event):
        if self.cropping:
            self.crop_start_x = event.x
            self.crop_start_y = event.y
            self.canvas.delete("crop_rect")  # Remove previous rectangle

    def on_canvas_drag(self, event):
        if self.cropping:
            x1, y1 = self.crop_start_x, self.crop_start_y
            x2, y2 = event.x, event.y
            self.canvas.delete("crop_rect")
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", tags="crop_rect")

    def on_canvas_release(self, event):
        if self.cropping:
            self.cropping = False
            x1, y1 = self.crop_start_x, self.crop_start_y
            x2, y2 = event.x, event.y
            if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:  # Min size
                self.crop_region = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                self.display_status("Crop region selected. Click 'Crop' again to apply.")
                self.apply_crop() # Auto apply crop
            else:
                self.display_status("Crop selection too small.  Try again.")

    def start_crop(self):
        if self.img:
            self.cropping = True
            self.display_status("Click and drag to select crop region.")
        else:
            messagebox.showerror("Error", "No image loaded to crop.")

    def apply_crop(self):
        if self.img and hasattr(self, 'crop_region'):
            self.display_status("Cropping image...")
            threading.Thread(target=self._apply_crop).start()

    def _apply_crop(self):
        try:
            x1, y1, x2, y2 = self.crop_region
            #scale crop region based on zoom level
            x1_scaled = int(x1/self.zoom_level)
            y1_scaled = int(y1/self.zoom_level)
            x2_scaled = int(x2/self.zoom_level)
            y2_scaled = int(y2/self.zoom_level)

            self.img = self.img.crop((x1_scaled, y1_scaled, x2_scaled, y2_scaled))
            self.zoom_level = 1.0 #reset zoom
            self.root.after(0, self._update_image_display, True)
            self.root.after(0, lambda: self.display_status("Image cropped"))
            self.canvas.delete("crop_rect")  # Remove the rectangle
            del self.crop_region
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error cropping image: {e}"))
            self.root.after(0, lambda: self.display_status("Ready"))

if __name__ == "__main__":
    root = tk.Tk()
    editor = ImageEditor(root)
    root.mainloop()
