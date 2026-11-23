"""Модульные тесты для настольного приложения «Чат-бот — помощник студента»."""

from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import unittest
from unittest.mock import patch

from chatbot import (
    APP_TITLE,
    STATUS_CLEARED,
    STATUS_EMPTY_WARNING,
    STATUS_READY,
    UNKNOWN_COMMAND_REPLY,
    ChatBotApp,
    StudentChatBot,
)


class TestStudentChatBotLogic(unittest.TestCase):
    """Тесты распознавания ключевых слов и ответов чат-бота."""

    def setUp(self) -> None:
        fixed_now = datetime(2026, 11, 23, 14, 30, 5)
        self.bot = StudentChatBot(now_provider=lambda: fixed_now)

    def test_at_least_ten_commands_implemented(self) -> None:
        self.assertGreaterEqual(len(self.bot.commands), 10)

    def test_all_core_commands_return_relevant_responses(self) -> None:
        cases = {
            "Привет": "помощник студента",
            "Как дела": "отлично",
            "Расписание": "Понедельник",
            "Домашнее задание": "домашнее задание",
            "Python": "язык программирования",
            "Tkinter": "стандартная библиотека Python",
            "Преподаватель": "Консультации",
            "Помощь": "Доступные команды чат-бота",
            "Спасибо": "Пожалуйста",
            "Пока": "До скорой встречи",
            "Экзамен": "Подготовка к экзамену",
            "Время": "23.11.2026, 14:30:05",
        }
        for command, expected_substring in cases.items():
            with self.subTest(command=command):
                reply = self.bot.get_response(command)
                self.assertIn(expected_substring.lower(), reply.lower())
                self.assertNotEqual(reply, UNKNOWN_COMMAND_REPLY)

    def test_case_insensitive_punctuation_and_yo_normalization(self) -> None:
        self.assertIn("помощник студента", self.bot.get_response("  ПРИВЕТ!!!  ").lower())
        self.assertIn("подготовка к экзамену", self.bot.get_response("Когда зачёт?").lower())
        self.assertIn("стандартная библиотека", self.bot.get_response("Что такое Tkinter в Python?").lower())

    def test_word_boundary_prevents_false_matches(self) -> None:
        # "дз" не должно срабатывать внутри слова "подзадача", а "hi" внутри "which"
        self.assertEqual(self.bot.get_response("подзадача"), UNKNOWN_COMMAND_REPLY)
        self.assertEqual(self.bot.get_response("which"), UNKNOWN_COMMAND_REPLY)

    def test_unknown_command_returns_exact_fallback_message(self) -> None:
        self.assertEqual(
            self.bot.get_response("Расскажи про квантовую гравитацию"),
            UNKNOWN_COMMAND_REPLY,
        )
        self.assertEqual(self.bot.get_response("   "), UNKNOWN_COMMAND_REPLY)

    def test_help_lists_all_core_commands(self) -> None:
        help_text = self.bot.get_response("Помощь")
        for cmd in (
            "Привет",
            "Как дела",
            "Расписание",
            "Домашнее задание",
            "Python",
            "Tkinter",
            "Преподаватель",
            "Помощь",
            "Спасибо",
            "Пока",
        ):
            self.assertIn(cmd, help_text)


class TestChatBotAppUI(unittest.TestCase):
    """Тесты графического интерфейса и функциональных требований Tkinter."""

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.times = iter(["12:00:00", "12:00:01", "12:00:02", "12:00:03", "12:00:04"])
        self.app = ChatBotApp(self.root, time_provider=lambda: next(self.times, "12:00:59"))
        self.root.update_idletasks()

    def tearDown(self) -> None:
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except tk.TclError:
            pass

    def test_interface_widgets_and_initial_state(self) -> None:
        self.assertEqual(self.root.title(), APP_TITLE)
        self.assertIsInstance(self.app.chat_history, ScrolledText)
        self.assertEqual(str(self.app.chat_history.cget("state")), tk.DISABLED)
        self.assertIsInstance(self.app.message_entry, tk.Entry)
        self.assertEqual(self.app.send_button.cget("text"), "Отправить")
        self.assertEqual(self.app.clear_button.cget("text"), "Очистить чат")
        self.assertEqual(self.app.exit_button.cget("text"), "Выход")
        self.assertEqual(self.app.status_var.get(), STATUS_READY)

    def test_empty_message_is_rejected(self) -> None:
        initial_content = self.app.chat_history.get("1.0", tk.END)
        self.app.message_entry.insert(0, "     ")

        sent = self.app.send_message()

        self.assertFalse(sent)
        self.assertEqual(self.app.chat_history.get("1.0", tk.END), initial_content)
        self.assertEqual(self.app.message_entry.get(), "")
        self.assertEqual(self.app.status_var.get(), STATUS_EMPTY_WARNING)

    def test_send_message_appends_timestamped_dialog_and_clears_entry(self) -> None:
        self.app.message_entry.insert(0, "Расписание")

        sent = self.app.send_message()

        self.assertTrue(sent)
        self.assertEqual(self.app.message_entry.get(), "")
        self.assertEqual(self.app.status_var.get(), STATUS_READY)

        chat_text = self.app.chat_history.get("1.0", tk.END)
        self.assertIn("Вы  [12:00:01]", chat_text)
        self.assertIn("Расписание", chat_text)
        self.assertIn("Бот  [12:00:02]", chat_text)
        self.assertIn("Понедельник", chat_text)
        self.assertEqual(str(self.app.chat_history.cget("state")), tk.DISABLED)

    def test_enter_key_sends_message(self) -> None:
        return_binding = self.app.message_entry.bind("<Return>")
        kp_enter_binding = self.app.message_entry.bind("<KP_Enter>")
        self.assertTrue(return_binding)
        self.assertTrue(kp_enter_binding)

        self.app.message_entry.insert(0, "Python")
        self.root.deiconify()
        self.root.update()
        self.app.message_entry.focus_force()
        self.root.update()
        self.app.message_entry.event_generate("<Return>")
        self.root.update()

        self.assertEqual(self.app.message_entry.get(), "")
        chat_text = self.app.chat_history.get("1.0", tk.END)
        self.assertIn("Python", chat_text)
        self.assertIn("высокоуровневый", chat_text)

    def test_user_and_bot_messages_have_distinct_visual_styles(self) -> None:
        self.app.message_entry.insert(0, "Привет")
        self.app.send_message()

        self.assertTrue(self.app.chat_history.tag_ranges("user_header"))
        self.assertTrue(self.app.chat_history.tag_ranges("user_body"))
        self.assertTrue(self.app.chat_history.tag_ranges("bot_header"))
        self.assertTrue(self.app.chat_history.tag_ranges("bot_body"))

        self.assertNotEqual(
            self.app.chat_history.tag_cget("user_header", "foreground"),
            self.app.chat_history.tag_cget("bot_header", "foreground"),
        )
        self.assertNotEqual(
            self.app.chat_history.tag_cget("user_body", "background"),
            self.app.chat_history.tag_cget("bot_body", "background"),
        )

    def test_clear_chat_empties_history(self) -> None:
        self.app.message_entry.insert(0, "Спасибо")
        self.app.send_message()
        self.assertNotEqual(self.app.chat_history.get("1.0", "end-1c"), "")

        self.app.clear_chat()

        self.assertEqual(self.app.chat_history.get("1.0", "end-1c"), "")
        self.assertEqual(self.app.status_var.get(), STATUS_CLEARED)

    def test_confirm_exit_respects_user_choice(self) -> None:
        with patch("chatbot.messagebox.askyesno", return_value=False) as mock_ask:
            closed = self.app.confirm_exit()
            self.assertFalse(closed)
            self.assertTrue(self.root.winfo_exists())
            mock_ask.assert_called_once()

        with patch("chatbot.messagebox.askyesno", return_value=True) as mock_ask:
            closed = self.app.confirm_exit()
            self.assertTrue(closed)
            with self.assertRaises(tk.TclError):
                self.root.winfo_exists()
            mock_ask.assert_called_once()


if __name__ == "__main__":
    unittest.main()
