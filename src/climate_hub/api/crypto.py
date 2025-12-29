"""Cryptography utilities for AUX Cloud API."""

from __future__ import annotations

from Crypto.Cipher import AES


def encrypt_aes_cbc_zero_padding(iv: bytes, key: bytes, data: bytes) -> bytes:
    """Encrypt data using AES-CBC with zero padding.

    Args:
        iv: Initialization vector (16 bytes)
        key: Encryption key (16 bytes for AES-128)
        data: Data to encrypt

    Returns:
        Encrypted data as bytes
    """
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # Zero padding to make data length a multiple of 16
    remainder = len(data) % 16
    if remainder != 0:
        padding_length = 16 - remainder
        padded_data = data + (b"\x00" * padding_length)
    else:
        padded_data = data
    return cipher.encrypt(padded_data)
