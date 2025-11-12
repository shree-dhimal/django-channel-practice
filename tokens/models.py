from django.db import models
from datetime import date

# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(
        max_length=20,
        null=False,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, null=False)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    is_public = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_counter_queue_node = models.BooleanField(default=False, null=False)
    batch_support = models.BooleanField(default=False, null=False)
    batch_size = models.PositiveIntegerField(default=1)
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'queue_department'


class Counter(models.Model):
    class CounterStatus(models.TextChoices):
        OPEN = "Open", "Open"
        CLOSED = "Closed", "Closed"
        PAUSED = "Paused", "Paused"

    name = models.CharField(max_length=255)
    code = models.CharField(
        max_length=20,
        null=False,
        db_index=True,
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, related_name='counters')
    is_active = models.BooleanField(default=True, null=False)
    status = models.CharField(
        max_length=255, choices=CounterStatus.choices, default=CounterStatus.OPEN
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "queue_counter"


class Priority(models.Model):
    priority_type = models.CharField(
        max_length=255
    )
    priority_score = models.PositiveIntegerField(
        max_length=255, default=0
    )
    display_name = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=False)
    class Meta:
        db_table = "queue_priority"



class Tokens(models.Model):

    class Category(models.TextChoices):
        OPEN = "Open", "Open"
        CLOSED = "Closed", "Closed"
        IN_PROGRESS = "In Progress", "In Progress"

    class ResetType(models.TextChoices):
        AUTO = "Auto", "Auto"
        MANUAL = "Manual", "Manual"

    class TokenStatus(models.TextChoices):
        OPEN = "Open", "Open"
        CLOSED = "Closed", "Closed"
        CANCELED = "Canceled", "Canceled"
        NO_SHOW = "No Show", "No Show"
        IN_PROGRESS = "In Progress", "In Progress"
        RECALL = "Recall", "Recall"
    
    class TokenCreatedFor(models.TextChoices):
        Department="D"
        Counter="C"

    token_no = models.PositiveIntegerField()
    category = models.CharField(
        max_length=255, choices=Category.choices, default=Category.OPEN
    )
    priority = models.ForeignKey(Priority, on_delete=models.SET_NULL, null=True)
    reset = models.BooleanField(default=False)
    reset_type = models.CharField(
        max_length=255, choices=ResetType.choices, default=ResetType.AUTO
    )
    description = models.TextField(default="", blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=255, choices=TokenStatus.choices, default=TokenStatus.OPEN
    )
    token_for = models.CharField(
        max_length=1, choices=TokenCreatedFor.choices, default=TokenCreatedFor.Department
    )
    refered_from = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    counter = models.ForeignKey(Counter, on_delete=models.SET_NULL, null=True)
    batch_processed = models.BooleanField(default=False)
    token_created_for = models.DateField(null=True, default=date.today)

    def __int__(self):
        return self.token_no

    class Meta:
        db_table = "queue_tokens"