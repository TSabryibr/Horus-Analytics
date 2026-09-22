import os

path = r'c:\Users\TSabr\Horus\Horus-Analytics-II\routes\signals.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''class SignalDeskPromotionRequest(BaseModel):
    lane: str = Field(..., min_length=3, max_length=32)
    ticker: str = Field(..., min_length=1, max_length=32)
    side: str = Field(default="BUY", min_length=3, max_length=8)
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    target_price: float = Field(..., gt=0)
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    score: float = Field(default=0.0, ge=0.0)
    horizon_days: Optional[int] = Field(default=None, ge=1, le=365)
    source_module: Optional[str] = None
    rationale: Optional[dict] = None'''

replacement = '''class SignalDeskPromotionRequest(BaseModel):
    lane: str = Field(..., min_length=3, max_length=32)
    ticker: str = Field(..., min_length=1, max_length=32)
    side: str = Field(default="BUY", min_length=3, max_length=8)
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    target_price: float = Field(..., gt=0)
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    score: float = Field(default=0.0, ge=0.0)
    horizon_days: Optional[int] = Field(default=None, ge=1, le=365)
    source_module: Optional[str] = None
    rationale: Optional[dict] = None

    @model_validator(mode='after')
    def validate_price_levels(self):
        side_upper = self.side.upper()
        if side_upper == 'BUY':
            if not (self.stop_loss < self.entry_price < self.target_price):
                raise ValueError('For BUY signals, prices must be: stop_loss < entry_price < target_price')
        elif side_upper == 'SELL':
            if not (self.stop_loss > self.entry_price > self.target_price):
                raise ValueError('For SELL signals, prices must be: stop_loss > entry_price > target_price')
        return self'''

if target in content:
    content = content.replace(target, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced successfully')
else:
    print('Target not found')
