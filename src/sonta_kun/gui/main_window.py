"""メインウィンドウモジュール"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
from typing import Optional

from ..config import AppConfig
from ..excel_reader import ExcelReader, ExcelReadError, TodoList
from ..output_formatter import OutputFormat, OutputFormatter
from ..profile_manager import ProfileManager, TargetProfile
from ..report_generator import GeneratedReport, ReportGenerationError, ReportGenerator


class MainWindow:
    """SONTA-kun メインウィンドウ"""

    def __init__(self):
        self._root = tk.Tk()
        self._root.title("SONTA-kun - 週報・月報作成支援ツール")
        self._root.geometry("900x700")
        self._root.minsize(800, 600)

        # 依存モジュール
        self._config = AppConfig.load()
        self._profile_manager = ProfileManager()
        self._excel_reader = ExcelReader()
        self._formatter = OutputFormatter()
        self._generator: Optional[ReportGenerator] = None

        # 状態
        self._current_todo_list: Optional[TodoList] = None
        self._generated_report: Optional[GeneratedReport] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self._root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側パネル（入力）
        left_frame = ttk.LabelFrame(main_frame, text="入力", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self._setup_input_panel(left_frame)

        # 右側パネル（出力）
        right_frame = ttk.LabelFrame(main_frame, text="出力", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self._setup_output_panel(right_frame)

    def _setup_input_panel(self, parent: ttk.Frame) -> None:
        """入力パネルをセットアップ"""
        # ファイル選択
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(file_frame, text="Excelファイル:").pack(side=tk.LEFT)
        self._file_path_var = tk.StringVar()
        self._file_entry = ttk.Entry(file_frame, textvariable=self._file_path_var)
        self._file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Button(file_frame, text="参照", command=self._browse_file).pack(side=tk.RIGHT)

        # 報告設定
        settings_frame = ttk.LabelFrame(parent, text="報告設定", padding="5")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # 報告タイプ
        type_frame = ttk.Frame(settings_frame)
        type_frame.pack(fill=tk.X, pady=2)
        ttk.Label(type_frame, text="報告タイプ:").pack(side=tk.LEFT)
        self._report_type_var = tk.StringVar(value="weekly")
        ttk.Radiobutton(type_frame, text="週報", variable=self._report_type_var, value="weekly").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(type_frame, text="月報", variable=self._report_type_var, value="monthly").pack(side=tk.LEFT)

        # 報告対象者
        target_frame = ttk.Frame(settings_frame)
        target_frame.pack(fill=tk.X, pady=2)
        ttk.Label(target_frame, text="報告対象者:").pack(side=tk.LEFT)
        self._target_var = tk.StringVar()
        profile_names = self._profile_manager.get_profile_names()
        self._target_combo = ttk.Combobox(target_frame, textvariable=self._target_var, values=profile_names, state="readonly")
        self._target_combo.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        if profile_names:
            self._target_combo.current(0)

        ttk.Button(target_frame, text="設定", command=self._open_settings).pack(side=tk.RIGHT)

        # 出力形式
        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(fill=tk.X, pady=2)
        ttk.Label(format_frame, text="出力形式:").pack(side=tk.LEFT)
        self._format_var = tk.StringVar(value="markdown")
        ttk.Radiobutton(format_frame, text="Markdown", variable=self._format_var, value="markdown").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="Text", variable=self._format_var, value="text").pack(side=tk.LEFT)

        # 前回報告（オプション）
        prev_frame = ttk.LabelFrame(parent, text="前回報告（オプション）", padding="5")
        prev_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._prev_report_text = scrolledtext.ScrolledText(prev_frame, height=6)
        self._prev_report_text.pack(fill=tk.BOTH, expand=True)

        # 追加メモ
        notes_frame = ttk.LabelFrame(parent, text="追加メモ（オプション）", padding="5")
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._notes_text = scrolledtext.ScrolledText(notes_frame, height=4)
        self._notes_text.pack(fill=tk.BOTH, expand=True)

        # 生成ボタン
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)

        self._generate_btn = ttk.Button(btn_frame, text="報告書を生成", command=self._generate_report)
        self._generate_btn.pack(side=tk.LEFT, padx=5)

        self._status_label = ttk.Label(btn_frame, text="")
        self._status_label.pack(side=tk.LEFT, padx=10)

    def _setup_output_panel(self, parent: ttk.Frame) -> None:
        """出力パネルをセットアップ"""
        # 出力テキスト
        self._output_text = scrolledtext.ScrolledText(parent)
        self._output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # ボタン
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="コピー", command=self._copy_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="ファイル保存", command=self._save_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="クリア", command=self._clear_output).pack(side=tk.RIGHT, padx=5)

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
        except ExcelReadError as e:
            messagebox.showerror("エラー", f"ファイル読み込みエラー:\n{e}")
            self._status_label.config(text="読み込み失敗")

    def _generate_report(self) -> None:
        """報告書を生成"""
        if not self._current_todo_list:
            messagebox.showwarning("警告", "先にExcelファイルを読み込んでください")
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
        prev_report = self._prev_report_text.get("1.0", tk.END).strip() or None
        notes = self._notes_text.get("1.0", tk.END).strip() or None

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
            self._output_text.delete("1.0", tk.END)
            self._output_text.insert("1.0", formatted.full_report)

            self._status_label.config(text="生成完了")

        except ReportGenerationError as e:
            messagebox.showerror("エラー", f"報告書生成エラー:\n{e}")
            self._status_label.config(text="生成失敗")
        finally:
            self._generate_btn.config(state=tk.NORMAL)

    def _copy_output(self) -> None:
        """出力をクリップボードにコピー"""
        content = self._output_text.get("1.0", tk.END).strip()
        if content:
            self._root.clipboard_clear()
            self._root.clipboard_append(content)
            self._status_label.config(text="クリップボードにコピーしました")

    def _save_output(self) -> None:
        """出力をファイルに保存"""
        content = self._output_text.get("1.0", tk.END).strip()
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
        self._output_text.delete("1.0", tk.END)
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
