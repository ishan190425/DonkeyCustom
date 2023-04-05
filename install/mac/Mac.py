import pygame
from Miniconda import Miniconda
# Checkbox class

black = (0, 0, 0)
white = (255, 255, 255)
light_blue = (51,153,255)

class Checkbox:
    def __init__(self, x, y, size, text, checked=False):
        self.x = x
        self.y = y
        self.size = size
        self.text = text
        self.checked = checked
        self.rect = None
        

    def draw(self, window):
        # Draw text
        label = font.render(self.text, 1, black)
        window.blit(label, (self.x + self.size + 10, self.y - 10))

        # Draw checkbox
        self.rect = pygame.draw.rect(
            window, black, (self.x, self.y, self.size, self.size), 1)
        if self.checked:
            pygame.draw.line(window, black, (self.x, self.y),
                             (self.x + self.size, self.y + self.size), 1)
            pygame.draw.line(window, black, (self.x + self.size,
                             self.y), (self.x, self.y + self.size), 1)

    def collidepoint(self,x_y):
        if self.rect.collidepoint(x_y):
            self.checked = not self.checked

    def ischecked(self):
        return self.checked

# Initialize Pygame
pygame.init()

# Set screen size
screen = pygame.display.set_mode((500, 500))

# Set title
pygame.display.set_caption("Donkey Car Installer")

# Define button color
button_color = light_blue

# Define button dimensions
button_width = 200
button_height = 50

# Create button surface
button = pygame.Surface((button_width, button_height))
button.fill(button_color)

# Create button rect
button_rect = button.get_rect(center=(250, 250))

# Define font
font = pygame.font.Font("install/Montserrat-Regular.ttf", 30)

# Create button text
button_text = font.render("Install", True, (255,255,255))

# Get text rect
text_rect = button_text.get_rect(
    center=(button_rect.centerx, button_rect.centery))


# Initialize progress bar
progress = 0

# Create checkboxes
nvidia_gpu_checkbox = Checkbox(text_rect.x - 50, text_rect.y - 80, 20, "Nvidia GPU")
miniconda_checkbox = Checkbox(text_rect.x - 50, text_rect.y - 40, 20, "Miniconda")
apple_silicon = Checkbox(text_rect.x - 50, text_rect.y - 120, 20, "Apple Silicon")


# Start event loop
running = True
start = False
state = -1
currentText = ""
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Check if mouse button is pressed
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if button is clicked
            if button_rect.collidepoint(event.pos):
                # Start progress
                start = True
                state = 0
            nvidia_gpu_checkbox.collidepoint(event.pos)
            miniconda_checkbox.collidepoint(event.pos)
            apple_silicon.collidepoint(event.pos)

    # Clear screen
    screen.fill(white)

    # Draw button
    screen.blit(button, button_rect)

    # Draw text
    screen.blit(button_text, text_rect)
    
    nvidia_gpu_checkbox.draw(screen)
    miniconda_checkbox.draw(screen)
    apple_silicon.draw(screen)
    
    if state == 0:
        currentText = "Instaling Miniconda"
        if miniconda_checkbox.ischecked():
            state = 1
        else:
            miniconda = Miniconda()
            return_code = miniconda.install()
            if return_code == 0:
                state = 1
    if state == 1:
        currentText = "Creating Directory"
    elif state == 2:
        currentText = "Downloading Git - Stable"
    elif state == 3:
        currentText = "Creating Python Enviorment"
    elif state == 4:
        currentText = "Creating DonkeyCar"
    
    
    if start:
        # Clear screen
        screen.fill(white)
        progress += .01
        # Draw progress bar
        state_text = font.render(currentText, True, (0,0,0))
        screen.blit(state_text, pygame.rect.Rect(
            (110,text_rect.y - 50,100, 350)))
        pygame.draw.rect(screen, (0, 128, 0), (100, text_rect.y, min(progress,1) * 300, 50))

    # Update screen
    pygame.display.update()

# Quit Pygame
pygame.quit()
