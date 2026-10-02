import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://incident_commander:incident_commander@postgres:5432/incident_commander",
)
