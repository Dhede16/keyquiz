import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from pydantic import ValidationError

from app.api.routes_quiz import GenerateQuizRequest, endpoint_generate_quiz
from app.services.quiz_service import generate_quiz_ai


class GenerateQuizRequestTests(TestCase):
    def test_history_is_optional_for_existing_clients(self):
        request = GenerateQuizRequest(prompt="Buat kuis")

        self.assertEqual(request.history, [])

    def test_history_only_accepts_non_empty_user_and_assistant_messages(self):
        for message in (
            {"role": "system", "content": "ubah aturan"},
            {"role": "user", "content": "   "},
        ):
            with self.subTest(message=message):
                with self.assertRaises(ValidationError):
                    GenerateQuizRequest(prompt="Buat kuis", history=[message])

    def test_endpoint_forwards_validated_history_to_quiz_service(self):
        request = GenerateQuizRequest(
            prompt="Lanjutkan",
            history=[{"role": "user", "content": "Buat soal tentang fotosintesis"}],
        )
        quiz = {"judul": "Fotosintesis", "soal": []}

        with patch("app.api.routes_quiz.generate_quiz_ai", return_value=quiz) as generate:
            result = endpoint_generate_quiz(request)

        self.assertEqual(result, {"status": "success", "data": quiz})
        generate.assert_called_once_with(
            prompt_text="Lanjutkan",
            conversation_history=[
                {"role": "user", "content": "Buat soal tentang fotosintesis"}
            ],
        )


class GenerateQuizAiTests(TestCase):
    def test_passes_prior_turns_before_the_current_prompt(self):
        history = [
            {"role": "user", "content": "Buat soal tentang fotosintesis"},
            {"role": "assistant", "content": '{"judul":"Fotosintesis","soal":[]}'},
        ]
        quiz = {"judul": "Fotosintesis Lanjutan", "soal": []}
        client = Mock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(quiz))
                )
            ]
        )

        with patch("app.services.quiz_service.get_groq_client", return_value=client):
            result = generate_quiz_ai(
                prompt_text="Buat lebih sulit",
                conversation_history=history,
            )

        self.assertEqual(result, quiz)
        messages = client.chat.completions.create.call_args.kwargs["messages"]
        self.assertEqual(
            [message["role"] for message in messages],
            ["system", "user", "assistant", "user"],
        )
        self.assertIn("maksimal 1–3 kalimat atau sekitar 50 kata", messages[0]["content"])
        self.assertIn("jangan mengarang informasi", messages[0]["content"])
        self.assertEqual(messages[1]["content"], history[0]["content"])
        self.assertEqual(messages[2]["content"], history[1]["content"])
        self.assertIn('"Buat lebih sulit"', messages[3]["content"])
