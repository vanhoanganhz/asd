from typing import List, Dict, Optional
from better_proxy import Proxy
from pydantic import BaseModel, PositiveInt, validator

class Account(BaseModel):
    email: str
    password: str
    imap_server: Optional[str] = ''  # Optional field
    proxy: Proxy

    class Config:
        arbitrary_types_allowed = True


class MultipleAccount(BaseModel):
    email: str
    password: str
    imap_server: Optional[str] = ''  # Optional field
    proxies: List[Proxy]  # List of Proxy objects

    class Config:
        arbitrary_types_allowed = True


class DelayBeforeStart(BaseModel):
    min: int
    max: int

    @validator('min')
    def check_min_less_than_max(cls, v, values):
        if 'max' in values and v > values['max']:
            raise ValueError('min must be less than or equal to max')
        return v


class Config(BaseModel):
    accounts_to_register: List[Account] = []
    accounts_to_farm: List[Account] = []
    accounts_to_multiple_farm: List[MultipleAccount] = []
    accounts_to_verify: List[Account] = []
    capsolver_api_key: str
    invite_code: str
    delay_before_start: DelayBeforeStart
    threads: PositiveInt
    imap_settings: Dict[str, str]
    module: str = ''

    class Config:
        arbitrary_types_allowed = True