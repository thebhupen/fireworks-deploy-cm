# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import base64
import io

from pypdf import PdfReader

from are.simulation.apps import SandboxLocalFileSystem

# File attachment validation constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per file
MAX_TOTAL_SIZE = 20 * 1024 * 1024  # 20MB total per message


def validate_attachment_sizes(attachments: list[tuple[str, str]] | None) -> None:
    """
    Validate file attachment sizes for uploads.

    Args:
        attachments: List of (file_name, base64_data) tuples

    Raises:
        ValueError: If any file exceeds size limits
    """
    if not attachments:
        return

    total_size = 0
    for file_name, base64_data in attachments:
        if not base64_data:
            continue

        # Calculate file size from base64 data
        # Base64 encoding increases size by ~33%, so original size = encoded_size * 3/4
        original_size = len(base64_data) * 3 // 4
        total_size += original_size

        # Check individual file size
        if original_size > MAX_FILE_SIZE:
            raise ValueError(
                f"File '{file_name}' is too large ({original_size / (1024 * 1024):.1f}MB). Maximum file size is {MAX_FILE_SIZE}MB."
            )

    # Check total size
    if total_size > MAX_TOTAL_SIZE:
        raise ValueError(
            f"Total attachment size is too large ({total_size / (1024 * 1024):.1f}MB). Maximum total size is {MAX_TOTAL_SIZE}MB."
        )


def file_contents_txt(
    fs: SandboxLocalFileSystem, file_path: str, max_size: int = 100000
):
    try:
        return fs.get_file_content(file_path).decode("utf-8")[:max_size]
    except Exception as e:
        return f"Failed to read file {file_path}: {e}"


def file_contents_pdf(
    fs: SandboxLocalFileSystem, file_path: str, max_size: int = 100000
):
    try:
        pdf_binary_data = fs.get_file_content(file_path)
        binary_stream = io.BytesIO(pdf_binary_data)
        reader = PdfReader(binary_stream)
        all_text = ""
        for i, page in enumerate(reader.pages):
            all_text += f"\n################# PAGE {i} #################\n\n\n"
            all_text += page.extract_text()
            if len(all_text) > max_size:
                break
        return all_text
    except Exception as e:
        return f"Failed to read file {file_path}: {e}"


def file_contents_img(
    fs: SandboxLocalFileSystem, file_path: str, max_size: int = 100000
):
    try:
        image_data = fs.get_file_content(file_path)
        return base64.b64encode(image_data).decode("utf-8")
    except Exception as e:
        return f"Failed to read file {file_path}: {e}"
