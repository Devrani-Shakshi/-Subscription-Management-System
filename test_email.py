from pydantic import BaseModel, EmailStr  
class A(BaseModel):  
    e: EmailStr  
A(e='admin@subscription.local')  
