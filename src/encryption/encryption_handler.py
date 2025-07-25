from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
import os
import logging
from typing import Optional, Tuple
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from cryptography.hazmat.primitives.kdf.x963kdf import X963KDF
from cryptography.hazmat.primitives.kdf.kbkdf import KBKDFHMAC, Mode
import random
import string

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Key Paths
PRIVATE_KEY_PATH = "keys/private-key.pem"
PUBLIC_KEY_PATH = "keys/public-key.pem"

class EncryptionHandler:
    def __init__(self):
        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()

    def _load_private_key(self) -> Optional[rsa.RSAPrivateKey]:
        """Load the private key from file."""
        try:
            with open(PRIVATE_KEY_PATH, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
                logging.info("Private key loaded successfully.")
                return private_key
        except FileNotFoundError:
            logging.error(f"Private key file not found: {PRIVATE_KEY_PATH}")
            return None
        except Exception as e:
            logging.error(f"Error loading private key: {e}")
            return None

    def _load_public_key(self) -> Optional[rsa.RSAPublicKey]:
        """Load the public key from file."""
        try:
            with open(PUBLIC_KEY_PATH, "rb") as key_file:
                public_key = serialization.load_pem_public_key(
                    key_file.read(),
                    backend=default_backend()
                )
                logging.info("Public key loaded successfully.")
                return public_key
        except FileNotFoundError:
            logging.error(f"Public key file not found: {PUBLIC_KEY_PATH}")
            return None
        except Exception as e:
            logging.error(f"Error loading public key: {e}")
            return None

    def generate_symmetric_key(self) -> bytes:
        """Generate a random symmetric key."""
        return os.urandom(32)  # 256-bit key

    def mutate_code(self, code: str) -> str:
        """Mutate the given code to evade detection."""
        mutations = [
            lambda s: s.replace("encrypt", "enc" + ''.join(random.choices(string.ascii_letters, k=5))),
            lambda s: s.replace("decrypt", "dec" + ''.join(random.choices(string.ascii_letters, k=5))),
            lambda s: s.replace("symmetric_key", "sym_key" + ''.join(random.choices(string.ascii_letters, k=5))),
            lambda s: s.replace("iv", "init_vec" + ''.join(random.choices(string.ascii_letters, k=5))),
        ]
        for mutation in mutations:
            code = mutation(code)
        return code

    def encrypt_message(self, message: str) -> Optional[str]:
        """Encrypt a message using hybrid encryption (RSA for key, AES for data)."""
        if not self.public_key:
            logging.error("Public key not loaded. Encryption failed.")
            return None

        try:
            symmetric_key = self.generate_symmetric_key()
            iv = os.urandom(16)  # Initialization Vector for AES
            cipher = Cipher(algorithms.AES(symmetric_key), modes.CFB(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(message.encode()) + padder.finalize()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            encrypted_key = self.public_key.encrypt(
                symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            encrypted_iv = self.public_key.encrypt(
                iv,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            # Combine encrypted key, IV, and ciphertext
            combined_data = base64.b64encode(encrypted_key + encrypted_iv + ciphertext).decode()
            logging.info("Message encrypted successfully.")
            return combined_data
        except Exception as e:
            logging.error(f"Error during encryption: {e}")
            return None

    def decrypt_message(self, combined_data: str) -> Optional[str]:
        """Decrypt a message using hybrid decryption (RSA for key, AES for data)."""
        if not self.private_key:
            logging.error("Private key not loaded. Decryption failed.")
            return None

        try:
            combined_data = base64.b64decode(combined_data.encode())
            encrypted_key = combined_data[:256]
            encrypted_iv = combined_data[256:512]
            ciphertext = combined_data[512:]

            symmetric_key = self.private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            iv = self.private_key.decrypt(
                encrypted_iv,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            cipher = Cipher(algorithms.AES(symmetric_key), modes.CFB(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = sym_padding.PKCS7(algorithms.AES.block_size).unpadder()
            unpadded_plaintext = unpadder.update(plaintext) + unpadder.finalize()
            logging.info("Message decrypted successfully.")
            return unpadded_plaintext.decode()
        except Exception as e:
            logging.error(f"Error during decryption: {e}")
            return None

    def encrypt_file(self, file_path: str) -> Optional[str]:
        """Encrypt a file using hybrid encryption (RSA for key, AES for data)."""
        if not self.public_key:
            logging.error("Public key not loaded. Encryption failed.")
            return None

        try:
            with open(file_path, "rb") as file:
                file_data = file.read()

            symmetric_key = self.generate_symmetric_key()
            iv = os.urandom(16)  # Initialization Vector for AES
            cipher = Cipher(algorithms.AES(symmetric_key), modes.CFB(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            padder = sym_padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(file_data) + padder.finalize()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            encrypted_key = self.public_key.encrypt(
                symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            encrypted_iv = self.public_key.encrypt(
                iv,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            # Combine encrypted key, IV, and ciphertext
            combined_data = base64.b64encode(encrypted_key + encrypted_iv + ciphertext).decode()
            logging.info("File encrypted successfully.")
            return combined_data
        except Exception as e:
            logging.error(f"Error during file encryption: {e}")
            return None

    def decrypt_file(self, combined_data: str, output_path: str) -> bool:
        """Decrypt a file using hybrid decryption (RSA for key, AES for data)."""
        if not self.private_key:
            logging.error("Private key not loaded. Decryption failed.")
            return False

        try:
            combined_data = base64.b64decode(combined_data.encode())
            encrypted_key = combined_data[:256]
            encrypted_iv = combined_data[256:512]
            ciphertext = combined_data[512:]

            symmetric_key = self.private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            iv = self.private_key.decrypt(
                encrypted_iv,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            cipher = Cipher(algorithms.AES(symmetric_key), modes.CFB(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = sym_padding.PKCS7(algorithms.AES.block_size).unpadder()
            unpadded_plaintext = unpadder.update(plaintext) + unpadded_plaintext.finalize()

            with open(output_path, "wb") as file:
                file.write(unpadded_plaintext)

            logging.info("File decrypted successfully.")
            return True
        except Exception as e:
            logging.error(f"Error during file decryption: {e}")
            return False

    def store_encryption_key(self, key: bytes, key_path: str) -> bool:
        """Store the encryption key securely."""
        try:
            with open(key_path, "wb") as key_file:
                key_file.write(key)
            logging.info(f"Encryption key stored successfully at {key_path}.")
            return True
        except Exception as e:
            logging.error(f"Error storing encryption key: {e}")
            return False

    def load_encryption_key(self, key_path: str) -> Optional[bytes]:
        """Load the encryption key securely."""
        try:
            with open(key_path, "rb") as key_file:
                key = key_file.read()
            logging.info(f"Encryption key loaded successfully from {key_path}.")
            return key
        except Exception as e:
            logging.error(f"Error loading encryption key: {e}")
            return None

if __name__ == '__main__':
    handler = EncryptionHandler()
    message = "This is a highly sensitive message that needs to be encrypted."
    encrypted_message = handler.encrypt_message(message)
    if (encrypted_message):
        print(f"Encrypted message: {encrypted_message}")
        decrypted_message = handler.decrypt_message(encrypted_message)
        if (decrypted_message):
            print(f"Decrypted message: {decrypted_message}")

    file_path = "sensitive_file.txt"
    encrypted_file_data = handler.encrypt_file(file_path)
    if (encrypted_file_data):
        print(f"Encrypted file data: {encrypted_file_data}")
        output_path = "decrypted_file.txt"
        if (handler.decrypt_file(encrypted_file_data, output_path)):
            print(f"File decrypted successfully. Output path: {output_path}")
