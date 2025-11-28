"""
Celtic-inspired calendar system for tracking time and date.
"""
from enum import Enum


class DayOfWeek(Enum):
    """Celtic days of the week."""
    DOMINACH = "Dominach"  # Sunday
    LUAN = "Luan"  # Monday
    MÁIRT = "Máirt"  # Tuesday
    CÉADAOIN = "Céadaoin"  # Wednesday
    ARDAOIN = "Ardaoin"  # Thursday
    AONAOIN = "Aonaoin"  # Friday
    SATHARN = "Satharn"  # Saturday


class Month(Enum):
    """Celtic months (based on seasonal markers)."""
    SAMHAIN = "Samhain"  # November (winter begins)
    NODLAIG = "Nodlaig"  # December
    EANÁIR = "Eanáir"  # January
    FEABHRA = "Feabhra"  # February
    MÁRTA = "Márta"  # March
    AIBREÁN = "Aibreán"  # April
    BEALTAINE = "Bealtaine"  # May (summer begins)
    MEITHEAMH = "Meitheamh"  # June
    IÚIL = "Iúil"  # July
    LÚNASA = "Lúnasa"  # August (harvest)
    MEÁN_FÓMHAR = "Meán Fómhar"  # September
    DEIREADH_FÓMHAR = "Deireadh Fómhar"  # October


class CelticCalendar:
    """Celtic-inspired calendar system."""
    
    # Days per month (simplified - all months have 30 days for consistency)
    DAYS_PER_MONTH = 30
    MONTHS_PER_YEAR = 12
    HOURS_PER_DAY = 24
    
    def __init__(self, year: int = 1, month: int = 1, day: int = 1, hour: int = 0):
        """
        Initialize the calendar.
        
        Args:
            year: Starting year (default 1)
            month: Starting month (1-12, default 1 = Samhain)
            day: Starting day (1-30, default 1)
            hour: Starting hour (0-23, default 0 = midnight)
        """
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
    
    def add_hours(self, hours: int):
        """Add hours to the calendar, advancing days/months/years as needed."""
        self.hour += hours
        
        # Advance days
        while self.hour >= self.HOURS_PER_DAY:
            self.hour -= self.HOURS_PER_DAY
            self.day += 1
        
        # Advance months
        while self.day > self.DAYS_PER_MONTH:
            self.day -= self.DAYS_PER_MONTH
            self.month += 1
        
        # Advance years
        while self.month > self.MONTHS_PER_YEAR:
            self.month -= self.MONTHS_PER_YEAR
            self.year += 1
    
    def get_day_of_week(self) -> DayOfWeek:
        """Calculate the day of the week based on total days elapsed."""
        # Calculate total days since start (year 1, month 1, day 1)
        total_days = (self.year - 1) * self.MONTHS_PER_YEAR * self.DAYS_PER_MONTH
        total_days += (self.month - 1) * self.DAYS_PER_MONTH
        total_days += (self.day - 1)
        
        # Day 1 is Dominach (Sunday)
        day_index = total_days % 7
        return list(DayOfWeek)[day_index]
    
    def get_month_name(self) -> str:
        """Get the name of the current month."""
        return list(Month)[self.month - 1].value
    
    def get_date_string(self) -> str:
        """Get a formatted date string."""
        day_name = self.get_day_of_week().value
        month_name = self.get_month_name()
        return f"{day_name}, {month_name} {self.day}, Year {self.year}"
    
    def get_time_string(self) -> str:
        """Get a formatted time string (24-hour format)."""
        return f"{self.hour:02d}:00"
    
    def get_full_datetime_string(self) -> str:
        """Get a formatted date and time string."""
        return f"{self.get_date_string()} - {self.get_time_string()}"


