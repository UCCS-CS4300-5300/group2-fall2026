"""
HW1 Part 1 — Python Foundations

Complete each function below. Read the docstring, then inspect the tests.
Run pytest frequently and read failures before changing code.
"""


def normalize_tag(tag):
    """Strip whitespace, lowercase, and replace internal spaces with hyphens."""
    # TODO
    raise NotImplementedError


def calculate_priority(importance, urgency):
    """Return importance * urgency; both inputs must be integers from 1 through 5."""
    # TODO
    raise NotImplementedError


def filter_active_items(items):
    """Return only dictionaries whose 'active' value is True; do not modify items."""
    # TODO
    raise NotImplementedError


def summarize_minutes(sessions):
    """Return the total 'minutes' across a list of session dictionaries."""
    # TODO
    raise NotImplementedError


class StudyGoal:
    def __init__(self, name, target_minutes):
        self.name = name
        self.target_minutes = target_minutes
        self.completed_minutes = 0

    def log_minutes(self, minutes):
        """Add positive minutes; raise ValueError for zero or negative input."""
        # TODO
        raise NotImplementedError

    def is_complete(self):
        """Return True when completed_minutes has reached target_minutes."""
        # TODO
        raise NotImplementedError
