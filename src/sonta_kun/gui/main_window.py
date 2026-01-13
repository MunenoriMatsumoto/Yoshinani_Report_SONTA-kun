"""メインウィンドウモジュール"""

import tkinter as tk
from pathlib import Path
from typing import Optional

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledText
    MODERN_UI = True
except ImportError:
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    MODERN_UI = False

from tkinter import filedialog, messagebox

from ..config import AppConfig
from ..excel_reader import ExcelReader, ExcelReadError, TodoItem, TodoList
from ..output_formatter import OutputFormat, OutputFormatter
from ..profile_manager import ProfileManager, TargetProfile
from ..report_generator import GeneratedReport, ReportGenerationError, ReportGenerator


class MainWindow:
    """SONTA-kun メインウィンドウ"""

    def __init__(self):
        if MODERN_UI:
            self._root = ttk.Window(
                title="SONTA-kun - 週報・月報作成支援ツール",
                themename="cosmo",  # モダンなテーマ
                size=(1000, 800),
                minsize=(900, 700),
            )
        else:
            self._root = tk.Tk()
            self._root.title("SONTA-kun - 週報・月報作成支援ツール")
            self._root.geometry("1000x800")
            self._root.minsize(900, 700)

        # 依存モジュール
        self._config = AppConfig.load()
        self._profile_manager = ProfileManager()
        self._excel_reader = ExcelReader()
        self._formatter = OutputFormatter()
        self._generator: Optional[ReportGenerator] = None

        # 状態
        self._current_todo_list: Optional[TodoList] = None
        self._generated_report: Optional[GeneratedReport] = None
        self._input_mode: str = "excel"  # "excel" or "freetext"

        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        # ヘッダー
        self._setup_header()

        # メインコンテンツ
        main_frame = ttk.Frame(self._root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側パネル（入力）
        left_frame = ttk.Labelframe(main_frame, text=" 入力 ", padding=10, bootstyle="primary")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self._setup_input_panel(left_frame)

        # 右側パネル（出力）
        right_frame = ttk.Labelframe(main_frame, text=" 出力 ", padding=10, bootstyle="success")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._setup_output_panel(right_frame)

    def _setup_header(self) -> None:
        """ヘッダーをセットアップ"""
        header_frame = ttk.Frame(self._root, padding=(15, 10))
        header_frame.pack(fill=tk.X)

        # タイトル
        title_label = ttk.Label(
            header_frame,
            text="SONTA-kun",
            font=("Helvetica", 20, "bold"),
            bootstyle="primary",
        )
        title_label.pack(side=tk.LEFT)

        subtitle_label = ttk.Label(
            header_frame,
            text="  週報・月報作成支援ツール",
            font=("Helvetica", 12),
            bootstyle="secondary",
        )
        subtitle_label.pack(side=tk.LEFT, padx=(5, 0), pady=(8, 0))

        # ステータス
        self._status_label = ttk.Label(
            header_frame,
            text="",
            font=("Helvetica", 10),
            bootstyle="info",
        )
        self._status_label.pack(side=tk.RIGHT)

    def _setup_input_panel(self, parent: ttk.Frame) -> None:
        """入力パネルをセットアップ"""
        # タブでExcel/自由記述を切り替え
        self._input_notebook = ttk.Notebook(parent, bootstyle="primary")
        self._input_notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Excelタブ
        excel_tab = ttk.Frame(self._input_notebook, padding=10)
        self._input_notebook.add(excel_tab, text="  Excel読み込み  ")
        self._setup_excel_tab(excel_tab)

        # 自由記述タブ
        freetext_tab = ttk.Frame(self._input_notebook, padding=10)
        self._input_notebook.add(freetext_tab, text="  自由記述  ")
        self._setup_freetext_tab(freetext_tab)

        # タブ切り替えイベント
        self._input_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 報告設定
        settings_frame = ttk.Labelframe(parent, text=" 報告設定 ", padding=10, bootstyle="info")
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        # 報告タイプ
        type_frame = ttk.Frame(settings_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="報告タイプ:", width=12).pack(side=tk.LEFT)
        self._report_type_var = tk.StringVar(value="weekly")
        ttk.Radiobutton(
            type_frame, text="週報", variable=self._report_type_var,
            value="weekly", bootstyle="primary-outline-toolbutton"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            type_frame, text="月報", variable=self._report_type_var,
            value="monthly", bootstyle="primary-outline-toolbutton"
        ).pack(side=tk.LEFT, padx=5)

        # 報告対象者
        target_frame = ttk.Frame(settings_frame)
        target_frame.pack(fill=tk.X, pady=5)
        ttk.Label(target_frame, text="報告対象者:", width=12).pack(side=tk.LEFT)
        self._target_var = tk.StringVar()
        profile_names = self._profile_manager.get_profile_names()
        self._target_combo = ttk.Combobox(
            target_frame, textvariable=self._target_var,
            values=profile_names, state="readonly", bootstyle="primary"
        )
        self._target_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        if profile_names:
            self._target_combo.current(0)

        ttk.Button(
            target_frame, text="設定", command=self._open_settings,
            bootstyle="secondary-outline", width=8
        ).pack(side=tk.RIGHT)

        # 出力形式
        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(fill=tk.X, pady=5)
        ttk.Label(format_frame, text="出力形式:", width=12).pack(side=tk.LEFT)
        self._format_var = tk.StringVar(value="markdown")
        ttk.Radiobutton(
            format_frame, text="Markdown", variable=self._format_var,
            value="markdown", bootstyle="success-outline-toolbutton"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            format_frame, text="Text", variable=self._format_var,
            value="text", bootstyle="success-outline-toolbutton"
        ).pack(side=tk.LEFT, padx=5)

        # 前回報告（オプション）
        prev_frame = ttk.Labelframe(parent, text=" 前回報告（オプション） ", padding=10, bootstyle="secondary")
        prev_frame.pack(fill=tk.X, pady=(0, 15))

        self._prev_report_text = ScrolledText(prev_frame, height=4, autohide=True)
        self._prev_report_text.pack(fill=tk.BOTH, expand=True)

        # 追加メモ
        notes_frame = ttk.Labelframe(parent, text=" 追加メモ（オプション） ", padding=10, bootstyle="secondary")
        notes_frame.pack(fill=tk.X, pady=(0, 15))

        self._notes_text = ScrolledText(notes_frame, height=3, autohide=True)
        self._notes_text.pack(fill=tk.BOTH, expand=True)

        # 生成ボタン
        self._generate_btn = ttk.Button(
            parent, text="報告書を生成", command=self._generate_report,
            bootstyle="success", width=20
        )
        self._generate_btn.pack(pady=5)

    def _setup_excel_tab(self, parent: ttk.Frame) -> None:
        """Excelタブをセットアップ"""
        # ファイル選択
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(file_frame, text="ファイル:").pack(side=tk.LEFT)
        self._file_path_var = tk.StringVar()
        self._file_entry = ttk.Entry(file_frame, textvariable=self._file_path_var, bootstyle="primary")
        self._file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        ttk.Button(
            file_frame, text="参照", command=self._browse_file,
            bootstyle="primary-outline", width=8
        ).pack(side=tk.RIGHT)

        # 読み込み内容プレビュー
        preview_label = ttk.Label(parent, text="読み込み内容:", bootstyle="secondary")
        preview_label.pack(anchor=tk.W, pady=(5, 5))

        self._excel_preview_text = ScrolledText(parent, height=12, autohide=True)
        self._excel_preview_text.pack(fill=tk.BOTH, expand=True)
        self._excel_preview_text.text.config(state=tk.DISABLED)

    def _setup_freetext_tab(self, parent: ttk.Frame) -> None:
        """自由記述タブをセットアップ"""
        # 説明
        hint_frame = ttk.Frame(parent)
        hint_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            hint_frame,
            text="ToDoアイテムを1行ずつ入力してください",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor=tk.W)
        ttk.Label(
            hint_frame,
            text="形式: タスク名 [ステータス] (優先度)   例: 機能Aの実装 [進行中] (高)",
            bootstyle="secondary",
        ).pack(anchor=tk.W)

        # 入力エリア
        self._freetext_input = ScrolledText(parent, height=14, autohide=True)
        self._freetext_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # ボタン
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame, text="サンプル挿入", command=self._insert_sample_todos,
            bootstyle="info-outline", width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            btn_frame, text="クリア", command=self._clear_freetext,
            bootstyle="warning-outline", width=8
        ).pack(side=tk.LEFT)
        ttk.Button(
            btn_frame, text="読み込み", command=self._load_freetext,
            bootstyle="primary", width=10
        ).pack(side=tk.RIGHT)

    def _on_tab_changed(self, event) -> None:
        """タブ切り替え時の処理"""
        selected_tab = self._input_notebook.index(self._input_notebook.select())
        self._input_mode = "excel" if selected_tab == 0 else "freetext"

    def _insert_sample_todos(self) -> None:
        """サンプルToDoを挿入"""
        sample = """週報作成ツールの設計 [完了] (高)
Bedrock API連携実装 [完了] (高)
Excel読み込み機能 [完了] (高)
GUI実装 [進行中] (高)
テスト作成 [進行中] (中)
ドキュメント作成 [未着手] (低)
コードレビュー [未着手] (中)"""
        self._freetext_input.text.delete("1.0", tk.END)
        self._freetext_input.text.insert("1.0", sample)

    def _clear_freetext(self) -> None:
        """自由記述をクリア"""
        self._freetext_input.text.delete("1.0", tk.END)
        self._current_todo_list = None
        self._status_label.config(text="")

    def _load_freetext(self) -> None:
        """自由記述からToDoリストを読み込む"""
        text = self._freetext_input.text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "ToDoアイテムを入力してください")
            return

        items = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            item = self._parse_todo_line(line)
            if item:
                items.append(item)

        if items:
            self._current_todo_list = TodoList(items=items, source_file="自由記述")
            self._status_label.config(text=f"読み込み完了: {len(items)}件のタスク")
        else:
            messagebox.showwarning("警告", "有効なToDoアイテムが見つかりません")

    def _parse_todo_line(self, line: str) -> Optional[TodoItem]:
        """1行をパースしてTodoItemを作成"""
        import re

        task = line
        status = ""
        priority = ""

        # ステータスを抽出 [xxx]
        status_match = re.search(r'\[([^\]]+)\]', line)
        if status_match:
            status = status_match.group(1)
            task = task.replace(status_match.group(0), "")

        # 優先度を抽出 (xxx)
        priority_match = re.search(r'\(([^)]+)\)', task)
        if priority_match:
            priority = priority_match.group(1)
            task = task.replace(priority_match.group(0), "")

        task = task.strip()
        if task:
            return TodoItem(task=task, status=status, priority=priority)
        return None

    def _setup_output_panel(self, parent: ttk.Frame) -> None:
        """出力パネルをセットアップ"""
        # 出力テキスト
        self._output_text = ScrolledText(parent, autohide=True)
        self._output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # ボタン
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame, text="コピー", command=self._copy_output,
            bootstyle="info", width=10
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            btn_frame, text="ファイル保存", command=self._save_output,
            bootstyle="success-outline", width=12
        ).pack(side=tk.LEFT)
        ttk.Button(
            btn_frame, text="クリア", command=self._clear_output,
            bootstyle="danger-outline", width=8
        ).pack(side=tk.RIGHT)

    def _browse_file(self) -> None:
        """ファイル選択ダイアログを開く"""
        filetypes = [
            ("Excel ファイル", "*.xlsx *.xls *.xlsm"),
            ("すべてのファイル", "*.*"),
        ]
        file_path = filedialog.askopenfilename(
            title="ToDoリストのExcelファイルを選択",
            filetypes=filetypes,
        )
        if file_path:
            self._file_path_var.set(file_path)
            self._load_excel_file(file_path)

    def _load_excel_file(self, file_path: str) -> None:
        """Excelファイルを読み込む"""
        try:
            self._current_todo_list = self._excel_reader.read(file_path)
            self._status_label.config(text=f"読み込み完了: {len(self._current_todo_list.items)}件のタスク")

            # プレビュー表示
            self._excel_preview_text.text.config(state=tk.NORMAL)
            self._excel_preview_text.text.delete("1.0", tk.END)
            self._excel_preview_text.text.insert("1.0", self._current_todo_list.to_text())
            self._excel_preview_text.text.config(state=tk.DISABLED)

        except ExcelReadError as e:
            messagebox.showerror("エラー", f"ファイル読み込みエラー:\n{e}")
            self._status_label.config(text="読み込み失敗")

    def _generate_report(self) -> None:
        """報告書を生成"""
        # 自由記述モードの場合、先に読み込み
        if self._input_mode == "freetext" and not self._current_todo_list:
            self._load_freetext()

        if not self._current_todo_list:
            if self._input_mode == "excel":
                messagebox.showwarning("警告", "先にExcelファイルを読み込んでください")
            else:
                messagebox.showwarning("警告", "ToDoアイテムを入力して「読み込み」をクリックしてください")
            return

        target_name = self._target_var.get()
        if not target_name:
            messagebox.showwarning("警告", "報告対象者を選択してください")
            return

        profile = self._profile_manager.get_profile(target_name)
        if not profile:
            messagebox.showerror("エラー", f"プロファイル '{target_name}' が見つかりません")
            return

        # 前回報告と追加メモを取得
        prev_report = self._prev_report_text.text.get("1.0", tk.END).strip() or None
        notes = self._notes_text.text.get("1.0", tk.END).strip() or None

        # 生成開始
        self._status_label.config(text="生成中...")
        self._generate_btn.config(state=tk.DISABLED)
        self._root.update()

        try:
            if self._generator is None:
                self._generator = ReportGenerator(
                    self._config.bedrock,
                    self._profile_manager,
                )

            self._generated_report = self._generator.generate(
                todo_list=self._current_todo_list,
                target_profile=profile,
                report_type=self._report_type_var.get(),
                previous_report=prev_report,
                additional_notes=notes,
                save_report=True,
            )

            # 出力をフォーマット
            output_format = OutputFormat.MARKDOWN if self._format_var.get() == "markdown" else OutputFormat.TEXT
            formatted = self._formatter.format(
                self._generated_report,
                output_format=output_format,
                report_type=self._report_type_var.get(),
                target_name=target_name,
            )

            # 出力表示
            self._output_text.text.delete("1.0", tk.END)
            self._output_text.text.insert("1.0", formatted.full_report)

            self._status_label.config(text="生成完了")

        except ReportGenerationError as e:
            messagebox.showerror("エラー", f"報告書生成エラー:\n{e}")
            self._status_label.config(text="生成失敗")
        finally:
            self._generate_btn.config(state=tk.NORMAL)

    def _copy_output(self) -> None:
        """出力をクリップボードにコピー"""
        content = self._output_text.text.get("1.0", tk.END).strip()
        if content:
            self._root.clipboard_clear()
            self._root.clipboard_append(content)
            self._status_label.config(text="クリップボードにコピーしました")

    def _save_output(self) -> None:
        """出力をファイルに保存"""
        content = self._output_text.text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "保存する内容がありません")
            return

        ext = ".md" if self._format_var.get() == "markdown" else ".txt"
        filetypes = [
            ("Markdown", "*.md") if ext == ".md" else ("Text", "*.txt"),
            ("すべてのファイル", "*.*"),
        ]
        file_path = filedialog.asksaveasfilename(
            title="報告書を保存",
            defaultextension=ext,
            filetypes=filetypes,
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self._status_label.config(text=f"保存完了: {Path(file_path).name}")

    def _clear_output(self) -> None:
        """出力をクリア"""
        self._output_text.text.delete("1.0", tk.END)
        self._generated_report = None

    def _open_settings(self) -> None:
        """設定画面を開く"""
        from .settings_window import SettingsWindow
        settings = SettingsWindow(self._root, self._profile_manager)
        self._root.wait_window(settings.window)
        # プロファイルリストを更新
        profile_names = self._profile_manager.get_profile_names()
        self._target_combo.config(values=profile_names)

    def run(self) -> None:
        """アプリケーションを実行"""
        self._root.mainloop()
