"""設定画面モジュール"""

import tkinter as tk
from typing import Optional

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    MODERN_UI = True
except ImportError:
    from tkinter import ttk
    MODERN_UI = False

from tkinter import messagebox

from ..profile_manager import ProfileManager, TargetProfile


class SettingsWindow:
    """設定画面（プロファイル管理）"""

    def __init__(self, parent: tk.Tk, profile_manager: ProfileManager):
        self._parent = parent
        self._profile_manager = profile_manager

        if MODERN_UI:
            self._window = ttk.Toplevel(parent)
            self._window.title("設定 - 報告対象者プロファイル")
            self._window.geometry("700x550")
        else:
            self._window = tk.Toplevel(parent)
            self._window.title("設定 - 報告対象者プロファイル")
            self._window.geometry("700x550")

        self._window.transient(parent)
        self._window.grab_set()

        self._selected_profile: Optional[TargetProfile] = None

        self._setup_ui()
        self._load_profiles()

    @property
    def window(self) -> tk.Toplevel:
        return self._window

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        main_frame = ttk.Frame(self._window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側：プロファイルリスト
        left_frame = ttk.Labelframe(main_frame, text=" プロファイル一覧 ", padding=10, bootstyle="primary")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # リストボックス
        list_container = ttk.Frame(left_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        self._profile_listbox = tk.Listbox(
            list_container,
            exportselection=False,
            font=("Helvetica", 11),
            selectbackground="#0d6efd",
            selectforeground="white",
        )
        self._profile_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._profile_listbox.bind("<<ListboxSelect>>", self._on_profile_select)

        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self._profile_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._profile_listbox.config(yscrollcommand=scrollbar.set)

        # リストボタン
        list_btn_frame = ttk.Frame(left_frame)
        list_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            list_btn_frame, text="新規", command=self._new_profile,
            bootstyle="success", width=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            list_btn_frame, text="削除", command=self._delete_profile,
            bootstyle="danger-outline", width=8
        ).pack(side=tk.LEFT)
        ttk.Button(
            list_btn_frame, text="リセット", command=self._reset_profiles,
            bootstyle="warning-outline", width=8
        ).pack(side=tk.RIGHT)

        # 右側：プロファイル編集
        right_frame = ttk.Labelframe(main_frame, text=" プロファイル編集 ", padding=10, bootstyle="info")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._setup_edit_form(right_frame)

    def _setup_edit_form(self, parent: ttk.Frame) -> None:
        """編集フォームをセットアップ"""
        # 名前
        name_frame = ttk.Frame(parent)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="名前:", width=12).pack(side=tk.LEFT)
        self._name_var = tk.StringVar()
        self._name_entry = ttk.Entry(name_frame, textvariable=self._name_var, bootstyle="primary")
        self._name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 役職
        role_frame = ttk.Frame(parent)
        role_frame.pack(fill=tk.X, pady=5)
        ttk.Label(role_frame, text="役職:", width=12).pack(side=tk.LEFT)
        self._role_var = tk.StringVar()
        self._role_combo = ttk.Combobox(
            role_frame,
            textvariable=self._role_var,
            values=["メンバー", "課長", "室長", "部長", "その他"],
            bootstyle="primary"
        )
        self._role_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 関心事
        focus_frame = ttk.Frame(parent)
        focus_frame.pack(fill=tk.X, pady=5)
        ttk.Label(focus_frame, text="関心事:", width=12).pack(side=tk.LEFT)
        self._focus_var = tk.StringVar()
        self._focus_combo = ttk.Combobox(
            focus_frame,
            textvariable=self._focus_var,
            values=["納期重視", "方針重視", "コスト重視", "詳細重視", "品質重視"],
            bootstyle="primary"
        )
        self._focus_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 説明
        desc_frame = ttk.Frame(parent)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="説明:", width=12).pack(side=tk.LEFT, anchor=tk.N)
        self._desc_text = tk.Text(desc_frame, height=3, font=("Helvetica", 10))
        self._desc_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # サマリ文字数
        summary_frame = ttk.Frame(parent)
        summary_frame.pack(fill=tk.X, pady=5)
        ttk.Label(summary_frame, text="サマリ文字数:", width=12).pack(side=tk.LEFT)
        self._summary_chars_var = tk.StringVar(value="300")
        self._summary_chars_spinbox = ttk.Spinbox(
            summary_frame,
            textvariable=self._summary_chars_var,
            from_=100,
            to=1000,
            width=10,
            bootstyle="primary"
        )
        self._summary_chars_spinbox.pack(side=tk.LEFT)

        # 詳細度
        detail_frame = ttk.Frame(parent)
        detail_frame.pack(fill=tk.X, pady=5)
        ttk.Label(detail_frame, text="詳細度:", width=12).pack(side=tk.LEFT)
        self._detail_level_var = tk.StringVar(value="medium")
        ttk.Radiobutton(
            detail_frame, text="低", variable=self._detail_level_var,
            value="low", bootstyle="info-outline-toolbutton"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            detail_frame, text="中", variable=self._detail_level_var,
            value="medium", bootstyle="info-outline-toolbutton"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            detail_frame, text="高", variable=self._detail_level_var,
            value="high", bootstyle="info-outline-toolbutton"
        ).pack(side=tk.LEFT, padx=5)

        # 出力形式
        format_frame = ttk.Frame(parent)
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

        # ボタン
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            btn_frame, text="保存", command=self._save_profile,
            bootstyle="success", width=10
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            btn_frame, text="閉じる", command=self._window.destroy,
            bootstyle="secondary-outline", width=10
        ).pack(side=tk.LEFT)

    def _load_profiles(self) -> None:
        """プロファイルリストを読み込む"""
        self._profile_listbox.delete(0, tk.END)
        for profile in self._profile_manager.list_profiles():
            self._profile_listbox.insert(tk.END, f"  {profile.name}  ({profile.role})")

    def _on_profile_select(self, event) -> None:
        """プロファイル選択時の処理"""
        selection = self._profile_listbox.curselection()
        if not selection:
            return

        # リストから名前を抽出
        item_text = self._profile_listbox.get(selection[0])
        name = item_text.split("(")[0].strip()

        profile = self._profile_manager.get_profile(name)
        if profile:
            self._selected_profile = profile
            self._load_profile_to_form(profile)

    def _load_profile_to_form(self, profile: TargetProfile) -> None:
        """プロファイルをフォームに読み込む"""
        self._name_var.set(profile.name)
        self._role_var.set(profile.role)
        self._focus_var.set(profile.focus)
        self._desc_text.delete("1.0", tk.END)
        self._desc_text.insert("1.0", profile.description)
        self._summary_chars_var.set(str(profile.summary_max_chars))
        self._detail_level_var.set(profile.detail_level)
        self._format_var.set(profile.preferred_format)

    def _save_profile(self) -> None:
        """プロファイルを保存"""
        name = self._name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "名前を入力してください")
            return

        role = self._role_var.get().strip()
        if not role:
            messagebox.showwarning("警告", "役職を選択してください")
            return

        focus = self._focus_var.get().strip()
        if not focus:
            messagebox.showwarning("警告", "関心事を選択してください")
            return

        try:
            summary_chars = int(self._summary_chars_var.get())
        except ValueError:
            summary_chars = 300

        profile = TargetProfile(
            name=name,
            role=role,
            focus=focus,
            description=self._desc_text.get("1.0", tk.END).strip(),
            summary_max_chars=summary_chars,
            detail_level=self._detail_level_var.get(),
            preferred_format=self._format_var.get(),
        )

        self._profile_manager.add_profile(profile)
        self._load_profiles()

        # 保存したプロファイルを選択
        names = self._profile_manager.get_profile_names()
        if name in names:
            idx = names.index(name)
            self._profile_listbox.selection_clear(0, tk.END)
            self._profile_listbox.selection_set(idx)

        messagebox.showinfo("完了", f"プロファイル '{name}' を保存しました")

    def _new_profile(self) -> None:
        """新規プロファイル"""
        self._selected_profile = None
        self._name_var.set("")
        self._role_var.set("")
        self._focus_var.set("")
        self._desc_text.delete("1.0", tk.END)
        self._summary_chars_var.set("300")
        self._detail_level_var.set("medium")
        self._format_var.set("markdown")
        self._profile_listbox.selection_clear(0, tk.END)

    def _delete_profile(self) -> None:
        """プロファイルを削除"""
        selection = self._profile_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除するプロファイルを選択してください")
            return

        item_text = self._profile_listbox.get(selection[0])
        name = item_text.split("(")[0].strip()

        if messagebox.askyesno("確認", f"プロファイル '{name}' を削除しますか？"):
            self._profile_manager.delete_profile(name)
            self._load_profiles()
            self._new_profile()

    def _reset_profiles(self) -> None:
        """デフォルトにリセット"""
        if messagebox.askyesno("確認", "すべてのプロファイルをデフォルトにリセットしますか？"):
            self._profile_manager.reset_to_defaults()
            self._load_profiles()
            self._new_profile()
            messagebox.showinfo("完了", "プロファイルをリセットしました")
