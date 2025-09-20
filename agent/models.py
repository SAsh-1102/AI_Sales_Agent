from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=255, unique=True)
    processor = models.CharField(max_length=255, blank=True, null=True)
    memory = models.CharField(max_length=100, blank=True, null=True)
    storage = models.CharField(max_length=100, blank=True, null=True)
    display = models.CharField(max_length=100, blank=True, null=True)
    graphics = models.CharField(max_length=255, blank=True, null=True)
    cooling = models.CharField(max_length=100, blank=True, null=True)
    display_type = models.CharField(max_length=50, blank=True, null=True)
    resolution = models.CharField(max_length=50, blank=True, null=True)
    refresh_rate = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    connectivity = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    switch_type = models.CharField(max_length=100, blank=True, null=True)
    lighting = models.CharField(max_length=100, blank=True, null=True)
    sensor_type = models.CharField(max_length=100, blank=True, null=True)
    dpi = models.CharField(max_length=50, blank=True, null=True)
    chipset = models.CharField(max_length=100, blank=True, null=True)
    capacity = models.CharField(max_length=50, blank=True, null=True)
    read_speed = models.CharField(max_length=50, blank=True, null=True)
    write_speed = models.CharField(max_length=50, blank=True, null=True)
    speed = models.CharField(max_length=50, blank=True, null=True)
    features = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    price = models.FloatField(default=0)

    def __str__(self):
        return f"{self.name} ({self.model})"

# -----------------------------
# ChatMessage Model for Memory
# -----------------------------
from django.db import models

class ChatMessage(models.Model):
    session_id = models.CharField(max_length=100, default="default")
    sender = models.CharField(max_length=50)  # "user" or "agent"
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.session_id}] {self.sender}: {self.message[:50]}"

