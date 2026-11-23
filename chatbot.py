"""Настольное приложение «Чат-бот — помощник студента» на Python и Tkinter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from typing import Callable


APP_TITLE = "Чат-бот — помощник студента"
STATUS_READY = "Бот готов к работе"
STATUS_EMPTY_WARNING = "Введите сообщение перед отправкой"
STATUS_CLEARED = "История чата очищена — Бот готов к работе"
UNKNOWN_COMMAND_REPLY = (
    "Я пока не знаю ответа на этот вопрос. "
    "Введите “Помощь”, чтобы увидеть список команд."
)


@dataclass(frozen=True)
class CommandRule:
    """Описание одной команды чат-бота и ключевых слов для её распознавания."""

    name: str
    description: str
    keywords: tuple[str, ...]
    response: str | Callable[[], str]


class StudentChatBot:
    """Логика распознавания ключевых слов и формирования ответов чат-бота."""

    def __init__(self, now_provider: Callable[[], datetime] | None = None) -> None:
        self._now_provider = now_provider or datetime.now
        self._rules: tuple[CommandRule, ...] = (
            CommandRule(
                name="Домашнее задание",
                description="напоминание о заданиях",
                keywords=(
                    "домашнее задание",
                    "домашнего задания",
                    "домашнюю работу",
                    "домашняя работа",
                    "домашка",
                    "домашку",
                    "дз",
                    "практическая",
                    "практическое задание",
                ),
                response=(
                    "Текущее домашнее задание:\n"
                    "• Завершить практическую работу по Python и Tkinter;\n"
                    "• Проверить валидацию ввода и обработку клавиши Enter;\n"
                    "• Загрузить готовый проект в репозиторий GitHub до конца недели."
                ),
            ),
            CommandRule(
                name="Расписание",
                description="информация о занятиях",
                keywords=(
                    "расписание",
                    "расписания",
                    "расписании",
                    "пары",
                    "занятия",
                    "занятий",
                    "лекции",
                ),
                response=(
                    "Расписание занятий на неделю:\n"
                    "• Понедельник, 09:00 — Программирование на Python (лекция);\n"
                    "• Среда, 10:40 — Практикум по графическим интерфейсам Tkinter;\n"
                    "• Пятница, 13:30 — Алгоритмы и структуры данных (лабораторная)."
                ),
            ),
            CommandRule(
                name="Преподаватель",
                description="информация о преподавателе",
                keywords=(
                    "преподаватель",
                    "преподавателя",
                    "преподавателю",
                    "препод",
                    "консультация",
                    "консультации",
                    "лектор",
                ),
                response=(
                    "Информация о преподавателе:\n"
                    "• Дисциплина: «Программирование на Python»;\n"
                    "• Консультации: четверг с 14:00 до 16:00 (ауд. 305);\n"
                    "• По вопросам практических заданий можно обратиться после лекции "
                    "или через учебный портал."
                ),
            ),
            CommandRule(
                name="Tkinter",
                description="назначение библиотеки",
                keywords=("tkinter", "ткинтер", "gui", "графический интерфейс"),
                response=(
                    "Tkinter — это стандартная библиотека Python для создания "
                    "настольных графических интерфейсов (GUI). Она входит в базовую "
                    "поставку Python и предоставляет готовые виджеты: окна, кнопки, "
                    "поля ввода, текстовые области и диалоговые окна."
                ),
            ),
            CommandRule(
                name="Python",
                description="краткая информация о языке",
                keywords=("python", "питон", "пайтон"),
                response=(
                    "Python — это высокоуровневый интерпретируемый язык "
                    "программирования с простым и читаемым синтаксисом. Его широко "
                    "используют в веб-разработке, анализе данных, автоматизации, "
                    "машинном обучении и создании настольных приложений."
                ),
            ),
            CommandRule(
                name="Экзамен",
                description="советы по подготовке к сессии",
                keywords=(
                    "экзамен",
                    "экзамены",
                    "экзамену",
                    "зачет",
                    "зачеты",
                    "сессия",
                    "сессии",
                ),
                response=(
                    "Подготовка к экзамену по Python:\n"
                    "• Повторите типы данных, циклы, функции и ООП;\n"
                    "• Разберите работу с виджетами и событиями в Tkinter;\n"
                    "• Выполните все практические работы — они помогут получить допуск."
                ),
            ),
            CommandRule(
                name="Время",
                description="текущая дата и время",
                keywords=("время", "который час", "дата", "какой сегодня день"),
                response=self._format_current_datetime,
            ),
            CommandRule(
                name="Помощь",
                description="список доступных команд",
                keywords=("помощь", "команды", "справка", "help", "что умеешь"),
                response=self.get_help_text,
            ),
            CommandRule(
                name="Как дела",
                description="ответ о состоянии бота",
                keywords=(
                    "как дела",
                    "как ты",
                    "как настроение",
                    "как сам",
                    "что нового",
                ),
                response=(
                    "Спасибо, у меня всё отлично! Все модули работают стабильно, "
                    "и я готов помогать тебе с учёбой. Как проходят твои занятия?"
                ),
            ),
            CommandRule(
                name="Привет",
                description="приветствие пользователя",
                keywords=(
                    "привет",
                    "здравствуй",
                    "здравствуйте",
                    "доброе утро",
                    "добрый день",
                    "добрый вечер",
                    "хай",
                    "hello",
                    "hi",
                ),
                response=(
                    "Привет! Я чат-бот — помощник студента. "
                    "Спроси меня о расписании, домашнем задании, Python или Tkinter, "
                    "либо введи «Помощь», чтобы увидеть все команды."
                ),
            ),
            CommandRule(
                name="Спасибо",
                description="вежливый ответ",
                keywords=("спасибо", "благодарю", "спс", "thanks", "thank you"),
                response=(
                    "Пожалуйста! Всегда рад помочь. Если появятся ещё вопросы по учёбе, "
                    "просто напиши мне."
                ),
            ),
            CommandRule(
                name="Пока",
                description="прощание",
                keywords=("пока", "до свидания", "прощай", "увидимся", "bye"),
                response=(
                    "До скорой встречи! Желаю продуктивной учёбы и отличных оценок!"
                ),
            ),
        )

        # Порядок отображения команд в справке «Помощь» (основные 10 + дополнительные).
        self._help_order: tuple[str, ...] = (
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
            "Экзамен",
            "Время",
        )

    @property
    def commands(self) -> tuple[CommandRule, ...]:
        """Возвращает кортеж зарегистрированных правил команд."""
        return self._rules

    @staticmethod
    def normalize_text(text: str) -> str:
        """Приводит текст к нижнему регистру, убирает лишние пробелы и заменяет «ё» на «е»."""
        cleaned = " ".join(text.strip().lower().split())
        return cleaned.replace("ё", "е")

    @staticmethod
    def matches_keyword(normalized_text: str, keyword: str) -> bool:
        """Проверяет наличие ключевого слова или фразы по границам слов."""
        normalized_keyword = StudentChatBot.normalize_text(keyword)
        pattern = rf"(?<!\w){re.escape(normalized_keyword)}(?!\w)"
        return re.search(pattern, normalized_text) is not None

    def _format_current_datetime(self) -> str:
        now = self._now_provider()
        return f"Сейчас {now.strftime('%d.%m.%Y, %H:%M:%S')}."

    def get_help_text(self) -> str:
        """Формирует список всех доступных команд чат-бота."""
        rules_by_name = {rule.name: rule for rule in self._rules}
        lines = ["Доступные команды чат-бота:"]
        for index, name in enumerate(self._help_order, start=1):
            rule = rules_by_name[name]
            lines.append(f"{index}. {rule.name} — {rule.description}")
        return "\n".join(lines)

    def get_response(self, user_message: str) -> str:
        """Распознаёт ключевые слова в сообщении и возвращает ответ бота."""
        normalized = self.normalize_text(user_message)
        if not normalized:
            return UNKNOWN_COMMAND_REPLY

        for rule in self._rules:
            for keyword in rule.keywords:
                if self.matches_keyword(normalized, keyword):
                    if callable(rule.response):
                        return rule.response()
                    return rule.response

        return UNKNOWN_COMMAND_REPLY


class ChatBotApp:
    """Графический интерфейс настольного приложения «Чат-бот — помощник студента»."""

    # Палитра оформления
    COLOR_BG = "#F1F5F9"
    COLOR_HEADER_BG = "#1E293B"
    COLOR_HEADER_FG = "#F8FAFC"
    COLOR_HEADER_SUB = "#94A3B8"
    COLOR_CARD_BG = "#FFFFFF"
    COLOR_BORDER = "#CBD5E1"
    COLOR_TEXT = "#0F172A"
    COLOR_MUTED = "#64748B"

    COLOR_USER_NAME = "#1D4ED8"
    COLOR_USER_BG = "#EFF6FF"
    COLOR_BOT_NAME = "#047857"
    COLOR_BOT_BG = "#F8FAFC"

    COLOR_BTN_SEND = "#2563EB"
    COLOR_BTN_SEND_HOVER = "#1D4ED8"
    COLOR_BTN_CLEAR = "#E2E8F0"
    COLOR_BTN_CLEAR_HOVER = "#CBD5E1"
    COLOR_BTN_EXIT = "#DC2626"
    COLOR_BTN_EXIT_HOVER = "#B91C1C"

    COLOR_STATUS_BG = "#E2E8F0"
    COLOR_STATUS_OK = "#334155"
    COLOR_STATUS_WARN = "#B45309"

    FONT_TITLE = ("Segoe UI", 14, "bold")
    FONT_SUBTITLE = ("Segoe UI", 9)
    FONT_CHAT_HEADER = ("Segoe UI", 9, "bold")
    FONT_CHAT_TIME = ("Segoe UI", 8)
    FONT_CHAT_BODY = ("Segoe UI", 10)
    FONT_ENTRY = ("Segoe UI", 11)
    FONT_BUTTON = ("Segoe UI", 10, "bold")
    FONT_STATUS = ("Segoe UI", 9)

    def __init__(
        self,
        root: tk.Tk,
        bot: StudentChatBot | None = None,
        time_provider: Callable[[], str] | None = None,
    ) -> None:
        self.root = root
        self.bot = bot or StudentChatBot()
        self._time_provider = time_provider or self._default_time_provider

        self._configure_window()
        self._build_ui()
        self._append_welcome_message()

    @staticmethod
    def _default_time_provider() -> str:
        return datetime.now().strftime("%H:%M:%S")

    def _configure_window(self) -> None:
        self.root.title(APP_TITLE)
        self.root.geometry("740x580")
        self.root.minsize(580, 460)
        self.root.configure(bg=self.COLOR_BG)
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

    def _build_ui(self) -> None:
        # 1. Верхняя шапка приложения
        header_frame = tk.Frame(
            self.root,
            bg=self.COLOR_HEADER_BG,
            padx=18,
            pady=14,
        )
        header_frame.grid(row=0, column=0, sticky="ew")

        title_label = tk.Label(
            header_frame,
            text=APP_TITLE,
            bg=self.COLOR_HEADER_BG,
            fg=self.COLOR_HEADER_FG,
            font=self.FONT_TITLE,
            anchor="w",
        )
        title_label.pack(fill="x")

        subtitle_label = tk.Label(
            header_frame,
            text="Задайте вопрос или введите «Помощь» для просмотра всех команд",
            bg=self.COLOR_HEADER_BG,
            fg=self.COLOR_HEADER_SUB,
            font=self.FONT_SUBTITLE,
            anchor="w",
        )
        subtitle_label.pack(fill="x", pady=(2, 0))

        # 2. Область истории переписки (ScrolledText)
        chat_outer = tk.Frame(self.root, bg=self.COLOR_BG)
        chat_outer.grid(row=1, column=0, sticky="nsew", padx=16, pady=(14, 10))
        chat_outer.columnconfigure(0, weight=1)
        chat_outer.rowconfigure(0, weight=1)

        chat_border = tk.Frame(
            chat_outer,
            bg=self.COLOR_BORDER,
            padx=1,
            pady=1,
        )
        chat_border.grid(row=0, column=0, sticky="nsew")
        chat_border.columnconfigure(0, weight=1)
        chat_border.rowconfigure(0, weight=1)

        self.chat_history = ScrolledText(
            chat_border,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.COLOR_CARD_BG,
            fg=self.COLOR_TEXT,
            font=self.FONT_CHAT_BODY,
            relief=tk.FLAT,
            padx=14,
            pady=12,
            spacing1=2,
            spacing3=4,
            cursor="arrow",
        )
        self.chat_history.grid(row=0, column=0, sticky="nsew")
        self._configure_chat_tags()

        # 3. Панель ввода и кнопок управления
        controls_frame = tk.Frame(self.root, bg=self.COLOR_BG)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        controls_frame.columnconfigure(0, weight=1)

        entry_border = tk.Frame(controls_frame, bg=self.COLOR_BORDER, padx=1, pady=1)
        entry_border.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        entry_border.columnconfigure(0, weight=1)

        entry_inner = tk.Frame(entry_border, bg=self.COLOR_CARD_BG, padx=8)
        entry_inner.grid(row=0, column=0, sticky="ew")
        entry_inner.columnconfigure(0, weight=1)

        self.message_entry = tk.Entry(
            entry_inner,
            font=self.FONT_ENTRY,
            bg=self.COLOR_CARD_BG,
            fg=self.COLOR_TEXT,
            insertbackground=self.COLOR_TEXT,
            relief=tk.FLAT,
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", ipady=8)
        self.message_entry.bind("<Return>", self.send_message)
        self.message_entry.bind("<KP_Enter>", self.send_message)
        self.message_entry.focus_set()

        self.send_button = tk.Button(
            controls_frame,
            text="Отправить",
            command=self.send_message,
            bg=self.COLOR_BTN_SEND,
            fg="#FFFFFF",
            activebackground=self.COLOR_BTN_SEND_HOVER,
            activeforeground="#FFFFFF",
            font=self.FONT_BUTTON,
            relief=tk.FLAT,
            padx=16,
            pady=7,
            cursor="hand2",
        )
        self.send_button.grid(row=0, column=1, padx=(0, 8))

        self.clear_button = tk.Button(
            controls_frame,
            text="Очистить чат",
            command=self.clear_chat,
            bg=self.COLOR_BTN_CLEAR,
            fg=self.COLOR_TEXT,
            activebackground=self.COLOR_BTN_CLEAR_HOVER,
            activeforeground=self.COLOR_TEXT,
            font=self.FONT_BUTTON,
            relief=tk.FLAT,
            padx=14,
            pady=7,
            cursor="hand2",
        )
        self.clear_button.grid(row=0, column=2, padx=(0, 8))

        self.exit_button = tk.Button(
            controls_frame,
            text="Выход",
            command=self.confirm_exit,
            bg=self.COLOR_BTN_EXIT,
            fg="#FFFFFF",
            activebackground=self.COLOR_BTN_EXIT_HOVER,
            activeforeground="#FFFFFF",
            font=self.FONT_BUTTON,
            relief=tk.FLAT,
            padx=14,
            pady=7,
            cursor="hand2",
        )
        self.exit_button.grid(row=0, column=3)

        self._bind_hover(self.send_button, self.COLOR_BTN_SEND, self.COLOR_BTN_SEND_HOVER)
        self._bind_hover(self.clear_button, self.COLOR_BTN_CLEAR, self.COLOR_BTN_CLEAR_HOVER)
        self._bind_hover(self.exit_button, self.COLOR_BTN_EXIT, self.COLOR_BTN_EXIT_HOVER)

        # 4. Строка состояния
        status_frame = tk.Frame(
            self.root,
            bg=self.COLOR_STATUS_BG,
            padx=16,
            pady=6,
        )
        status_frame.grid(row=3, column=0, sticky="ew")

        self.status_var = tk.StringVar(value=STATUS_READY)
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=self.COLOR_STATUS_BG,
            fg=self.COLOR_STATUS_OK,
            font=self.FONT_STATUS,
            anchor="w",
        )
        self.status_label.pack(fill="x")

    def _configure_chat_tags(self) -> None:
        # Оформление сообщений пользователя (выделение синим оттенком и отступ слева)
        self.chat_history.tag_configure(
            "user_header",
            foreground=self.COLOR_USER_NAME,
            background=self.COLOR_USER_BG,
            font=self.FONT_CHAT_HEADER,
            lmargin1=64,
            lmargin2=64,
            rmargin=10,
            spacing1=6,
        )
        self.chat_history.tag_configure(
            "user_time",
            foreground=self.COLOR_MUTED,
            background=self.COLOR_USER_BG,
            font=self.FONT_CHAT_TIME,
        )
        self.chat_history.tag_configure(
            "user_body",
            foreground=self.COLOR_TEXT,
            background=self.COLOR_USER_BG,
            font=self.FONT_CHAT_BODY,
            lmargin1=64,
            lmargin2=64,
            rmargin=10,
            spacing3=8,
        )

        # Оформление сообщений бота (выделение зелёным акцентом и отступ справа)
        self.chat_history.tag_configure(
            "bot_header",
            foreground=self.COLOR_BOT_NAME,
            background=self.COLOR_BOT_BG,
            font=self.FONT_CHAT_HEADER,
            lmargin1=10,
            lmargin2=10,
            rmargin=64,
            spacing1=6,
        )
        self.chat_history.tag_configure(
            "bot_time",
            foreground=self.COLOR_MUTED,
            background=self.COLOR_BOT_BG,
            font=self.FONT_CHAT_TIME,
        )
        self.chat_history.tag_configure(
            "bot_body",
            foreground=self.COLOR_TEXT,
            background=self.COLOR_BOT_BG,
            font=self.FONT_CHAT_BODY,
            lmargin1=10,
            lmargin2=10,
            rmargin=64,
            spacing3=8,
        )

        self.chat_history.tag_configure("spacer", font=("Segoe UI", 4))

    @staticmethod
    def _bind_hover(button: tk.Button, normal_bg: str, hover_bg: str) -> None:
        button.bind("<Enter>", lambda _event: button.configure(bg=hover_bg))
        button.bind("<Leave>", lambda _event: button.configure(bg=normal_bg))

    def _set_status(self, message: str, is_warning: bool = False) -> None:
        self.status_var.set(message)
        color = self.COLOR_STATUS_WARN if is_warning else self.COLOR_STATUS_OK
        self.status_label.configure(fg=color)

    def _append_welcome_message(self) -> None:
        welcome_text = (
            "Здравствуйте! Я чат-бот — помощник студента.\n"
            "Напишите вопрос или введите «Помощь», чтобы увидеть список команд."
        )
        self.append_message("Бот", welcome_text, is_user=False)

    def append_message(self, sender: str, text: str, *, is_user: bool) -> None:
        """Добавляет отформатированное сообщение с текущим временем в область переписки."""
        timestamp = self._time_provider()
        prefix = "user" if is_user else "bot"

        self.chat_history.configure(state=tk.NORMAL)
        if self.chat_history.index("end-1c") != "1.0":
            self.chat_history.insert(tk.END, "\n", "spacer")

        self.chat_history.insert(tk.END, f"{sender}  ", f"{prefix}_header")
        self.chat_history.insert(tk.END, f"[{timestamp}]\n", (f"{prefix}_header", f"{prefix}_time"))
        self.chat_history.insert(tk.END, f"{text}\n", f"{prefix}_body")

        self.chat_history.configure(state=tk.DISABLED)
        self.chat_history.see(tk.END)

    def send_message(self, _event: tk.Event | None = None) -> bool:
        """Обрабатывает отправку сообщения пользователя и выводит ответ бота."""
        raw_text = self.message_entry.get()
        user_text = raw_text.strip()

        if not user_text:
            self.message_entry.delete(0, tk.END)
            self._set_status(STATUS_EMPTY_WARNING, is_warning=True)
            self.root.bell()
            self.message_entry.focus_set()
            return False

        self.append_message("Вы", user_text, is_user=True)
        self.message_entry.delete(0, tk.END)

        bot_reply = self.bot.get_response(user_text)
        self.append_message("Бот", bot_reply, is_user=False)

        self._set_status(STATUS_READY, is_warning=False)
        self.message_entry.focus_set()
        return True

    def clear_chat(self) -> None:
        """Очищает область истории переписки."""
        self.chat_history.configure(state=tk.NORMAL)
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.configure(state=tk.DISABLED)

        self._set_status(STATUS_CLEARED, is_warning=False)
        self.message_entry.focus_set()

    def confirm_exit(self) -> bool:
        """Запрашивает подтверждение перед закрытием приложения."""
        should_exit = messagebox.askyesno(
            "Подтверждение выхода",
            f"Вы действительно хотите закрыть приложение «{APP_TITLE}»?",
            parent=self.root,
        )
        if should_exit:
            self.root.destroy()
            return True
        return False


def main() -> None:
    """Точка входа для запуска настольного приложения."""
    root = tk.Tk()
    ChatBotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
