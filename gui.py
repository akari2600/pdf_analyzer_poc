import cv2
import numpy as np
import os
import threading

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
from kivy.uix.splitter import Splitter  # Import Splitter
from kivy.core.window import Window

from pdf_processor import load_pdf, get_total_pages
from image_analyzer import analyze_layout, preprocess_image


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
        super(PDFAnalyzerGUI, self).__init__(orientation='horizontal', **kwargs)
        self.orientation = 'horizontal'

        # Bind to window resize event
        Window.bind(size=self.on_window_resize)
            
        # Splitter configuration for left image pane 
        left_splitter = Splitter(sizable_from='right', min_size=100, max_size=2000, size_hint=(1, 1))
        self.image_preview = Image(allow_stretch=True, keep_ratio=True)
        left_splitter.add_widget(self.image_preview)
        self.add_widget(left_splitter)

        # Right pane: Controls
        right_pane = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(None, 1), width=400)

        # Adding right splitter to root layout
        self.add_widget(right_pane)

        # Top controls
        top_controls = BoxLayout(size_hint_y=None, height=40)
        self.file_button = Button(text='Choose File', size_hint_x=None, width=100)
        self.file_button.bind(on_release=self.show_file_chooser)
        self.file_label = Label(text='No file chosen', size_hint_x=1)
        top_controls.add_widget(self.file_button)
        top_controls.add_widget(self.file_label)
        right_pane.add_widget(top_controls)

        # Page controls
        page_controls = BoxLayout(size_hint_y=None, height=40)
        self.page_dec_button = Button(text='-', size_hint_x=None, width=40)
        self.page_dec_button.bind(on_release=self.decrement_page)
        self.current_page_input = TextInput(text='1', multiline=False, size_hint_x=None, width=50)
        self.current_page_input.bind(on_text_validate=self.on_page_input)
        self.page_inc_button = Button(text='+', size_hint_x=None, width=40)
        self.page_inc_button.bind(on_release=self.increment_page)
        self.total_pages_label = Label(text='/ 1')
        self.page_slider = Slider(min=1, max=1, value=1, step=1)
        self.page_slider.bind(value=self.on_page_slider)
        page_controls.add_widget(Label(text='Page:'))
        page_controls.add_widget(self.page_dec_button)
        page_controls.add_widget(self.current_page_input)
        page_controls.add_widget(self.page_inc_button)
        page_controls.add_widget(self.total_pages_label)
        page_controls.add_widget(self.page_slider)
        right_pane.add_widget(page_controls)

        # Add Zoom controls
        zoom_controls = BoxLayout(size_hint_y=None, height=40)
        self.zoom_out_button = Button(text='-', size_hint_x=None, width=40)
        self.zoom_out_button.bind(on_release=self.decrease_zoom)
        self.zoom_label = Label(text='Zoom: 100%', size_hint_x=1)
        self.zoom_in_button = Button(text='+', size_hint_x=None, width=40)
        self.zoom_in_button.bind(on_release=self.increase_zoom)
        zoom_controls.add_widget(self.zoom_out_button)
        zoom_controls.add_widget(self.zoom_label)
        zoom_controls.add_widget(self.zoom_in_button)
        right_pane.add_widget(zoom_controls)

        # Granularity slider
        slider_layout = BoxLayout(size_hint_y=None, height=50)
        slider_layout.add_widget(Label(text='Granularity:'))
        self.granularity_slider = Slider(min=1, max=100, value=20)
        self.granularity_slider.bind(value=self.on_granularity_change)
        slider_layout.add_widget(self.granularity_slider)
        right_pane.add_widget(slider_layout)

        # Layout data display (collapsible)
        self.layout_data_display = CollapsibleTextInput(size_hint_y=None, height=40)
        right_pane.add_widget(self.layout_data_display)

        # Bottom controls
        bottom_controls = BoxLayout(orientation='vertical', size_hint_y=None, height=120)
        
        # Preprocessing checkbox
        preprocess_layout = BoxLayout(size_hint_y=None, height=30)
        self.preprocess_checkbox = CheckBox()
        self.preprocess_checkbox.bind(active=self.on_preprocess_change)
        preprocess_layout.add_widget(Label(text='Enable Preprocessing'))
        preprocess_layout.add_widget(self.preprocess_checkbox)
        bottom_controls.add_widget(preprocess_layout)

        # Relationship lines checkbox
        relationship_layout = BoxLayout(size_hint_y=None, height=30)
        self.relationship_checkbox = CheckBox(active=False)  # Unchecked by default
        self.relationship_checkbox.bind(active=self.on_relationship_change)
        relationship_layout.add_widget(Label(text='Show Relationships'))
        relationship_layout.add_widget(self.relationship_checkbox)
        bottom_controls.add_widget(relationship_layout)

        # Analyze button
        self.analyze_button = Button(text='Analyze Layout', size_hint_y=None, height=40)
        self.analyze_button.bind(on_press=self.start_analysis)
        bottom_controls.add_widget(self.analyze_button)

        right_pane.add_widget(bottom_controls)

        # Loading indicator
        self.loading_popup = Popup(title='Analyzing...', content=Label(text='Please wait...'), size_hint=(0.8, 0.2))

        self.current_image = None
        self.layout_data = None
        self.pdf_path = None
        self.total_pages = 1
        self.zoom_value = 1 # zoom value starts at 1 (100%)

    def increment_page(self, instance):
        current_page = int(self.current_page_input.text)
        if current_page < self.total_pages:
            self.load_page(current_page + 1)

    def decrement_page(self, instance):
        current_page = int(self.current_page_input.text)
        if current_page > 1:
            self.load_page(current_page - 1)

    def increase_zoom(self, instance):
        self.set_zoom(self.zoom_value + 0.25)

    def decrease_zoom(self, instance):
        self.set_zoom(self.zoom_value - 0.25)

    def set_zoom(self, value):
        self.zoom_value = max(0.25, value)  # Ensuring zoom doesn't go below 0.25 (25%)
        self.zoom_label.text = f'Zoom: {int(self.zoom_value * 100)}%'
        if self.pdf_path:
            self.load_page(int(self.current_page_input.text))

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
            self.pdf_path = pdf_path
            self.total_pages = get_total_pages(pdf_path)
            self.page_slider.max = self.total_pages
            self.total_pages_label.text = f'/ {self.total_pages}'
            self.file_label.text = os.path.basename(pdf_path)
            self.load_page(1)
            # Initialize increment/decrement button states
            self.page_dec_button.disabled = True
            self.page_inc_button.disabled = (self.total_pages == 1)
        except Exception as e:
            print(f"Error loading PDF: {str(e)}")
            import traceback
            traceback.print_exc()

    def load_page(self, page_number):
        try:
            self.current_image, _ = load_pdf(self.pdf_path, page_number - 1, self.zoom_value)
            print(f"Image shape: {self.current_image.shape}")
            self.current_page_input.text = str(page_number)
            self.page_slider.value = page_number
            self.update_image_preview()
            if self.layout_data:
                self.layout_data = None
                self.update_layout_data_display()  # Clear the layout data display
                self.analyze_layout()  # Re-analyze layout if there was previous data
            
            # Update increment/decrement button states
            self.page_dec_button.disabled = (page_number == 1)
            self.page_inc_button.disabled = (page_number == self.total_pages)
        except Exception as e:
            print(f"Error loading page: {str(e)}")
            import traceback
            traceback.print_exc()


    def on_window_resize(self, instance, width, height):
        # This method will be called whenever the window size changes
        self.width = width
        self.height = height
        # Ensure the right pane maintains its width
        self.children[0].width = 400  # Adjust this value as needed

    def on_page_input(self, instance):
        try:
            page = int(instance.text)
            if 1 <= page <= self.total_pages:
                self.load_page(page)
            else:
                instance.text = str(int(self.page_slider.value))
        except ValueError:
            instance.text = str(int(self.page_slider.value))

    def on_page_slider(self, instance, value):
        page = int(value)
        if page != int(self.current_page_input.text):
            self.load_page(page)

    def on_preprocess_change(self, instance, value):
        if self.current_image is not None:
            self.update_image_preview()

    def on_relationship_change(self, instance, value):
        if self.layout_data:
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
            'text_block': (0, 128, 0),  # Dark Green
            'short_text': (0, 192, 0),  # Light Green
            'image': (128, 0, 0),      # Dark Blue
            'table': (0, 0, 128),      # Dark Red
            'line': (128, 128, 0),     # Dark Cyan
            'unknown': (64, 64, 64)    # Dark Gray
        }


        for element in elements:
            x, y, w, h = element.bbox
            color = colors.get(element.type, (64, 64, 64))
            # Draw filled rectangle for better visibility
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 2)
            # Draw filled rectangle for the label background
            cv2.rectangle(overlay, (x, y - 20), (x + len(element.type) * 8, y), color, -1)
            # White text on color background
            cv2.putText(overlay, element.type, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Draw lines for relationships only if checkbox is checked
        if self.relationship_checkbox.active:
            for i, j, relationship in relationships:
                elem1 = elements[i]
                elem2 = elements[j]
                x1, y1, w1, h1 = elem1.bbox
                x2, y2, w2, h2 = elem2.bbox
                start = (x1 + w1 // 2, y1 + h1 // 2)
                end = (x2 + w2 // 2, y2 + h2 // 2)
                cv2.line(overlay, start, end, (128, 0, 128), 1)  # Dark Magenta

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
            
            if self.relationship_checkbox.active:
                display_text += "\nRelationships:\n"
                for i, j, rel in relationships:
                    display_text += f"Element {i} is {rel} Element {j}\n"
            else:
                display_text += "\nRelationships are hidden. Check 'Show Relationships' to view.\n"
            
            self.layout_data_display.content.text = display_text
        else:
            self.layout_data_display.content.text = "No layout data available"


class PDFAnalyzerApp(App):
    def build(self):
        return PDFAnalyzerGUI()

if __name__ == '__main__':
    PDFAnalyzerApp().run()

