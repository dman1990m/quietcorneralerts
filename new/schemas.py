from typing import Any, Dict, List, Optional, Union

import pydantic


class CadSchema(pydantic.BaseModel):
    test: str

'''
class UserSchema(pydantic.BaseModel):
    email: str
    password: str
    password2: str
    salt: str
    permission: str
    name: str
    dispatcher: str
    lastconnection: str
'''