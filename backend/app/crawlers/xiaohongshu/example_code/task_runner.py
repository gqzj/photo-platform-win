from __future__ import annotations

import json
import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from PIL import Image as PILImage
from playwright.sync_api import sync_playwright
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import CrawlerCookie, CrawlerTask, ImageAsset
from app.settings import settings
from app.crawlers.xiaohongshu.xiaohongshu_db.models import (
    Post,
    PostComment,
    PostMedia,
)

logger = logging.getLogger(__name__)


class CrawlError(RuntimeError):
    pass


def _get_storage_dir() -> Path:
    """
    获取存储目录：优先使用配置文件中的 local_image_dir，否则使用 settings.storage_dir
    """
    config_file = Path(__file__).parent.parent.parent.parent / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                local_dir = config.get("local_image_dir")
                if local_dir and local_dir.strip():
                    return Path(local_dir.strip())
        except Exception:
            pass
    return Path(settings.storage_dir)


def _get_full_storage_path(relative_path: str) -> Path:
    """
    将相对路径转换为完整路径（相对于配置的存储目录）
    """
    storage_base = _get_storage_dir()
    # 统一处理路径分隔符
    relative_path = relative_path.replace("\\", "/")
    return storage_base / relative_path


def _now() -> datetime:
    return datetime.utcnow()


def _log(task_id: int, msg: str, **kv: Any) -> None:
    """
    同时用 logger + print 打日志，避免 uvicorn logging 配置导致看不到。
    """
    payload = {"task_id": task_id, "msg": msg, **kv}
    try:
        logger.info("crawl %s", payload)
    except Exception:
        pass
    try:
        print(f"[crawl] {payload}", flush=True)
    except Exception:
        pass


def _safe_dir_name(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.U)
    return s[:80] or "xhs"


def _download_image(
    url: str,
    out_dir: Path,
    filename_hint: str,
    storage_base: Path,
    task_id: int = 0,
) -> tuple[str | None, str]:
    """
    Downloads image and returns (relative_path, status)
    relative_path is relative to storage_base
    """
    try:
        # 确保目录存在
        out_dir.mkdir(parents=True, exist_ok=True)
        _log(
            task_id,
            "download_image_start",
            url=url[:100],
            out_dir=str(out_dir),
            storage_base=str(storage_base),
        )

        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        parsed = urlparse(url)
        name = os.path.basename(parsed.path) or filename_hint
        if "." not in name:
            name = f"{name}.jpg"
        name = _safe_dir_name(name)
        path = out_dir / name
        path.write_bytes(resp.content)
        _log(
            task_id,
            "download_image_written",
            path=str(path),
            size=len(resp.content),
        )

        # 计算相对路径（相对于 storage_base）
        try:
            relative_path = str(path.relative_to(storage_base))
            # 统一使用正斜杠作为路径分隔符（跨平台兼容）
            relative_path = relative_path.replace("\\", "/")
            _log(
                task_id, "download_image_success", relative_path=relative_path
            )
            return relative_path, "success"
        except ValueError as e:
            # 如果无法计算相对路径，返回 None
            _log(
                task_id,
                "download_image_relative_path_failed",
                error=str(e),
                path=str(path),
                storage_base=str(storage_base),
            )
            return None, "failed"
    except Exception as e:
        _log(task_id, "download_image_failed", error=str(e), url=url[:100])
        return None, "failed"


def _parse_hash_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    out: list[str] = []
    for t in tags:
        s = (t or "").strip()
        if not s:
            continue
        out.append(s)
    # 去重保序
    return list(dict.fromkeys(out))


def _compute_image_meta(local_path: str) -> dict[str, Any]:
    """
    基于本地文件计算 image_hash/width/height/format。
    """
    p = Path(local_path)
    data = p.read_bytes()
    h = hashlib.sha256(data).hexdigest()

    width: int | None = None
    height: int | None = None
    fmt: str | None = None
    try:
        with PILImage.open(p) as im:
            width, height = im.size
            fmt = (im.format or "").lower() or None
    except Exception:
        pass
    return {"image_hash": h, "width": width, "height": height, "format": fmt}


def _upsert_image_asset(
    db: Session,
    *,
    filename: str,
    storage_path: str,  # 相对路径
    original_url: str | None,
    visit_url: str | None,
    keyword: str | None,
    hash_tags: list[str],
) -> None:
    """
    将抓取到的图片写入 app 的 images 表（ImageAsset）。
    去重优先使用 image_hash，其次用 original_url。
    storage_path 是相对路径（相对于配置的存储目录）。
    """
    # 计算完整路径用于读取文件元数据
    storage_base = _get_storage_dir()
    full_path = storage_base / storage_path
    meta = _compute_image_meta(str(full_path))
    image_hash = meta.get("image_hash")
    if image_hash:
        exists = (
            db.query(ImageAsset)
            .filter(ImageAsset.image_hash == image_hash)
            .first()
        )
        if exists is not None:
            return
    if original_url:
        exists2 = (
            db.query(ImageAsset)
            .filter(ImageAsset.original_url == original_url)
            .first()
        )
        if exists2 is not None:
            return

    img = ImageAsset(
        filename=filename,
        storage_path=storage_path,
        original_url=original_url,
        storage_mode="local",
        source_site="xiaohongshu",
        keyword=keyword,
        hash_tags_json=json.dumps(hash_tags, ensure_ascii=False),
        visit_url=visit_url,
        image_hash=image_hash,
        width=meta.get("width"),
        height=meta.get("height"),
        format=meta.get("format"),
        status="ready",
    )
    db.add(img)


def _parse_int_cn(s: str | None) -> int:
    """
    Parse counts like '123', '1.2万' into int.
    """
    if not s:
        return 0
    v = str(s).strip()
    v = v.replace(",", "")
    m = re.match(r"^(\d+(?:\.\d+)?)(万)?$", v)
    if not m:
        return 0
    num = float(m.group(1))
    if m.group(2) == "万":
        num *= 10000
    return int(num)


def _db_post_exists(db: Session, post_id: str) -> bool:
    return db.query(Post).filter(Post.post_id == post_id).first() is not None


def _db_comment_exists(db: Session, comment_id: str) -> bool:
    return (
        db.query(PostComment)
        .filter(PostComment.comment_id == comment_id)
        .first()
        is not None
    )


def _task_set_progress(
    db: Session,
    task_id: int,
    *,
    current_keyword: str | None = None,
    inc_posts: int = 0,
    inc_comments: int = 0,
    inc_media: int = 0,
    progress: dict[str, Any] | None = None,
) -> None:
    sets: list[str] = ["updated_at=:updated_at"]
    params: dict[str, Any] = {"task_id": task_id, "updated_at": _now()}
    if current_keyword is not None:
        sets.append("current_keyword=:current_keyword")
        params["current_keyword"] = current_keyword
    if inc_posts:
        sets.append("processed_posts=processed_posts+:inc_posts")
        params["inc_posts"] = int(inc_posts)
    if inc_comments:
        sets.append("processed_comments=processed_comments+:inc_comments")
        params["inc_comments"] = int(inc_comments)
    if inc_media:
        sets.append("downloaded_media=downloaded_media+:inc_media")
        params["inc_media"] = int(inc_media)
    if progress is not None:
        sets.append("progress_json=:progress_json")
        params["progress_json"] = json.dumps(progress, ensure_ascii=False)
    stmt = text(
        f"UPDATE crawler_tasks SET {', '.join(sets)} WHERE id=:task_id"
    )
    db.execute(stmt, params)
    db.commit()


def _get_latest_succeeded_cookie(db: Session) -> CrawlerCookie | None:
    row = (
        db.execute(
            text(
                """
                SELECT id FROM crawler_cookies
                WHERE platform='xiaohongshu'
                  AND status='succeeded'
                  AND cookie_json IS NOT NULL
                ORDER BY id DESC
                LIMIT 1
                """
            )
        )
        .fetchone()
    )
    if not row:
        return None
    return db.get(CrawlerCookie, int(row[0]))


def _require_storage_state(cookie: CrawlerCookie) -> dict[str, Any]:
    if not cookie.cookie_json:
        raise CrawlError("cookie_json is empty")
    try:
        return json.loads(cookie.cookie_json)
    except Exception as e:
        raise CrawlError(f"invalid cookie_json: {e}")


def _extract_post_id_from_url(url: str) -> str:
    m = re.findall(r"/explore/(\w+)", url)
    if not m:
        raise CrawlError("cannot extract post_id from url")
    return m[0]


def _search_keyword(page, task_id: int, kw: str) -> None:
    """
    Playwright 的 get_by_role/get_by_placeholder 返回的是 locator，不会在这里报错；
    只有在 click/fill 时才会因 selector 不匹配/不可点击而超时。
    所以这里用“多策略逐个尝试”的方式，并在失败时截图。
    """
    candidates: list[tuple[str, Any]] = [
        ("role:name=搜索小红书", page.get_by_role("textbox", name="搜索小红书")),
        ("placeholder=搜索小红书", page.get_by_placeholder("搜索小红书")),
        (
            "css:input[placeholder*='搜索']",
            page.locator("input[placeholder*='搜索']"),
        ),
        (
            "css:aria/placeholder contains 搜索",
            page.locator(
                "input[aria-label*='搜索'], input[placeholder*='搜索']"
            ).first,
        ),
    ]

    last_err: Exception | None = None
    for idx, (desc, box) in enumerate(candidates, start=1):
        try:
            _log(task_id, "search_try", idx=idx, selector=desc, keyword=kw)
            box.click(timeout=10_000)
            box.fill(kw, timeout=10_000)
            box.press("Enter", timeout=10_000)
            _log(task_id, "search_sent", idx=idx, selector=desc, keyword=kw)
            return
        except Exception as e:
            last_err = e
            _log(
                task_id,
                "search_try_failed",
                idx=idx,
                selector=desc,
                err=str(e),
            )
            continue

    storage_base = _get_storage_dir()
    shot_dir = storage_base / "debug" / "xhs"
    shot_dir.mkdir(parents=True, exist_ok=True)
    shot_path = shot_dir / f"task_{task_id}_search_box_error.png"
    try:
        page.screenshot(path=str(shot_path), full_page=True)
    except Exception:
        pass
    raise CrawlError(
        f"search box not found/clickable: {last_err}; screenshot={shot_path}"
    )


def _crawl_open_post_and_persist(
    db: Session, page, *, search_keyword: str | None, task_id: int = 0
) -> tuple[int, int, int]:
    url = page.url
    post_id = _extract_post_id_from_url(url)
    if _db_post_exists(db, post_id):
        return (0, 0, 0)

    desc = ""
    if page.locator("#detail-desc > span > span").count() > 0:
        desc = page.locator("#detail-desc > span > span").all()[0].inner_text()
    title = ""
    if page.locator("#detail-title").count() > 0:
        title = page.locator("#detail-title").inner_text()

    like_count = ""
    collect_count = ""
    comment_count = ""
    try:
        like_count = page.locator(
            "div.interact-container span.like-wrapper"
        ).inner_text()
    except Exception:
        pass
    try:
        collect_count = page.locator(
            "div.interact-container span.collect-wrapper"
        ).inner_text()
    except Exception:
        pass
    try:
        comment_count = page.locator(
            "div.interact-container span.chat-wrapper"
        ).inner_text()
    except Exception:
        pass

    author_name = ""
    author_id = ""
    try:
        author_name = page.locator("span.username").all()[0].inner_text()
        author_url = (
            page.locator("div.info > a").all()[0].get_attribute("href") or ""
        )
        m = re.findall(r"/profile/(\w+)", author_url)
        author_id = m[0] if m else ""
    except Exception:
        pass

    tags: list[str] = []
    try:
        tags = [
            tag.inner_text() for tag in page.locator("#detail-desc a").all()
        ]
    except Exception:
        pass
    hash_tags = _parse_hash_tags(tags)

    # hover to get follower stats
    follower_count = 0
    like_collect_count = 0
    try:
        page.locator(
            "div.author-container .author-wrapper .info"
        ).all()[0].hover()
        page.wait_for_timeout(1000)
        user_info = [
            u.inner_text()
            for u in page.locator("div.interaction-info a").all()
        ]
        if len(user_info) >= 3:
            follower_count = _parse_int_cn(user_info[1].replace("粉丝", ""))
            like_collect_count = _parse_int_cn(
                user_info[2].replace("获赞与收藏", "")
            )
    except Exception:
        pass

    now = _now()
    post = Post(
        post_id=post_id,
        title=title or None,
        content=desc or None,
        author_id=author_id or None,
        author_name=author_name or None,
        author_follower_count=follower_count,
        author_like_collect_count=like_collect_count,
        like_count=_parse_int_cn(like_count),
        comment_count=_parse_int_cn(comment_count),
        collect_count=_parse_int_cn(collect_count),
        post_type="image",
        tags=tags or None,
        search_keyword=search_keyword,
        publish_time=None,
        crawl_time=now,
        update_time=now,
    )
    db.add(post)
    db.flush()
    inserted_posts = 1

    # comments (minimal): parent + replies
    inserted_comments = 0
    try:
        parent_comments = page.locator(
            "div.list-container > .parent-comment"
        ).all()
        for parent in parent_comments[:50]:
            if parent.locator(">div.comment-item").count() == 0:
                continue
            comment_text = ""
            comment_id = ""
            avatar = None
            user_id = None
            user_name = None
            try:
                comment_text = (
                    parent.locator(">div.comment-item span.note-text")
                    .all()[0]
                    .inner_text()
                )
                comment_id = (
                    parent.locator(">div.comment-item")
                    .first.get_attribute("id")
                    or ""
                )
                if parent.locator("div.avatar a img").count() > 0:
                    avatar = (
                        parent.locator("div.avatar a img")
                        .first.get_attribute("src")
                    )
                user_id = (
                    parent.locator("div.author a")
                    .first.get_attribute("data-user-id")
                )
                user_name = parent.locator("div.author a").first.inner_text()
            except Exception:
                pass

            if comment_id and not _db_comment_exists(db, comment_id):
                db.add(
                    PostComment(
                        comment_id=comment_id,
                        post_id=post_id,
                        parent_comment_id=None,
                        user_id=user_id,
                        user_name=user_name,
                        user_avatar=avatar,
                        content=comment_text,
                        like_count=0,
                        reply_count=0,
                        comment_time=None,
                        crawl_time=now,
                    )
                )
                inserted_comments += 1

            if (
                parent.locator("div.reply-container").count() > 0
                and comment_id
            ):
                sub_items = parent.locator(
                    "div.reply-container div.comment-item.comment-item-sub"
                ).all()
                for sub in sub_items[:50]:
                    sub_id = sub.get_attribute("id") or ""
                    if not sub_id or _db_comment_exists(db, sub_id):
                        continue
                    try:
                        sub_avatar = (
                            sub.locator("div.avatar a img")
                            .first.get_attribute("src")
                        )
                        sub_user_id = (
                            sub.locator("div.avatar a")
                            .first.get_attribute("data-user-id")
                        )
                        sub_user_name = (
                            sub.locator("div.right div.author a")
                            .first.inner_text()
                        )
                        sub_content = (
                            sub.locator("div.right div.content span")
                            .first.inner_text()
                        )
                    except Exception:
                        continue
                    db.add(
                        PostComment(
                            comment_id=sub_id,
                            post_id=post_id,
                            parent_comment_id=comment_id,
                            user_id=sub_user_id,
                            user_name=sub_user_name,
                            user_avatar=sub_avatar,
                            content=sub_content,
                            like_count=0,
                            reply_count=0,
                            comment_time=None,
                            crawl_time=now,
                        )
                    )
                    inserted_comments += 1
    except Exception:
        pass

    # media images
    storage_base = _get_storage_dir()
    out_dir = (
        storage_base
        / "xiaohongshu"
        / _safe_dir_name(search_keyword or "target_url")
        / post_id
    )
    success_media = 0
    try:
        imgs = page.locator("div.swiper-wrapper > div img").all()
        if len(imgs) > 2:
            imgs = imgs[1:-1]
        for idx, img in enumerate(imgs[:20]):
            media_url = img.get_attribute("src") or ""
            if not media_url:
                continue
            relative_path, status = _download_image(
                media_url,
                out_dir,
                f"image_{post_id}_{idx}.jpg",
                storage_base,
                task_id,
            )
            if status == "success":
                success_media += 1
                try:
                    _upsert_image_asset(
                        db,
                        filename=os.path.basename(relative_path or "")
                        or f"{post_id}_{idx}.jpg",
                        storage_path=relative_path or "",
                        original_url=media_url,
                        visit_url=url,
                        keyword=search_keyword,
                        hash_tags=hash_tags,
                    )
                except Exception:
                    pass
            db.add(
                PostMedia(
                    post_id=post_id,
                    media_type="image",
                    media_url=media_url,
                    media_local_path=relative_path,  # 保存相对路径
                    thumbnail_url=None,
                    file_size=None,
                    duration=None,
                    width=None,
                    height=None,
                    sort_order=idx,
                    download_status=status,
                    download_time=now if status == "success" else None,
                    create_time=now,
                )
            )
    except Exception:
        pass
    return (inserted_posts, inserted_comments, success_media)


def run_xiaohongshu_task(db: Session, task_id: int) -> None:
    # 断点兜底：解决 BackgroundTasks 在线程池里跑、且入口执行过快导致“断点没命中”的问题。
    # 用法：启动后端时加环境变量 XHS_DEBUG_BREAK=1
    if os.getenv("XHS_DEBUG_BREAK") == "1":
        try:
            import debugpy  # type: ignore

            debugpy.breakpoint()
        except Exception:
            pass

    task = db.get(CrawlerTask, task_id)
    if task is None:
        raise CrawlError("task not found")

    cookie = _get_latest_succeeded_cookie(db)
    if cookie is None:
        raise CrawlError(
            "no succeeded xiaohongshu cookie found; fetch cookie first"
        )
    state = _require_storage_state(cookie)

    # 打印 cookie_json（脱敏：长度 + 前后片段）
    cj = cookie.cookie_json or ""
    if cj:
        _log(
            task_id,
            "cookie_json_loaded",
            cookie_id=cookie.id,
            cookie_len=len(cj),
            head=cj[:120],
            tail=cj[-120:] if len(cj) > 120 else cj,
        )
    else:
        _log(task_id, "cookie_json_empty", cookie_id=cookie.id)

    # prepare keywords
    try:
        keywords = json.loads(task.keywords_json) if task.keywords_json else []
        if not isinstance(keywords, list):
            keywords = []
        keywords = [str(x).strip() for x in keywords if str(x).strip()]
    except Exception:
        keywords = []

    task_type = (task.task_type or "keyword").strip()
    task.status = "running"
    task.last_error = None
    task.started_at = _now()
    task.finished_at = None
    task.current_keyword = None
    task.progress_json = json.dumps(
        {"phase": "start"}, ensure_ascii=False
    )
    task.processed_posts = 0
    task.processed_comments = 0
    task.downloaded_media = 0
    task.updated_at = _now()
    db.commit()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=state)
        page = context.new_page()
        try:
            _log(task_id, "goto_explore")
            page.goto("https://www.xiaohongshu.com/explore")
            page.wait_for_timeout(5000)

            if task_type == "target_url":
                if not task.target_url:
                    raise CrawlError("target_url task requires target_url")
                page.goto(task.target_url)
                page.wait_for_timeout(5000)
                p_inc, c_inc, m_inc = _crawl_open_post_and_persist(
                    db, page, search_keyword=None, task_id=task_id
                )
                db.commit()
                _task_set_progress(
                    db,
                    task_id,
                    current_keyword=None,
                    inc_posts=p_inc,
                    inc_comments=c_inc,
                    inc_media=m_inc,
                    progress={
                        "phase": "target_url",
                        "post_inc": p_inc,
                        "comment_inc": c_inc,
                        "media_inc": m_inc,
                    },
                )
                db.commit()
            else:
                if not keywords:
                    raise CrawlError("keyword task requires keywords")

                for kw in keywords[:10]:
                    _log(task_id, "keyword_start", keyword=kw)
                    _task_set_progress(
                        db,
                        task_id,
                        current_keyword=kw,
                        progress={"phase": "search", "keyword": kw},
                    )
                    page.goto("https://www.xiaohongshu.com/explore")
                    page.wait_for_timeout(3000)
                    _search_keyword(page, task_id=task_id, kw=kw)
                    page.wait_for_timeout(2000)
                    try:
                        page.get_by_text("筛选").click()
                        page.get_by_text("筛选").click()
                        page.get_by_text("最多点赞").click()
                        page.locator("span").filter(has_text="图文").click()
                        page.get_by_text("已筛选").click()
                    except Exception:
                        pass
                    page.wait_for_timeout(5000)

                    topic_set: set[str] = set()
                    has_new = True
                    loops = 0
                    while has_new and loops < 3:
                        loops += 1
                        has_new = False
                        sections = page.locator("section").all()
                        _log(
                            task_id,
                            "sections_found",
                            keyword=kw,
                            count=len(sections),
                            loop=loops,
                        )
                        for section in sections:
                            if section.locator("div > a").count() == 0:
                                continue
                            href = (
                                section.locator("div > a")
                                .first.get_attribute("href")
                                or ""
                            )
                            m = re.findall(r"/explore/(\w+)", href)
                            if not m:
                                continue
                            topic_id = m[0]
                            if topic_id in topic_set:
                                continue
                            topic_set.add(topic_id)
                            has_new = True
                            _log(
                                task_id,
                                "open_detail_click",
                                keyword=kw,
                                topic_id=topic_id,
                                href=href,
                            )

                            try:
                                section.click()
                                page.wait_for_timeout(5000)
                                p_inc, c_inc, m_inc = (
                                    _crawl_open_post_and_persist(
                                        db,
                                        page,
                                        search_keyword=kw,
                                        task_id=task_id,
                                    )
                                )
                                db.commit()
                                if p_inc or c_inc or m_inc:
                                    _task_set_progress(
                                        db,
                                        task_id,
                                        current_keyword=kw,
                                        inc_posts=p_inc,
                                        inc_comments=c_inc,
                                        inc_media=m_inc,
                                        progress={
                                            "phase": "detail",
                                            "keyword": kw,
                                            "post_inc": p_inc,
                                            "comment_inc": c_inc,
                                            "media_inc": m_inc,
                                        },
                                    )
                            finally:
                                try:
                                    page.locator(".close > .reds-icon").click()
                                except Exception:
                                    try:
                                        page.keyboard.press("Escape")
                                    except Exception:
                                        pass
                                page.wait_for_timeout(300)

        finally:
            try:
                context.close()
            finally:
                browser.close()

    task = db.get(CrawlerTask, task_id)
    if task is not None:
        # 如果 0 结果，视为失败（更符合排查/预期）
        if (
            (task.processed_posts or 0) == 0
            and (task.downloaded_media or 0) == 0
        ):
            task.status = "failed"
            task.last_error = (
                "抓取完成但未获得任何帖子/图片，请查看日志与截图（可能是页面 selector 变更或登录失效）"
            )
        else:
            task.status = "succeeded"
        task.finished_at = _now()
        task.current_keyword = None
        task.updated_at = _now()
        task.progress_json = json.dumps(
            {"phase": "done"}, ensure_ascii=False
        )
        db.commit()
