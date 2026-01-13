"""設定画面モジュール"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from ..profile_manager import ProfileManager, TargetProfile


class SettingsWindow:
    """設定画面（プロファイル管理）"""

    def __init__(self, parent: tk.Tk, profile_manager: ProfileManager):
        self._parent = parent
        self._profile_manager = profile_manager

        self._window = tk.Toplevel(parent)
        self._window.title("設定 - 報告対象者プロファイル")
        self._window.geometry("600x500")
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
        main_frame = ttk.Frame(self._window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側：プロファイルリスト
        left_frame = ttk.LabelFrame(main_frame, text="プロファイル一覧", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self._profile_listbox = tk.Listbox(left_frame, exportselection=False)
        self._profile_listbox.pack(fill=tk.BOTH, expand=True)
        self._profile_listbox.bind("<<ListboxSelect>>", self._on_profile_select)

        # リストボタン
        list_btn_frame = ttk.Frame(left_frame)
        list_btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(list_btn_frame, text="新規", command=self._new_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_btn_frame, text="削除", command=self._delete_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_btn_frame, text="リセット", command=self._reset_profiles).pack(side=tk.RIGHT, padx=2)

        # 右側：プロファイル編集
        right_frame = ttk.LabelFrame(main_frame, text="プロファイル編集", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self._setup_edit_form(right_frame)

    def _setup_edit_form(self, parent: ttk.Frame) -> None:
        """編集フォームをセットアップ"""
        # 名前
        ttk.Label(parent, text="名前:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self._name_var = tk.StringVar()
        self._name_entry = ttk.Entry(parent, textvariable=self._name_var)
        self._name_entry.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=5)

        # 役職
        ttk.Label(parent, text="役職:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self._role_var = tk.StringVar()
        self._role_combo = ttk.Combobox(
            parent,
            textvariable=self._role_var,
            values=["メンバー", "課長", "室長", "部長", "その他"],
        )
        self._role_combo.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=5)

        # 関心事
        ttk.Label(parent, text="関心事:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self._focus_var = tk.StringVar()
        self._focus_combo = ttk.Combobox(
            parent,
            textvariable=self._focus_var,
            values=["納期重視", "方針重視", "コスト重視", "詳細重視", "品質重視"],
        )
        self._focus_combo.grid(row=2, column=1, sticky=tk.EW, pady=2, padx=5)

        # 説明
        ttk.Label(parent, text="説明:").grid(row=3, column=0, sticky=tk.NW, pady=2)
        self._desc_text = tk.Text(parent, height=3)
        self._desc_text.grid(row=3, column=1, sticky=tk.EW, pady=2, padx=5)

        # サマリ文字数
        ttk.Label(parent, text="サマリ文字数:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self._summary_chars_var = tk.StringVar(value="300")
        self._summary_chars_spinbox = ttk.Spinbox(
            parent,
            textvariable=self._summary_chars_var,
            from_=100,
            to=1000,
            width=10,
        )
        self._summary_chars_spinbox.grid(row=4, column=1, sticky=tk.W, pady=2, padx=5)

        # 詳細度
        ttk.Label(parent, text="詳細度:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self._detail_level_var = tk.StringVar(value="medium")
        detail_frame = ttk.Frame(parent)
        detail_frame.grid(row=5, column=1, sticky=tk.W, pady=2, padx=5)
        ttk.Radiobutton(detail_frame, text="低", variable=self._detail_level_var, value="low").pack(side=tk.LEFT)
        ttk.Radiobutton(detail_frame, text="中", variable=self._detail_level_var, value="medium").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(detail_frame, text="高", variable=self._detail_level_var, value="high").pack(side=tk.LEFT)

        # 出力形式
        ttk.Label(parent, text="出力形式:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self._format_var = tk.StringVar(value="markdown")
        format_frame = ttk.Frame(parent)
        format_frame.grid(row=6, column=1, sticky=tk.W, pady=2, padx=5)
        ttk.Radiobutton(format_frame, text="Markdown", variable=self._format_var, value="markdown").pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="Text", variable=self._format_var, value="text").pack(side=tk.LEFT, padx=10)

        # グリッド設定
        parent.columnconfigure(1, weight=1)

        # 保存ボタン
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="保存", command=self._save_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="閉じる", command=self._window.destroy).pack(side=tk.LEFT, padx=5)

    def _load_profiles(self) -> None:
        """プロファイルリストを読み込む"""
        self._profile_listbox.delete(0, tk.END)
        for profile in self._profile_manager.list_profiles():
            self._profile_listbox.insert(tk.END, profile.name)

    def _on_profile_select(self, event) -> None:
        """プロファイル選択時の処理"""
        selection = self._profile_listbox.curselection()
        if not selection:
            return

        name = self._profile_listbox.get(selection[0])
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

        name = self._profile_listbox.get(selection[0])
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
