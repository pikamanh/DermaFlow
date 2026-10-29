from types import SimpleNamespace


class FakeLLMClient:
    """Giả lập OpenAI client: ghi lại messages đã gửi và trả lời theo thứ tự."""

    def __init__(self, answers=None, fail=False):
        self.calls: list[list[dict]] = []
        self.answers = list(answers or [])
        self.fail = fail
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, model, messages):
        self.calls.append(messages)

        if self.fail:
            raise RuntimeError("LLM down")

        answer = self.answers.pop(0) if self.answers else f"answer {len(self.calls)}"
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=answer))])
