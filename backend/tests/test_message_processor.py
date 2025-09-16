from types import SimpleNamespace

from backend.services.message_processor import MessageProcessor


class DummyFileClient:
    def __init__(self):
        self.calls = []

    def get(self, file_id):
        self.calls.append(file_id)
        return SimpleNamespace(filename=f"{file_id}.pdf")


class DummyProjectClient:
    def __init__(self):
        self.agents = SimpleNamespace(files=DummyFileClient())


def build_message(content_value="hello world", include_annotations=True):
    text_item = SimpleNamespace(text=SimpleNamespace(value=content_value))
    message = SimpleNamespace(
        content=[text_item],
        role="assistant",
        id="msg-1",
        created_at=123,
    )
    if include_annotations:
        file_annotation = SimpleNamespace(
            text="file text",
            start_index=0,
            end_index=4,
            file_citation=SimpleNamespace(file_id="file-1", quote="quote"),
        )
        url_annotation = SimpleNamespace(
            text="url text",
            start_index=5,
            end_index=8,
            url_citation=SimpleNamespace(url="https://example.com", title="Example"),
        )
        message.file_citation_annotations = [file_annotation]
        message.url_citation_annotations = [url_annotation]
    else:
        message.file_citation_annotations = []
        message.url_citation_annotations = []
    return message


def test_extract_message_with_annotations_collects_details():
    processor = MessageProcessor(DummyProjectClient())
    message = build_message()

    result = processor.extract_message_with_annotations(message)
    assert result["content"] == "hello world"
    assert len(result["annotations"]) == 2
    file_annotation = result["annotations"][0]
    assert file_annotation["type"] == "file_citation"
    assert file_annotation["file_name"] == "file-1.pdf"
    url_annotation = result["annotations"][1]
    assert url_annotation["url"] == "https://example.com"


def test_extract_message_with_annotations_no_content():
    processor = MessageProcessor(DummyProjectClient())
    message = build_message(include_annotations=False)
    message.content = []

    result = processor.extract_message_with_annotations(message)
    assert result["content"] == ""
    assert result["annotations"] == []


def test_format_thread_messages_reverses_order():
    processor = MessageProcessor(DummyProjectClient())
    messages = [
        build_message(content_value="first"),
        build_message(content_value="second"),
    ]

    formatted = processor.format_thread_messages(messages, "thread-1")
    assert [msg["content"] for msg in formatted] == ["second", "first"]
    assert all(msg["thread_id"] == "thread-1" for msg in formatted)
