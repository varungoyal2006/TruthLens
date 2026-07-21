"""
Application Configuration Module 
Validates and loads enviroment variable required for the application
"""

from pydantic_settings import BaseSettings, SettingsConfigDict 

class settings(BaseSettings): 
  GROQ_API_KEY: str 
  TAVILY_API_KEY: str 
  GOOGLE_API_KEY: str 

  API_V1_STR: str = "/api/v1"
  PROJECT_NAME: str = "TruethLens API"

  model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = settings() 