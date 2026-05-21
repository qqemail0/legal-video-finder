from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, VERTICAL, W, X, Y, StringVar, Tk, messagebox
from tkinter import ttk

from .models import VideoResult
from .providers import create_default_providers
from .search import SearchEngine
from .store import AppStore

REPO_URL = "https://github.com/qqemail0/legal-video-finder"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    return Path.home() / ".legal_video_finder"


class LegalVideoFinderApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Legal Video Finder - 合法影视资源搜索")
        self.root.geometry("1180x760")
        self.root.minsize(960, 640)

        data_dir = project_root() / "data"
        self.engine = SearchEngine(create_default_providers(data_dir))
        self.store = AppStore(user_data_dir() / "app.db")
        self.results: list[VideoResult] = []
        self.favorite_results: list[VideoResult] = []
        self.query_var = StringVar(value="")
        self.status_var = StringVar(value="输入片名、动漫名、电影名或关键词后搜索。")

        self._configure_style()
        self._build_layout(data_dir)
        self._refresh_favorites()
        self._refresh_history()

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        self.root.configure(bg="#0f1412")
        style.configure(".", font=("Microsoft YaHei UI", 10), background="#0f1412", foreground="#edf5ef")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"), foreground="#f3f6d8")
        style.configure("Subtle.TLabel", foreground="#9fb4a8")
        style.configure("TFrame", background="#0f1412")
        style.configure("Panel.TFrame", background="#18211d", relief="flat")
        style.configure("TButton", padding=(14, 8), background="#d9f27d", foreground="#101510")
        style.map("TButton", background=[("active", "#f3ffb0")])
        style.configure("Treeview", background="#121a17", fieldbackground="#121a17", foreground="#edf5ef", rowheight=30)
        style.configure("Treeview.Heading", background="#243229", foreground="#f3f6d8", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("TNotebook", background="#0f1412", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8), background="#18211d", foreground="#cbd9ce")
        style.map("TNotebook.Tab", background=[("selected", "#d9f27d")], foreground=[("selected", "#101510")])

    def _build_layout(self, data_dir: Path) -> None:
        top = ttk.Frame(self.root, padding=(24, 18, 24, 10))
        top.pack(fill=X)

        title_group = ttk.Frame(top)
        title_group.pack(side=LEFT, fill=X, expand=True)
        ttk.Label(title_group, text="Legal Video Finder", style="Title.TLabel").pack(anchor=W)
        ttk.Label(
            title_group,
            text="合法影视、动漫、公开视频与官方入口聚合搜索，不抓取盗版播放源。",
            style="Subtle.TLabel",
        ).pack(anchor=W, pady=(4, 0))
        ttk.Button(top, text="开源项目", command=lambda: webbrowser.open(REPO_URL)).pack(side=RIGHT)

        search_bar = ttk.Frame(self.root, padding=(24, 8, 24, 16), style="Panel.TFrame")
        search_bar.pack(fill=X, padx=24)
        entry = ttk.Entry(search_bar, textvariable=self.query_var, font=("Microsoft YaHei UI", 12))
        entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10), ipady=6)
        entry.bind("<Return>", lambda _event: self.run_search())
        ttk.Button(search_bar, text="搜索", command=self.run_search).pack(side=LEFT, padx=(0, 8))
        ttk.Button(search_bar, text="清空", command=self.clear_results).pack(side=LEFT)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=24, pady=(16, 0))
        self._build_search_tab()
        self._build_favorites_tab()
        self._build_settings_tab(data_dir)

        status = ttk.Label(self.root, textvariable=self.status_var, style="Subtle.TLabel", padding=(24, 12))
        status.pack(fill=X)

    def _build_search_tab(self) -> None:
        frame = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(frame, text="搜索结果")
        columns = ("title", "year", "kind", "provider", "confidence", "legal")
        self.result_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        headings = {
            "title": "标题",
            "year": "年份",
            "kind": "类型",
            "provider": "来源",
            "confidence": "匹配度",
            "legal": "合法性",
        }
        widths = {"title": 300, "year": 70, "kind": 130, "provider": 140, "confidence": 90, "legal": 170}
        for column in columns:
            self.result_tree.heading(column, text=headings[column])
            self.result_tree.column(column, width=widths[column], anchor=W)
        self.result_tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.result_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_detail())

        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=LEFT, fill=Y)

        detail_panel = ttk.Frame(frame, padding=(16, 0, 0, 0))
        detail_panel.pack(side=RIGHT, fill=BOTH, expand=False)
        self.detail_text = ttk.Label(detail_panel, text="选择一个结果查看详情。", wraplength=360, justify=LEFT)
        self.detail_text.pack(fill=BOTH, expand=True, anchor=W)
        ttk.Button(detail_panel, text="打开观看入口", command=self.open_selected).pack(fill=X, pady=(12, 8))
        ttk.Button(detail_panel, text="收藏", command=self.favorite_selected).pack(fill=X, pady=(0, 8))
        ttk.Button(detail_panel, text="打开来源页", command=self.open_selected_source).pack(fill=X)

    def _build_favorites_tab(self) -> None:
        frame = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(frame, text="收藏")
        columns = ("title", "year", "kind", "provider", "legal")
        self.favorite_tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)
        for column, title in zip(columns, ["标题", "年份", "类型", "来源", "合法性"]):
            self.favorite_tree.heading(column, text=title)
            self.favorite_tree.column(column, width=170 if column != "title" else 360, anchor=W)
        self.favorite_tree.pack(fill=BOTH, expand=True)
        button_bar = ttk.Frame(frame)
        button_bar.pack(fill=X, pady=(12, 0))
        ttk.Button(button_bar, text="打开收藏", command=self.open_favorite).pack(side=LEFT, padx=(0, 8))
        ttk.Button(button_bar, text="删除收藏", command=self.remove_favorite).pack(side=LEFT)

    def _build_settings_tab(self, data_dir: Path) -> None:
        frame = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(frame, text="设置与说明")
        custom_path = data_dir / "custom_sources.json"
        text = (
            "合法源策略\n\n"
            "1. 内置片库只放公共版权、开放授权或官方可访问入口。\n"
            "2. Internet Archive 结果会打开原始档案页，具体版权和地区限制以原页面为准。\n"
            "3. Jikan 与 TVmaze 主要提供元数据、预告片、官方站点或资料页。\n"
            "4. 需要添加自己的合法资源站时，复制 data/custom_sources.example.json 为 data/custom_sources.json。\n\n"
            f"自定义源文件：{custom_path}\n"
            f"开源地址：{REPO_URL}"
        )
        ttk.Label(frame, text=text, wraplength=900, justify=LEFT).pack(anchor=W)
        history_frame = ttk.Frame(frame)
        history_frame.pack(fill=BOTH, expand=True, pady=(18, 0))
        ttk.Label(history_frame, text="最近搜索", style="Title.TLabel").pack(anchor=W)
        self.history_tree = ttk.Treeview(history_frame, columns=("query", "time"), show="headings", height=8)
        self.history_tree.heading("query", text="关键词")
        self.history_tree.heading("time", text="时间")
        self.history_tree.column("query", width=320, anchor=W)
        self.history_tree.column("time", width=220, anchor=W)
        self.history_tree.pack(fill=X, pady=(8, 0))

    def run_search(self) -> None:
        query = self.query_var.get().strip()
        if not query:
            messagebox.showinfo("提示", "请输入搜索关键词。")
            return
        self.status_var.set("正在并行搜索合法来源...")
        self.store.add_history(query)
        self._refresh_history()
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()

    def _search_worker(self, query: str) -> None:
        outcome = self.engine.search(query)
        self.root.after(0, lambda: self._render_search_outcome(outcome.results, outcome.errors))

    def _render_search_outcome(self, results: list[VideoResult], errors: list[str]) -> None:
        self.results = results
        self.result_tree.delete(*self.result_tree.get_children())
        for index, item in enumerate(results):
            self.result_tree.insert(
                "",
                END,
                iid=str(index),
                values=(item.title, item.year, item.kind, item.provider, f"{item.confidence:.0f}%", item.legal_status),
            )
        status = f"找到 {len(results)} 条结果。"
        if errors:
            status += " 部分来源暂时不可用：" + "；".join(errors[:3])
        self.status_var.set(status)
        if results:
            self.result_tree.selection_set("0")
            self.show_selected_detail()

    def clear_results(self) -> None:
        self.query_var.set("")
        self.results = []
        self.result_tree.delete(*self.result_tree.get_children())
        self.detail_text.configure(text="选择一个结果查看详情。")
        self.status_var.set("已清空。")

    def selected_result(self) -> VideoResult | None:
        selection = self.result_tree.selection()
        if not selection:
            return None
        index = int(selection[0])
        return self.results[index] if index < len(self.results) else None

    def show_selected_detail(self) -> None:
        item = self.selected_result()
        if not item:
            return
        tags = " / ".join(item.tags) if item.tags else "无"
        self.detail_text.configure(
            text=(
                f"{item.title}\n\n"
                f"年份：{item.year or '未知'}\n"
                f"类型：{item.kind}\n"
                f"来源：{item.provider}\n"
                f"匹配度：{item.confidence:.0f}%\n"
                f"标签：{tags}\n\n"
                f"说明：{item.description or '暂无简介'}\n\n"
                f"合法性：{item.legal_status}\n"
                f"{item.legal_note}\n\n"
                f"观看入口：{item.watch_url or '无'}\n"
                f"来源页：{item.source_url or '无'}"
            )
        )

    def open_selected(self) -> None:
        item = self.selected_result()
        if item and item.primary_url:
            webbrowser.open(item.primary_url)

    def open_selected_source(self) -> None:
        item = self.selected_result()
        if item and item.source_url:
            webbrowser.open(item.source_url)

    def favorite_selected(self) -> None:
        item = self.selected_result()
        if not item:
            return
        self.store.add_favorite(item)
        self._refresh_favorites()
        self.status_var.set(f"已收藏：{item.title}")

    def _refresh_favorites(self) -> None:
        self.favorite_results = self.store.list_favorites()
        if not hasattr(self, "favorite_tree"):
            return
        self.favorite_tree.delete(*self.favorite_tree.get_children())
        for index, item in enumerate(self.favorite_results):
            self.favorite_tree.insert("", END, iid=str(index), values=(item.title, item.year, item.kind, item.provider, item.legal_status))

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_tree"):
            return
        self.history_tree.delete(*self.history_tree.get_children())
        for query, created_at in self.store.list_history():
            self.history_tree.insert("", END, values=(query, created_at))

    def selected_favorite(self) -> VideoResult | None:
        selection = self.favorite_tree.selection()
        if not selection:
            return None
        index = int(selection[0])
        return self.favorite_results[index] if index < len(self.favorite_results) else None

    def open_favorite(self) -> None:
        item = self.selected_favorite()
        if item and item.primary_url:
            webbrowser.open(item.primary_url)

    def remove_favorite(self) -> None:
        item = self.selected_favorite()
        if not item:
            return
        self.store.remove_favorite(item.primary_url)
        self._refresh_favorites()


def main() -> None:
    root = Tk()
    app = LegalVideoFinderApp(root)
    root.mainloop()

