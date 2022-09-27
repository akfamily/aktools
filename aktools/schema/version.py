from pydantic import BaseModel


class VersionBase(BaseModel):
    ak_current_version: str = "1.7.30"
    ak_latest_version: str = "1.7.30"
    at_current_version: str = "0.0.75"
    at_latest_version: str = "0.0.75"
