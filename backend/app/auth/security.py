from passlib.context import CryptContext

"""
Use PBKDF2-SHA256 for password hashing.
This avoids bcrypt's 72-byte limitation and backend issues,
while still providing strong, salted hashes for this project.
"""
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)
