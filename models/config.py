from dataclasses import dataclass
from typing import Optional

from better_proxy import Proxy
from pydantic import BaseModel, Field, ConfigDict, validator


@dataclass
class Account:
    pk_or_mnemonic: str
    proxy: Optional[Proxy] = None
    auth_token: Optional[str] = None
    referral_codes: list[tuple[str, int]] | None = None
    referral_private_keys: list[str] | None = None
    token_discord: Optional[str] = None

class DelayRange(BaseModel):
    min: int
    max: int

    @validator('max')
    def max_greater_than_min(cls, v, values):
        if 'min' in values and v < values['min']:
            raise ValueError('max must be greater than min')
        return v


class Token(BaseModel):
    name: str
    address: str


class ActivePair(BaseModel):
    input: str
    output: str


class Config(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="forbid"
    )

    accounts: list[Account] = Field(default_factory=list)
    cap_monster: str = ""
    two_captcha: str = ""
    capsolver: str = ""
    somnia_rpc: str = ""
    referral_code: str = ""
    tokens: list[Token] = Field(default_factory=list)
    delay_before_start: DelayRange
    threads: int
    module: str = ""