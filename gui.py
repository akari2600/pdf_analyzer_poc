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
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from pdf_processor import load_pdf
from image_analyzer import analyze_layout, preprocess_image
import cv2
import numpy as np
import os
import threading

class CollapsibleTextInput(BoxLayout):
    def __init__(self, **kwargs):
        super(CollapsibleTextInput, self).__init__(orientation='vertical', **kwargs)
        self.toggle_button = ToggleButton(text='Show Analysis Results', size_hint_y=None, height=40)
        self.toggle_button.bind(on_press=self.toggle_content)
        self.add_widget(self.toggle_button)
        
        self.content = TextInput(readonly=True, size_hint_y=None, height=0)
        self.add_widget(self.content)
    
    def toggle_content(self, instance):
        if instance.state == 'down':
            instance.text = 'Hide Analysis Results'
            self.content.height = 200  # or any desired height
        else:
            instance.text = 'Show Analysis Results'
            self.content.height = 0

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

        # Granularity slider
        slider_layout = BoxLayout(size_hint_y=None, height=50)
        slider_layout.add_widget(Label(text='Granularity:'))
        self.granularity_slider = Slider(min=1, max=100, value=50)
        self.granularity_slider.bind(value=self.on_granularity_change)
        slider_layout.add_widget(self.granularity_slider)
        self.add_widget(slider_layout)

        # Layout data display (collapsible)
        self.layout_data_display = CollapsibleTextInput(size_hint_y=None, height=40)
        self.add_widget(self.layout_data_display)

        # Bottom controls
        bottom_controls = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        
        # Preprocessing checkbox
        preprocess_layout = BoxLayout(size_hint_y=None, height=30)
        self.preprocess_checkbox = CheckBox()
        self.preprocess_checkbox.bind(active=self.on_preprocess_change)
        preprocess_layout.add_widget(Label(text='Enable Preprocessing'))
        preprocess_layout.add_widget(self.preprocess_checkbox)
        bottom_controls.add_widget(preprocess_layout)

        # Analyze button
        self.analyze_button = Button(text='Analyze Layout', size_hint_y=None, height=40)
        self.analyze_button.bind(on_press=self.start_analysis)
        bottom_controls.add_widget(self.analyze_button)

        self.add_widget(bottom_controls)

        # Loading indicator
        self.loading_popup = Popup(title='Analyzing...', content=Label(text='Please wait...'), size_hint=(0.8, 0.2))

        self.current_image = None
        self.layout_data = None

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
            self.update_image_preview()
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            import traceback
            traceback.print_exc()

    def on_preprocess_change(self, instance, value):
        if self.current_image is not None:
            self.update_image_preview()

    def on_granularity_change(self, instance, value):
        # We don't need to do anything here, as the value will be used in start_analysis
        pass

    def start_analysis(self, instance):
        if self.current_image is not None:
            self.loading_popup.open()
            threading.Thread(target=self.analyze_layout).start()

    def analyze_layout(self):
        try:
            image = preprocess_image(self.current_image) if self.preprocess_checkbox.active else self.current_image
            granularity = int(self.granularity_slider.value)
            self.layout_data = analyze_layout(image, granularity)
            Clock.schedule_once(self.update_ui_after_analysis)
        except Exception as e:
            print(f"Error analyzing layout: {str(e)}")
            import traceback
            traceback.print_exc()
            Clock.schedule_once(lambda dt: self.loading_popup.dismiss())

    def update_ui_after_analysis(self, dt):
        self.loading_popup.dismiss()
        self.update_image_preview()
        self.update_layout_data_display()

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
        
        # Apply layout if available
        if self.layout_data:
            image = self.apply_layout_to_image(image)
        
        # Flip the image vertically
        image = cv2.flip(image, 0)
        
        return image

    def apply_layout_to_image(self, image):
        if not self.layout_data:
            return image

        overlay = image.copy()
        elements = self.layout_data['elements']
        relationships = self.layout_data['relationships']

        # Draw bounding boxes for elements
        colors = {
            'text_block': (0, 255, 0),  # Green
            'image': (255, 0, 0),      # Blue
            'table': (0, 0, 255),      # Red
            'line': (255, 255, 0),     # Cyan
            'unknown': (128, 128, 128) # Gray
        }

        height = image.shape[0]
        for element in elements:
            x, y, w, h = element.bbox
            color = colors.get(element.type, (128, 128, 128))
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
            # Place the text label above the bounding box
            cv2.putText(overlay, element.type, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Draw lines for relationships
        for i, j, relationship in relationships:
            elem1 = elements[i]
            elem2 = elements[j]
            x1, y1, w1, h1 = elem1.bbox
            x2, y2, w2, h2 = elem2.bbox
            start = (x1 + w1 // 2, y1 + h1 // 2)
            end = (x2 + w2 // 2, y2 + h2 // 2)
            cv2.line(overlay, start, end, (255, 0, 255), 1)  # Magenta

        # Blend the overlay with the original image
        result = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
        return result

    def update_layout_data_display(self):
        if self.layout_data:
            elements = self.layout_data['elements']
            relationships = self.layout_data['relationships']
            
            display_text = "Layout Analysis Results:\n\n"
            display_text += "Elements:\n"
            for i, elem in enumerate(elements):
                display_text += f"{i}: {elem.type} at {elem.bbox}\n"
            
            display_text += "\nRelationships:\n"
            for i, j, rel in relationships:
                display_text += f"Element {i} is {rel} Element {j}\n"
            
            self.layout_data_display.content.text = display_text
        else:
            self.layout_data_display.content.text = "No layout data available"

class PDFAnalyzerApp(App):
    def build(self):
        return PDFAnalyzerGUI()

if __name__ == '__main__':
    PDFAnalyzerApp().run()