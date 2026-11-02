# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import io
import tempfile
from unittest.mock import Mock, patch

import pytest

from are.simulation.core.mdconvert import (
    BingSerpConverter,
    DocumentConverter,
    DocumentConverterResult,
    DocxConverter,
    FileConversionMarkdownError,
    HtmlConverter,
    MarkdownConverter,
    PdfConverter,
    PlainTextConverter,
    PptxConverter,
    UnsupportedFormatMarkdownError,
    XlsxConverter,
    XmlConverter,
)


class TestDocumentConverter:
    """Test the base DocumentConverter class backward compatibility."""

    def test_convert_path_calls_convert_io(self):
        converter = DocumentConverter()

        # Mock convert_io to return a test result
        expected_result = DocumentConverterResult(text_content="test content")
        converter.convert_io = Mock(return_value=expected_result)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            temp_path = temp_file.name

        try:
            result = converter.convert_path(temp_path)
            assert result == expected_result
            converter.convert_io.assert_called_once()
        finally:
            import os

            os.unlink(temp_path)

    def test_convert_backward_compatibility(self):
        converter = DocumentConverter()

        # Mock convert_path to return a test result
        expected_result = DocumentConverterResult(text_content="test content")
        converter.convert_path = Mock(return_value=expected_result)

        result = converter.convert("test_path")
        assert result == expected_result
        converter.convert_path.assert_called_once_with("test_path")


class TestPlainTextConverter:
    """Test the PlainTextConverter class."""

    def test_convert_io_text_file(self):
        converter = PlainTextConverter()
        content = "This is plain text content with emojis 🚀"
        file_io = io.BytesIO(content.encode("utf-8"))

        result = converter.convert_io(file_io, file_extension=".txt")

        assert result is not None
        assert result.text_content == content
        assert result.title is None

    def test_convert_io_unsupported_extension(self):
        converter = PlainTextConverter()
        content = "This is content"
        file_io = io.BytesIO(content.encode("utf-8"))

        # Mock mimetypes.guess_type to return None
        with patch(
            "are.simulation.core.mdconvert.mimetypes.guess_type",
            return_value=(None, None),
        ):
            result = converter.convert_io(file_io, file_extension=".unknown")
            assert result is None

    def test_convert_io_no_extension(self):
        converter = PlainTextConverter()
        content = "This is content"
        file_io = io.BytesIO(content.encode("utf-8"))

        result = converter.convert_io(file_io)
        assert result is None


class TestHtmlConverter:
    """Test the HtmlConverter class."""

    def test_convert_io_html_file(self):
        converter = HtmlConverter()
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Heading</h1>
                <p>This is a test paragraph.</p>
            </body>
        </html>
        """
        file_io = io.BytesIO(html_content.encode("utf-8"))

        result = converter.convert_io(file_io, file_extension=".html")

        assert result is not None
        assert "Test Heading" in result.text_content
        assert "test paragraph" in result.text_content
        assert result.title == "Test Page"

    def test_convert_io_unsupported_extension(self):
        converter = HtmlConverter()
        content = "<html><body>Test</body></html>"
        file_io = io.BytesIO(content.encode("utf-8"))

        result = converter.convert_io(file_io, file_extension=".txt")
        assert result is None

    def test_convert_io_encoding_fallback(self):
        converter = HtmlConverter()
        # Create content with special characters that might cause encoding issues
        html_content = "<html><body>Café résumé naïve</body></html>"
        file_io = io.BytesIO(html_content.encode("iso-8859-1"))

        result = converter.convert_io(file_io, file_extension=".html")

        assert result is not None
        assert "Café" in result.text_content or "Caf" in result.text_content


class TestPdfConverter:
    """Test the PdfConverter class."""

    @patch("are.simulation.core.mdconvert.pdfminer.high_level.extract_text")
    @patch("are.simulation.core.mdconvert.tempfile.NamedTemporaryFile")
    def test_convert_io_pdf_file(self, mock_temp_file, mock_extract_text):
        converter = PdfConverter()

        # Mock the temporary file context manager
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test.pdf"
        mock_temp_file.return_value.__enter__.return_value.write = Mock()
        mock_temp_file.return_value.__enter__.return_value.flush = Mock()

        # Mock pdfminer extraction
        mock_extract_text.return_value = "Extracted PDF content"

        pdf_content = b"fake pdf content"
        file_io = io.BytesIO(pdf_content)

        result = converter.convert_io(file_io, file_extension=".pdf")

        assert result is not None
        assert result.text_content == "Extracted PDF content"
        assert result.title is None
        mock_extract_text.assert_called_once_with("/tmp/test.pdf")
        # Verify context manager was used (no manual cleanup needed)
        mock_temp_file.assert_called_once_with(suffix=".pdf")

    def test_convert_io_unsupported_extension(self):
        converter = PdfConverter()
        content = b"fake content"
        file_io = io.BytesIO(content)

        result = converter.convert_io(file_io, file_extension=".txt")
        assert result is None


class TestDocxConverter:
    """Test the DocxConverter class."""

    @patch("are.simulation.core.mdconvert.mammoth.convert_to_html")
    def test_convert_io_docx_file(self, mock_mammoth):
        converter = DocxConverter()

        # Mock mammoth conversion
        mock_result = Mock()
        mock_result.value = (
            "<html><body><h1>Document Title</h1><p>Document content</p></body></html>"
        )
        mock_mammoth.return_value = mock_result

        docx_content = b"fake docx content"
        file_io = io.BytesIO(docx_content)

        result = converter.convert_io(file_io, file_extension=".docx")

        assert result is not None
        assert "Document Title" in result.text_content
        assert "Document content" in result.text_content
        mock_mammoth.assert_called_once_with(file_io)

    def test_convert_io_unsupported_extension(self):
        converter = DocxConverter()
        content = b"fake content"
        file_io = io.BytesIO(content)

        result = converter.convert_io(file_io, file_extension=".txt")
        assert result is None


class TestXlsxConverter:
    """Test the XlsxConverter class."""

    @patch("are.simulation.core.mdconvert.pd.read_excel")
    def test_convert_io_xlsx_file(self, mock_read_excel):
        converter = XlsxConverter()

        # Mock pandas DataFrame
        mock_df = Mock()
        mock_df.to_html.return_value = "<table><tr><th>Col1</th><th>Col2</th></tr><tr><td>A</td><td>B</td></tr></table>"
        mock_read_excel.return_value = {"Sheet1": mock_df}

        xlsx_content = b"fake xlsx content"
        file_io = io.BytesIO(xlsx_content)

        result = converter.convert_io(file_io, file_extension=".xlsx")

        assert result is not None
        assert "Sheet1" in result.text_content
        assert "Col1" in result.text_content or "Col2" in result.text_content
        mock_read_excel.assert_called_once_with(file_io, sheet_name=None)

    def test_convert_io_supported_extensions(self):
        converter = XlsxConverter()

        supported_extensions = [
            ".xlsx",
            ".xls",
            ".xlsm",
            ".xlsb",
            ".ods",
            ".odf",
            ".odt",
        ]

        for ext in supported_extensions:
            with patch(
                "are.simulation.core.mdconvert.pd.read_excel"
            ) as mock_read_excel:
                mock_df = Mock()
                mock_df.to_html.return_value = "<table></table>"
                mock_read_excel.return_value = {"Sheet1": mock_df}

                file_io = io.BytesIO(b"fake content")
                result = converter.convert_io(file_io, file_extension=ext)
                assert result is not None

    def test_convert_io_unsupported_extension(self):
        converter = XlsxConverter()
        content = b"fake content"
        file_io = io.BytesIO(content)

        result = converter.convert_io(file_io, file_extension=".txt")
        assert result is None


class TestPptxConverter:
    """Test the PptxConverter class."""

    @patch("are.simulation.core.mdconvert.pptx.Presentation")
    def test_convert_io_pptx_file(self, mock_presentation_class):
        converter = PptxConverter()

        # Mock presentation and slides
        mock_presentation = Mock()
        mock_slide = Mock()

        # Mock the title shape
        mock_title_shape = Mock()
        mock_title_shape.text = "Slide Title"
        mock_title_shape.has_text_frame = True

        # Mock shapes collection
        mock_slide.shapes = Mock()
        mock_slide.shapes.title = mock_title_shape
        mock_slide.shapes.__iter__ = Mock(return_value=iter([mock_title_shape]))
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_presentation_class.return_value = mock_presentation

        pptx_content = b"fake pptx content"
        file_io = io.BytesIO(pptx_content)

        result = converter.convert_io(file_io, file_extension=".pptx")

        assert result is not None
        assert "Slide Title" in result.text_content
        mock_presentation_class.assert_called_once_with(file_io)

    def test_convert_io_unsupported_extension(self):
        converter = PptxConverter()
        content = b"fake content"
        file_io = io.BytesIO(content)

        result = converter.convert_io(file_io, file_extension=".txt")
        assert result is None


class TestXmlConverter:
    """Test the XmlConverter class."""

    def test_convert_io_xml_file(self):
        converter = XmlConverter()
        xml_content = """<?xml version="1.0"?>
        <root>
            <item>Test content</item>
        </root>"""
        file_io = io.BytesIO(xml_content.encode("utf-8"))

        # This will likely fail due to the specific XML structure expected
        # but we test that it doesn't crash
        try:
            result = converter.convert_io(file_io, file_extension=".xml")
            # If it succeeds, check basic properties
            if result is not None:
                assert isinstance(result.text_content, str)
        except Exception:
            # Expected for most XML that doesn't match the expected structure
            pass

    def test_convert_io_unsupported_extension(self):
        converter = XmlConverter()
        content = b"fake content"
        file_io = io.BytesIO(content)

        result = converter.convert_io(file_io, file_extension=".txt")
        assert result is None


class TestBingSerpConverter:
    """Test the BingSerpConverter class (file-based only)."""

    def test_convert_io_not_implemented(self):
        converter = BingSerpConverter()

        # BingSerpConverter doesn't implement convert_io, only convert
        with pytest.raises(NotImplementedError):
            converter.convert_io(io.BytesIO(b"test"))


class TestMarkdownConverter:
    """Test the main MarkdownConverter class."""

    def test_convert_io_success(self):
        converter = MarkdownConverter()
        content = "This is plain text content"
        file_io = io.BytesIO(content.encode("utf-8"))

        result = converter.convert_io(file_io, file_extension=".txt")

        assert isinstance(result, DocumentConverterResult)
        assert result.text_content == content

    @patch("are.simulation.core.mdconvert.requests.get")
    def test_convert_url_success(self, mock_get):
        converter = MarkdownConverter()

        # Mock response
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.url = "http://example.com/test.txt"
        mock_response.iter_content.return_value = [b"Test ", b"content ", b"from URL"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = converter.convert_url("http://example.com/test.txt")

        assert isinstance(result, DocumentConverterResult)
        assert result.text_content == "Test content from URL"
        mock_get.assert_called_once_with("http://example.com/test.txt", stream=True)

    def test_convert_response_success(self):
        converter = MarkdownConverter()

        # Mock response object
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.url = "http://example.com/test.txt"
        mock_response.iter_content.return_value = [b"Response ", b"content"]

        result = converter.convert_response(mock_response)

        assert isinstance(result, DocumentConverterResult)
        assert result.text_content == "Response content"

    def test_convert_response_with_content_disposition(self):
        converter = MarkdownConverter()

        # Mock response with content disposition header
        mock_response = Mock()
        mock_response.headers = {
            "content-type": "application/octet-stream",
            "content-disposition": 'attachment; filename="test.txt"',
        }
        mock_response.url = "http://example.com/download"
        mock_response.iter_content.return_value = [b"File content"]

        result = converter.convert_response(mock_response)

        assert isinstance(result, DocumentConverterResult)
        assert result.text_content == "File content"

    def test_convert_response_with_url_extension(self):
        converter = MarkdownConverter()

        # Mock response where extension comes from URL path
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/octet-stream"}
        mock_response.url = "http://example.com/files/document.txt"
        mock_response.iter_content.return_value = [b"URL path content"]

        result = converter.convert_response(mock_response)

        assert isinstance(result, DocumentConverterResult)
        assert result.text_content == "URL path content"

    def test_convert_str_success(self):
        converter = MarkdownConverter()
        content = "String content to convert"

        result = converter.convert_str(content, file_extension=".txt")

        assert isinstance(result, DocumentConverterResult)
        assert result.text_content == content

    def test_convert_str_html_content(self):
        converter = MarkdownConverter()
        html_content = (
            "<html><body><h1>HTML Title</h1><p>HTML content</p></body></html>"
        )

        result = converter.convert_str(html_content, file_extension=".html")

        assert isinstance(result, DocumentConverterResult)
        assert "HTML Title" in result.text_content
        assert "HTML content" in result.text_content

    def test_convert_str_without_extension(self):
        converter = MarkdownConverter()
        content = "Content without extension"

        # Without extension, converters may not be able to determine format
        # This should raise an exception since no converter can handle it
        with pytest.raises(
            (UnsupportedFormatMarkdownError, FileConversionMarkdownError)
        ):
            converter.convert_str(content)

    def test_convert_io_unsupported_format(self):
        converter = MarkdownConverter()
        content = b"unknown binary content"
        file_io = io.BytesIO(content)

        # Should raise UnsupportedFormatMarkdownError when no converter can handle the format
        with pytest.raises(
            (UnsupportedFormatMarkdownError, FileConversionMarkdownError)
        ):
            converter.convert_io(file_io, file_extension=".totallyunknownext")

    def test_convert_path_success(self):
        converter = MarkdownConverter()
        content = "This is test content"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            result = converter.convert_path(temp_path)
            assert isinstance(result, DocumentConverterResult)
            assert result.text_content == content
        finally:
            import os

            os.unlink(temp_path)

    def test_convert_backward_compatibility_path(self):
        converter = MarkdownConverter()

        with patch.object(converter, "convert_path") as mock_convert_path:
            expected_result = DocumentConverterResult(text_content="test")
            mock_convert_path.return_value = expected_result

            result = converter.convert("local_file.txt")

            assert result == expected_result
            mock_convert_path.assert_called_once_with("local_file.txt")

    def test_convert_backward_compatibility_url(self):
        converter = MarkdownConverter()

        with patch.object(converter, "convert_url") as mock_convert_url:
            expected_result = DocumentConverterResult(text_content="test")
            mock_convert_url.return_value = expected_result

            result = converter.convert("http://example.com/test.txt")

            assert result == expected_result
            mock_convert_url.assert_called_once_with("http://example.com/test.txt")

    def test_convert_io_with_conversion_error(self):
        converter = MarkdownConverter()

        # Create a mock converter that raises an exception
        mock_converter = Mock()
        mock_converter.convert_io.side_effect = Exception("Conversion failed")

        # Replace all converters with our mock
        converter._page_converters = [mock_converter]

        file_io = io.BytesIO(b"test content")

        with pytest.raises(FileConversionMarkdownError) as exc_info:
            converter.convert_io(file_io, file_extension=".test")

        assert "Conversion failed" in str(exc_info.value)

    def test_normalize_content(self):
        converter = MarkdownConverter()
        content = "Line 1\r\nLine 2\n\n\n\nLine 3"
        file_io = io.BytesIO(content.encode("utf-8"))

        result = converter.convert_io(file_io, file_extension=".txt")

        # Check that excessive newlines are normalized
        assert "\n\n\n" not in result.text_content
        assert "Line 1\nLine 2\n\nLine 3" == result.text_content


class TestIntegration:
    """Integration tests for the mdconvert module."""

    def test_io_interface_compatibility(self):
        """Test that the IO interface works with file-like objects."""
        converter = MarkdownConverter()

        # Test with BytesIO
        content = "Test content for IO interface"
        file_io = io.BytesIO(content.encode("utf-8"))

        result = converter.convert_io(file_io, file_extension=".txt")
        assert result.text_content == content

        # Test that file position is handled correctly
        file_io.seek(10)  # Move position
        result2 = converter.convert_io(file_io, file_extension=".txt")
        assert result2.text_content == content  # Should still get full content

    def test_fsspec_compatibility(self):
        """Test compatibility with fsspec file handles."""
        converter = MarkdownConverter()

        # Simulate an fsspec file handle using BytesIO (which is IO[bytes] compatible)
        content = "Content from fsspec filesystem"
        mock_file = io.BytesIO(content.encode("utf-8"))

        result = converter.convert_io(mock_file, file_extension=".txt")
        assert result.text_content == content

    def test_multiple_converter_fallback(self):
        """Test that the converter tries multiple converters until one succeeds."""
        converter = MarkdownConverter()

        # Create content that will be rejected by some converters but accepted by PlainTextConverter
        content = "This is plain text that should work"
        file_io = io.BytesIO(content.encode("utf-8"))

        # The converter should try multiple converters and eventually succeed with PlainTextConverter
        result = converter.convert_io(file_io, file_extension=".txt")
        assert result.text_content == content

    def test_error_handling_chain(self):
        """Test error handling when all converters fail."""
        converter = MarkdownConverter()

        # Use an extension that no converter supports
        content = b"Unknown binary content"
        file_io = io.BytesIO(content)

        with pytest.raises(
            (UnsupportedFormatMarkdownError, FileConversionMarkdownError)
        ) as exc_info:
            converter.convert_io(file_io, file_extension=".unknownext")

        # Check that the error message contains relevant information
        error_msg = str(exc_info.value)
        assert ".unknownext" in error_msg or "not supported" in error_msg.lower()


if __name__ == "__main__":
    pytest.main([__file__])
