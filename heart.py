import vtk
import numpy as np

# Load the heart model
importer = vtk.vtkOBJImporter()
importer.SetFileName("models/heart.obj")
importer.SetFileNameMTL("models/heart.mtl")
importer.Update()

# Check if actors were loaded
actors = importer.GetRenderer().GetActors()
num_actors = actors.GetNumberOfItems()

# Create a new renderer
renderer = vtk.vtkRenderer()
renderer.SetBackground(0.1, 0.2, 0.4)  # Dark blue background

# Size control: Adjust base scale of the heart
BASE_SCALE = 10.0  # Increase (>10) for larger heart, decrease (<10) for smaller

# Add all actors and set initial properties
actor_list = []
actors.InitTraversal()
for i in range(num_actors):
    actor = actors.GetNextActor()
    if actor is None:
        continue
    renderer.AddActor(actor)
    bounds = actor.GetBounds()
    actor.SetPosition(0, 0, 0)  # Center all actors
    actor.SetScale(BASE_SCALE, BASE_SCALE, BASE_SCALE)  # Apply base scale
    actor_list.append(actor)

# Add lighting
light = vtk.vtkLight()
light.SetPosition(10, 10, 10)
light.SetFocalPoint(0, 0, 0)
light.SetIntensity(1.0)
renderer.AddLight(light)

# Create text annotations for ECG phases
text_actor = vtk.vtkTextActor()
text_actor.GetTextProperty().SetFontSize(36)
text_actor.GetTextProperty().SetColor(1.0, 1.0, 1.0)
text_actor.SetPosition(20, 20)
renderer.AddActor2D(text_actor)

# Create render window
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)
render_window.SetSize(800, 600)

# Create interactor
render_window_interactor = vtk.vtkRenderWindowInteractor()
render_window_interactor.SetRenderWindow(render_window)

# Initialize interactor before setting timer
render_window_interactor.Initialize()

# Speed control: Adjust for ~70 BPM (0.857s per beat)
P_WAVE_DURATION = 0.143  # ~1/6 of cycle
QRS_DURATION = 0.286     # ~2/6 of cycle
T_WAVE_DURATION = 0.429  # ~3/6 of cycle
NUM_STEPS = 5            # Number of steps per phase (smoothness)
TIMER_INTERVAL_MS = 20   # Timer interval in milliseconds (smaller = smoother)

# Animation amplitude: Adjust scaling range relative to BASE_SCALE
SCALE_MIN = 0.95 * BASE_SCALE  # Minimum scale (e.g., 95% of base)
SCALE_MAX = 1.05 * BASE_SCALE  # Maximum scale (e.g., 105% of base)

# Define ECG timing with smooth transitions
ecg_timing = [
    ("P", P_WAVE_DURATION, np.linspace(BASE_SCALE, SCALE_MAX, NUM_STEPS)),
    ("QRS", QRS_DURATION, np.linspace(SCALE_MAX, SCALE_MIN, NUM_STEPS)),
    ("T", T_WAVE_DURATION, np.linspace(SCALE_MIN, SCALE_MAX * 0.8, NUM_STEPS))
]

# Timer callback for animation
class AnimationCallback:
    def __init__(self, actors, text_actor, render_window):
        self.actors = actors
        self.text_actor = text_actor
        self.render_window = render_window
        self.ecg_timing = ecg_timing
        self.current_beat = 0
        self.phase_index = 0
        self.scale_index = 0
        self.max_beats = float('inf')  # Set to float('inf') for continuous animation

    def __call__(self, caller, event):
        if self.current_beat >= self.max_beats:
            caller.RemoveObserver(self.timer_id)
            print("Timer animation completed.")
            return

        phase, duration, scale_factors = self.ecg_timing[self.phase_index]
        self.text_actor.SetInput(phase)
        scale_factor = scale_factors[self.scale_index]
        for actor in self.actors:
            actor.SetScale(scale_factor, scale_factor, scale_factor)
        self.render_window.Render()

        self.scale_index += 1
        if self.scale_index >= len(scale_factors):
            self.scale_index = 0
            self.phase_index += 1
            if self.phase_index >= len(self.ecg_timing):
                self.phase_index = 0
                self.current_beat += 1

# Set up the animation
callback = AnimationCallback(actor_list, text_actor, render_window)
render_window_interactor.AddObserver("TimerEvent", callback)
callback.timer_id = render_window_interactor.CreateRepeatingTimer(TIMER_INTERVAL_MS)

# Reset camera and adjust clipping range
renderer.ResetCamera()
camera = renderer.GetActiveCamera()
camera.SetClippingRange(0.1, 1000)

# Render and start interaction
render_window.Render()
render_window_interactor.Start()