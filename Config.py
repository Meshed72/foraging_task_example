class Config:
    from decouple import config    
    user_name = config('FORAGING_USER', '')
    