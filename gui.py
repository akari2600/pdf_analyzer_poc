from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from pdf_processor import load_pdf
from image_analyzer import preprocess_image, analyze_layout
import cv2
import numpy as np
import os

class PDFAnalyzerGUI(BoxLayout):
    def __init__(self, **kwargs):
        super(PDFAnalyzerGUI, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        # Top controls
        top_controls = BoxLayout(size_hint_y=None, height=40)
        self.file_button = Button(text='Choose File', size_hint_x=None, width=100)
        self.file_button.bind(on_release=self.show_file_chooser)
        self.file_label = Label(text='No file chosen', size_hint_x=1)
        top_controls.add_widget(self.file_button)
        top_controls.add_widget(self.file_label)
        self.add_widget(top_controls)

        # Image preview
        self.image_preview = Image(allow_stretch=True, keep_ratio=True, size_hint_y=0.6)
        self.add_widget(self.image_preview)

        # Layout data display
        self.layout_data_display = TextInput(readonly=True, size_hint_y=0.2)
        self.add_widget(self.layout_data_display)

        # Bottom controls
        bottom_controls = BoxLayout(orientation='vertical', size_hint_y=None, height=120)
        
        # Preprocessing checkbox
        preprocess_layout = BoxLayout(size_hint_y=None, height=30)
        self.preprocess_checkbox = CheckBox()
        self.preprocess_checkbox.bind(active=self.on_preprocess_change)
        preprocess_layout.add_widget(Label(text='Enable Preprocessing'))
        preprocess_layout.add_widget(self.preprocess_checkbox)
        bottom_controls.add_widget(preprocess_layout)

        # Threshold inputs
        threshold_layout = BoxLayout(size_hint_y=None, height=30)
        threshold_layout.add_widget(Label(text='Threshold (%):'))
        self.x_threshold = TextInput(text='95', multiline=False)
        self.y_threshold = TextInput(text='95', multiline=False)
        self.x_threshold.bind(text=self.schedule_on_threshold_change)
        self.y_threshold.bind(text=self.schedule_on_threshold_change)
        threshold_layout.add_widget(Label(text='X:'))
        threshold_layout.add_widget(self.x_threshold)
        threshold_layout.add_widget(Label(text='Y:'))
        threshold_layout.add_widget(self.y_threshold)
        bottom_controls.add_widget(threshold_layout)

        # Analyze button
        self.analyze_button = Button(text='Analyze Layout', size_hint_y=None, height=40)
        self.analyze_button.bind(on_press=self.analyze_layout)
        bottom_controls.add_widget(self.analyze_button)

        self.add_widget(bottom_controls)

        self.current_image = None
        self.layout_data = None
        self.threshold_update_event = None

    def show_file_chooser(self, instance):
        content = BoxLayout(orientation='vertical')
        initial_path = os.getcwd()
        file_chooser = FileChooserListView(path=initial_path)
        content.add_widget(file_chooser)
        
        def load(selection):
            if selection:
                self.load_pdf(selection[0])
            self._popup.dismiss()

        btn_layout = BoxLayout(size_hint_y=None, height=30)
        btn_layout.add_widget(Button(text='Cancel', on_release=lambda x: self._popup.dismiss()))
        btn_layout.add_widget(Button(text='Load', on_release=lambda x: load(file_chooser.selection)))
        content.add_widget(btn_layout)

        self._popup = Popup(title="Choose PDF file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load_pdf(self, pdf_path):
        print(f"Loading PDF: {pdf_path}")
        try:
            image = load_pdf(pdf_path)
            self.current_image = np.array(image)
            print(f"Image shape: {self.current_image.shape}")
            self.file_label.text = os.path.basename(pdf_path)
            self.analyze_layout(None)
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            import traceback
            traceback.print_exc()

    def schedule_on_threshold_change(self, instance, value):
        if self.threshold_update_event:
            self.threshold_update_event.cancel()
        self.threshold_update_event = Clock.schedule_once(self.delayed_threshold_change, 0.5)

    def delayed_threshold_change(self, dt):
        try:
            x_thresh = float(self.x_threshold.text)
            y_thresh = float(self.y_threshold.text)
            if 0 <= x_thresh <= 100 and 0 <= y_thresh <= 100:
                self.analyze_layout(None)
            else:
                print("Thresholds must be between 0 and 100")
        except ValueError:
            print("Invalid threshold values")

    def on_preprocess_change(self, instance, value):
        if self.current_image is not None:
            self.analyze_layout(None)

    def analyze_layout(self, instance):
        if self.current_image is not None:
            try:
                image = preprocess_image(self.current_image) if self.preprocess_checkbox.active else self.current_image
                x_thresh = float(self.x_threshold.text)
                y_thresh = float(self.y_threshold.text)
                self.layout_data = analyze_layout(image, x_thresh, y_thresh)
                self.update_image_preview()
                self.update_layout_data_display()
            except ValueError:
                print("Invalid threshold values. Please enter valid numbers between 0 and 100.")

    def update_image_preview(self):
        if self.current_image is not None:
            image = self.current_image.copy()
            if self.preprocess_checkbox.active:
                image = preprocess_image(image)
            
            image = self.prepare_image_for_display(image)

            buf = image.tobytes()
            texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt='rgb')
            texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            self.image_preview.texture = texture

    def prepare_image_for_display(self, image):
        # Ensure the image is in RGB format
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        # Flip the image vertically
        image = cv2.flip(image, 0)
        
        # Apply layout if available
        if self.layout_data:
            image = self.apply_layout_to_image(image)
        
        return image

    def apply_layout_to_image(self, image):
        height, width = image.shape[:2]
        overlay = np.zeros((height, width, 3), dtype=np.uint8)
        
        x_cuts = self.layout_data['x_cuts']
        y_cuts = self.layout_data['y_cuts']
        
        # Apply x-cuts (horizontal, green)
        for start, end in x_cuts:
            cv2.rectangle(overlay, (0, start), (width, end), (0, 255, 0), -1)
        
        # Apply y-cuts (vertical, red)
        for start, end in y_cuts:
            current_overlay = overlay.copy()
            cv2.rectangle(current_overlay, (start, 0), (end, height), (255, 0, 0), -1)
            # Use maximum values for overlapping areas (additive color mixing)
            overlay = np.maximum(overlay, current_overlay)
        
        # Blend the overlay with the original image
        result = cv2.addWeighted(image, 1, overlay, 0.3, 0)
        return result

    def update_layout_data_display(self):
        if self.layout_data:
            x_cuts = self.layout_data['x_cuts']
            y_cuts = self.layout_data['y_cuts']
            display_text = f"X-cuts: {x_cuts}\nY-cuts: {y_cuts}"
            self.layout_data_display.text = display_text
        else:
            self.layout_data_display.text = "No layout data available"

class PDFAnalyzerApp(App):
    def build(self):
        return PDFAnalyzerGUI()

if __name__ == '__main__':
    PDFAnalyzerApp().run()
