from django.db import models

class Product(models.Model):
    category = models.CharField(max_length=50)
    model = models.CharField(max_length=100, unique=True)
    price = models.FloatField()

    # Optional fields
    processor = models.CharField(max_length=100, null=True, blank=True)
    memory = models.CharField(max_length=100, null=True, blank=True)
    storage = models.CharField(max_length=100, null=True, blank=True)
    display = models.CharField(max_length=100, null=True, blank=True)
    graphics = models.CharField(max_length=100, null=True, blank=True)
    cooling = models.CharField(max_length=100, null=True, blank=True)
    cooling_type = models.CharField(max_length=100, null=True, blank=True)
    display_type = models.CharField(max_length=100, null=True, blank=True)
    resolution = models.CharField(max_length=100, null=True, blank=True)
    refresh_rate = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    connectivity = models.CharField(max_length=200, null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    switch_type = models.CharField(max_length=100, null=True, blank=True)
    lighting = models.CharField(max_length=100, null=True, blank=True)
    sensor_type = models.CharField(max_length=100, null=True, blank=True)
    dpi = models.CharField(max_length=50, null=True, blank=True)
    buttons = models.CharField(max_length=100, null=True, blank=True)
    chipset = models.CharField(max_length=100, null=True, blank=True)
    capacity = models.CharField(max_length=50, null=True, blank=True)
    read_speed = models.CharField(max_length=50, null=True, blank=True)
    write_speed = models.CharField(max_length=50, null=True, blank=True)
    speed = models.CharField(max_length=50, null=True, blank=True)
    features = models.CharField(max_length=200, null=True, blank=True)
    ports = models.CharField(max_length=50, null=True, blank=True)
    compatibility = models.CharField(max_length=200, null=True, blank=True)
    length = models.CharField(max_length=50, null=True, blank=True)
    
    stripe_price_id = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"{self.category} - {self.model}"
# agent/models.py
from django.db import models

class ChatMessage(models.Model):
    session_id = models.CharField(max_length=100)
    sender = models.CharField(max_length=20)  # 'user' or 'agent'
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.sender}: {self.message}"
