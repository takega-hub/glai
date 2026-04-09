
from passlib.context import CryptContext

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password = "admin123"
    hashed_password = pwd_context.hash(password)
    print("Password hashing successful.")
    print(f"Password: {password}")
    print(f"Hashed: {hashed_password}")
    is_valid = pwd_context.verify(password, hashed_password)
    print(f"Verification successful: {is_valid}")
except Exception as e:
    print("An error occurred during password hashing:")
    print(e)
    import traceback
    traceback.print_exc()
