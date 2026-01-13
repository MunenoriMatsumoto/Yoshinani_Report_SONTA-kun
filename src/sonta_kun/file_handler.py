"""ファイル操作ハンドラーモジュール"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

# D&Dサポートはオプション
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


class FileSelector:
    """ファイル選択クラス（ダイアログ＆D&D対応）"""

    SUPPORTED_EXTENSIONS = [".xlsx", ".xls", ".xlsm"]

    def __init__(self):
        self._selected_file: Optional[Path] = None
        self._on_file_selected: Optional[Callable[[Path], None]] = None

    def select_file_dialog(self, title: str = "Excelファイルを選択") -> Optional[Path]:
        """
        ファイル選択ダイアログを表示する

        Args:
            title: ダイアログのタイトル

        Returns:
            選択されたファイルのPath、キャンセル時はNone
        """
        root = tk.Tk()
        root.withdraw()

        filetypes = [
            ("Excel ファイル", "*.xlsx *.xls *.xlsm"),
            ("すべてのファイル", "*.*"),
        ]

        file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)

        root.destroy()

        if file_path:
            path = Path(file_path)
            self._selected_file = path
            return path
        return None

    def select_from_path(self, file_path: str | Path) -> Path:
        """
        パス指定でファイルを選択する

        Args:
            file_path: ファイルパス

        Returns:
            検証されたファイルのPath

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: サポートされていない拡張子の場合
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {path}")

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"サポートされていないファイル形式です: {path.suffix}\n"
                f"対応形式: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        self._selected_file = path
        return path

    @property
    def selected_file(self) -> Optional[Path]:
        """選択されたファイル"""
        return self._selected_file


class DropZoneWindow:
    """ドラッグ＆ドロップ対応のファイル選択ウィンドウ"""

    def __init__(
        self,
        on_file_dropped: Callable[[Path], None],
        title: str = "SONTA-kun - ファイル選択",
    ):
        """
        Args:
            on_file_dropped: ファイルがドロップされた時のコールバック
            title: ウィンドウタイトル
        """
        self._on_file_dropped = on_file_dropped
        self._title = title
        self._selected_file: Optional[Path] = None

        if not DND_AVAILABLE:
            print("注意: tkinterdnd2がインストールされていないため、D&D機能は無効です")
            print("D&D機能を有効にするには: pip install tkinterdnd2")

    def show(self) -> Optional[Path]:
        """
        ドロップゾーンウィンドウを表示する

        Returns:
            選択されたファイルのPath、キャンセル時はNone
        """
        if DND_AVAILABLE:
            return self._show_with_dnd()
        else:
            return self._show_without_dnd()

    def _show_with_dnd(self) -> Optional[Path]:
        """D&D対応ウィンドウを表示"""
        root = TkinterDnD.Tk()
        root.title(self._title)
        root.geometry("400x200")

        self._setup_ui(root, dnd_enabled=True)

        root.mainloop()
        return self._selected_file

    def _show_without_dnd(self) -> Optional[Path]:
        """D&Dなしのウィンドウを表示"""
        root = tk.Tk()
        root.title(self._title)
        root.geometry("400x200")

        self._setup_ui(root, dnd_enabled=False)

        root.mainloop()
        return self._selected_file

    def _setup_ui(self, root: tk.Tk, dnd_enabled: bool) -> None:
        """UIをセットアップ"""
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(expand=True, fill=tk.BOTH)

        # ドロップゾーン
        drop_frame = tk.Frame(frame, relief=tk.RIDGE, bd=2, bg="#f0f0f0")
        drop_frame.pack(expand=True, fill=tk.BOTH, pady=10)

        if dnd_enabled:
            label_text = "ここにExcelファイルをドロップ\nまたは下のボタンでファイルを選択"
        else:
            label_text = "下のボタンでExcelファイルを選択"

        drop_label = tk.Label(
            drop_frame, text=label_text, bg="#f0f0f0", font=("", 11), pady=30
        )
        drop_label.pack(expand=True, fill=tk.BOTH)

        if dnd_enabled:
            drop_frame.drop_target_register(DND_FILES)
            drop_frame.dnd_bind("<<Drop>>", lambda e: self._handle_drop(e, root))

        # ファイル選択ボタン
        select_btn = tk.Button(
            frame,
            text="ファイルを選択",
            command=lambda: self._handle_select(root),
            padx=20,
            pady=5,
        )
        select_btn.pack(pady=5)

        # キャンセルボタン
        cancel_btn = tk.Button(
            frame, text="キャンセル", command=root.destroy, padx=20, pady=5
        )
        cancel_btn.pack(pady=5)

    def _handle_drop(self, event, root: tk.Tk) -> None:
        """ドロップイベントを処理"""
        file_path = event.data.strip()
        # Windows: パスが{}で囲まれることがある
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]

        path = Path(file_path)
        if path.suffix.lower() in FileSelector.SUPPORTED_EXTENSIONS:
            self._selected_file = path
            self._on_file_dropped(path)
            root.destroy()
        else:
            tk.messagebox.showerror(
                "エラー",
                f"サポートされていないファイル形式です: {path.suffix}\n"
                f"対応形式: {', '.join(FileSelector.SUPPORTED_EXTENSIONS)}",
            )

    def _handle_select(self, root: tk.Tk) -> None:
        """ファイル選択ボタンの処理"""
        selector = FileSelector()
        path = selector.select_file_dialog()
        if path:
            self._selected_file = path
            self._on_file_dropped(path)
            root.destroy()
