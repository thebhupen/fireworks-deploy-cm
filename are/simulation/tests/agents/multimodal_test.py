# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import base64
import json

import pytest

from are.simulation.agents.multimodal import Attachment


@pytest.fixture
def sample_image_data():
    """Fixture providing sample base64 encoded image data."""
    return base64.b64encode(b"sample image data")


@pytest.fixture
def image_attachment(sample_image_data):
    """Fixture providing a sample image attachment."""
    return Attachment(
        base64_data=sample_image_data, mime="image/jpeg", name="test_image.jpg"
    )


@pytest.fixture
def non_image_attachment(sample_image_data):
    """Fixture providing a sample non-image attachment."""
    return Attachment(
        base64_data=sample_image_data, mime="application/pdf", name="test_document.pdf"
    )


class TestAttachment:
    def test_init(self, sample_image_data):
        """Test that an Attachment can be initialized correctly."""
        attachment = Attachment(
            base64_data=sample_image_data, mime="image/png", name="test.png"
        )

        assert attachment.base64_data == sample_image_data
        assert attachment.mime == "image/png"
        assert attachment.name == "test.png"

    def test_init_without_name(self, sample_image_data):
        """Test that an Attachment can be initialized without a name."""
        attachment = Attachment(base64_data=sample_image_data, mime="image/png")

        assert attachment.base64_data == sample_image_data
        assert attachment.mime == "image/png"
        assert attachment.name is None

    def test_init_with_none_base64_data(self):
        """Test that an Attachment cannot be initialized with None for base64_data."""
        with pytest.raises(ValueError) as excinfo:
            Attachment(base64_data=None, mime="image/png")

        assert "base64_data cannot be null or empty" in str(excinfo.value)

    def test_init_with_empty_base64_data(self):
        """Test that an Attachment cannot be initialized with empty bytes for base64_data."""
        with pytest.raises(ValueError) as excinfo:
            Attachment(base64_data=b"", mime="image/png")

        assert "base64_data cannot be null or empty" in str(excinfo.value)

    def test_init_with_none_mime(self, sample_image_data):
        """Test that an Attachment cannot be initialized with None for mime."""
        with pytest.raises(ValueError) as excinfo:
            Attachment(base64_data=sample_image_data, mime=None)

        assert "mime cannot be null or empty" in str(excinfo.value)

    def test_init_with_empty_mime(self, sample_image_data):
        """Test that an Attachment cannot be initialized with an empty string for mime."""
        with pytest.raises(ValueError) as excinfo:
            Attachment(base64_data=sample_image_data, mime="")

        assert "mime cannot be null or empty" in str(excinfo.value)

    def test_hash(self, image_attachment, sample_image_data):
        """Test that the __hash__ method works correctly."""
        # Create an identical attachment
        identical_attachment = Attachment(
            base64_data=sample_image_data, mime="image/jpeg", name="test_image.jpg"
        )

        # Create a different attachment
        different_attachment = Attachment(
            base64_data=sample_image_data,
            mime="image/png",  # Different mime type
            name="test_image.jpg",
        )

        # Test that identical attachments have the same hash
        assert hash(image_attachment) == hash(identical_attachment)

        # Test that different attachments have different hashes
        assert hash(image_attachment) != hash(different_attachment)

        # Test that attachments can be used in sets
        attachment_set = {image_attachment, identical_attachment, different_attachment}
        assert len(attachment_set) == 2

    def test_field_validator_string_to_bytes(self):
        """Test that field_validator converts string input to bytes."""
        # Create attachment with string base64_data (should be converted to bytes)
        string_data = "dGVzdCBkYXRh"  # "test data" in base64
        attachment = Attachment(base64_data=string_data, mime="image/png")

        # Verify the data was converted to bytes
        assert isinstance(attachment.base64_data, bytes)
        assert attachment.base64_data == string_data.encode("utf-8")

    def test_field_validator_bytes_unchanged(self):
        """Test that field_validator leaves bytes input unchanged."""
        # Create attachment with bytes base64_data (should remain as bytes)
        bytes_data = b"dGVzdCBkYXRh"
        attachment = Attachment(base64_data=bytes_data, mime="image/png")

        # Verify the data remained as bytes
        assert isinstance(attachment.base64_data, bytes)
        assert attachment.base64_data == bytes_data

    def test_field_serializer_bytes_to_string(self, sample_image_data):
        """Test that field_serializer converts bytes to string for JSON serialization."""
        attachment = Attachment(base64_data=sample_image_data, mime="image/png")

        # Test direct serialization
        serialized_data = attachment.serialize_base64_data(attachment.base64_data)
        assert isinstance(serialized_data, str)
        assert serialized_data == sample_image_data.decode("utf-8")

    def test_json_serialization_deserialization(self, sample_image_data):
        """Test complete JSON serialization and deserialization cycle."""
        # Create original attachment
        original = Attachment(
            base64_data=sample_image_data, mime="image/jpeg", name="test.jpg"
        )

        # Serialize to JSON
        json_data = json.dumps(original.model_dump())

        # Deserialize from JSON
        parsed_data = json.loads(json_data)
        reconstructed = Attachment(**parsed_data)

        # Verify the reconstructed attachment matches the original
        assert reconstructed.base64_data == original.base64_data
        assert reconstructed.mime == original.mime
        assert reconstructed.name == original.name

    def test_serialization_with_string_input(self):
        """Test serialization when attachment is created with string input."""
        string_data = "dGVzdCBkYXRh"  # "test data" in base64

        # Create attachment with string input
        attachment = Attachment(base64_data=string_data, mime="image/png")

        # Serialize to JSON
        json_data = json.dumps(attachment.model_dump())
        parsed_data = json.loads(json_data)

        # Verify the serialized data is a string
        assert isinstance(parsed_data["base64_data"], str)
        assert parsed_data["base64_data"] == string_data

    def test_deserialization_with_string_data(self):
        """Test deserialization when JSON contains string base64_data."""
        json_data = {
            "base64_data": "dGVzdCBkYXRh",  # String input
            "mime": "image/png",
            "name": "test.png",
        }

        # Create attachment from dict (simulating JSON deserialization)
        attachment = Attachment(**json_data)

        # Verify the string was converted to bytes internally
        assert isinstance(attachment.base64_data, bytes)
        assert attachment.base64_data == b"dGVzdCBkYXRh"
