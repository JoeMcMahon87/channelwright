"""Data models for ChannelWright bot."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ChannelTemplate(BaseModel):
    """Template for creating a channel."""
    name: str
    type: str = Field(..., regex="^(text|voice|forum)$")
    private: bool = False
    description: Optional[str] = None


class CampaignTemplate(BaseModel):
    """Template for creating a campaign with channels."""
    channels: List[ChannelTemplate]


class Campaign(BaseModel):
    """Campaign data model."""
    guild_id: str
    campaign_name: str
    category_id: str
    role_id: str
    channels: List[Dict[str, str]]  # List of {name, id, type}
    created_by: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    template_used: str = "default_template"


class BotConfig(BaseModel):
    """Bot configuration model."""
    config_key: str
    config_value: Dict
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
