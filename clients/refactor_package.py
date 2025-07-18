#!/usr/bin/env python3
import re
import shutil
from pathlib import Path

OLD_PACKAGE = "io.nekohasekai.sfa"
NEW_PACKAGE = "com.clearpath.sfa"

OLD_PACKAGE_SLASH = OLD_PACKAGE.replace(".", "/")
NEW_PACKAGE_SLASH = NEW_PACKAGE.replace(".", "/")

ANDROID_ROOT = Path("android")
APP_ROOT = ANDROID_ROOT / "app"
PACKAGE_PATH = APP_ROOT / "src"

# $ find . -print | awk -F/ 'tolower($NF) ~ /nekohasekai/'
# ./app/schemas/io.nekohasekai.sfa.database.preference.KeyValueDatabase
# ./app/schemas/io.nekohasekai.sfa.database.ProfileDatabase
# ./app/src/github/java/io/nekohasekai
# ./app/src/main/aidl/io/nekohasekai
# ./app/src/main/java/io/nekohasekai
# ./app/src/minApi21/java/io/nekohasekai
# ./app/src/minApi23/aidl/io/nekohasekai
# ./app/src/minApi23/java/io/nekohasekai
# ./app/src/other/java/io/nekohasekai
# ./app/src/otherLegacy/java/io/nekohasekai
# ./app/src/play/java/io/nekohasekai

OLD_SCHEMAS_BASE_PATH1 = (
    APP_ROOT / "schemas" / Path(f"{OLD_PACKAGE}.database.preference.KeyValueDatabase")
)
NEW_SCHEMAS_BASE_PATH1 = (
    APP_ROOT / "schemas" / Path(f"{NEW_PACKAGE}.database.preference.KeyValueDatabase")
)
OLD_SCHEMAS_BASE_PATH2 = (
    APP_ROOT / "schemas" / Path(f"{OLD_PACKAGE}.database.ProfileDatabase")
)
NEW_SCHEMAS_BASE_PATH2 = (
    APP_ROOT / "schemas" / Path(f"{NEW_PACKAGE}.database.ProfileDatabase")
)
OLD_GITHUB_PATH = PACKAGE_PATH / Path("github/java") / Path(OLD_PACKAGE_SLASH)
NEW_GITHUB_PATH = PACKAGE_PATH / Path("github/java") / Path(NEW_PACKAGE_SLASH)
OLD_AIDL_PATH = PACKAGE_PATH / Path("main/aidl") / Path(OLD_PACKAGE_SLASH)
NEW_AIDL_PATH = PACKAGE_PATH / Path("main/aidl") / Path(NEW_PACKAGE_SLASH)
OLD_PACKAGE_PATH = PACKAGE_PATH / Path("main/java") / Path(OLD_PACKAGE_SLASH)
NEW_PACKAGE_PATH = PACKAGE_PATH / Path("main/java") / Path(NEW_PACKAGE_SLASH)
OLD_MINAPI21_PATH = PACKAGE_PATH / Path("minApi21/java") / Path(OLD_PACKAGE_SLASH)
NEW_MINAPI21_PATH = PACKAGE_PATH / Path("minApi21/java") / Path(NEW_PACKAGE_SLASH)
OLD_MINAPI23_AIDL_PATH = PACKAGE_PATH / Path("minApi23/aidl") / Path(OLD_PACKAGE_SLASH)
NEW_MINAPI23_AIDL_PATH = PACKAGE_PATH / Path("minApi23/aidl") / Path(NEW_PACKAGE_SLASH)
OLD_MINAPI23_PATH = PACKAGE_PATH / Path("minApi23/java") / Path(OLD_PACKAGE_SLASH)
NEW_MINAPI23_PATH = PACKAGE_PATH / Path("minApi23/java") / Path(NEW_PACKAGE_SLASH)
OLD_OTHER_PATH = PACKAGE_PATH / Path("other/java") / Path(OLD_PACKAGE_SLASH)
NEW_OTHER_PATH = PACKAGE_PATH / Path("other/java") / Path(NEW_PACKAGE_SLASH)
OLD_OTHERLEGACY_PATH = PACKAGE_PATH / Path("otherLegacy/java") / Path(OLD_PACKAGE_SLASH)
NEW_OTHERLEGACY_PATH = PACKAGE_PATH / Path("otherLegacy/java") / Path(NEW_PACKAGE_SLASH)
OLD_PLAY_PATH = PACKAGE_PATH / Path("play/java") / Path(OLD_PACKAGE_SLASH)
NEW_PLAY_PATH = PACKAGE_PATH / Path("play/java") / Path(NEW_PACKAGE_SLASH)

# replace and move
# must be folders, not files
PACKAGE_PATH_PAIR_LIST = [
    (OLD_SCHEMAS_BASE_PATH1, NEW_SCHEMAS_BASE_PATH1),
    (OLD_SCHEMAS_BASE_PATH2, NEW_SCHEMAS_BASE_PATH2),
    (OLD_GITHUB_PATH, NEW_GITHUB_PATH),
    (OLD_AIDL_PATH, NEW_AIDL_PATH),
    (OLD_PACKAGE_PATH, NEW_PACKAGE_PATH),
    (OLD_MINAPI21_PATH, NEW_MINAPI21_PATH),
    (OLD_MINAPI23_AIDL_PATH, NEW_MINAPI23_AIDL_PATH),
    (OLD_MINAPI23_PATH, NEW_MINAPI23_PATH),
    (OLD_OTHER_PATH, NEW_OTHER_PATH),
    (OLD_OTHERLEGACY_PATH, NEW_OTHERLEGACY_PATH),
    (OLD_PLAY_PATH, NEW_PLAY_PATH),
]

BUILD_GRADLE_FILE = Path("android/app/build.gradle.kts")

PROGUARD_FILE = Path("android/app/proguard-rules.pro")

PERFORMANCE_GRADLE_FILE = Path("android/gradle.properties")

VERSION_FILE = Path("android/version.properties")

# replace but keep original location
# may be folders or files
PACKAGE_PATH_LIST_KEEP = [
    PACKAGE_PATH,
    BUILD_GRADLE_FILE,
    Path("android/build.gradle.kts"),
    PROGUARD_FILE,
    PERFORMANCE_GRADLE_FILE,
    Path("android/app/src/main/resources/META-INF/xposed/java_init.list"),
    Path("android/app/lint.xml"),
]

TEXT_EXT = {
    ".kt",
    ".java",
    ".xml",
    ".gradle",
    ".kts",
    ".properties",
    ".json",
    ".txt",
    ".mk",
    ".pro",
    ".aidl",
}

EXECUTE_EXT = {
    ".aar",
    ".so",
    ".dll",
    ".dylib",
    ".exe",
    ".bin",
    ".apk",
    ".ipa",
    ".app",
    ".xctest",
    ".jar",
}

ENABLE_PROGUARD = True
REPLACE_PROGUARD = True
PROGUARD_CONTENT = """
-keep class com.itsaky.androidide.treesitter.** { *; }

# These compile-time stubs must retain their framework names so the boot
# classloader resolves Android's real hidden Binder interfaces at runtime.
-keep class android.content.IIntentReceiver { *; }
-keep class android.content.IIntentSender { *; }
-keep class android.content.IIntentSender$Stub { *; }

-dontwarn io.github.libxposed.annotation.**
-keep class $NEW_PACKAGE.xposed.XposedInit { public *; }
-keep class $NEW_PACKAGE.xposed.XposedLegacyInit { public *; }
""".replace("$NEW_PACKAGE", NEW_PACKAGE)

# PERFORMANCE_GRADLE_CONTENT = """
# """


def replace_content(
    text: str, old_pkg: str, new_pkg: str, include_slashes: bool = True
) -> str:
    dot_pat = re.escape(old_pkg)
    text = re.sub(dot_pat, new_pkg, text)
    if include_slashes:
        slash_pat = re.escape(old_pkg.replace(".", "/"))
        text = re.sub(slash_pat, new_pkg.replace(".", "/"), text)
    return text


def replace_in_file(path: Path, old_pkg: str, new_pkg: str, inplace=True):
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    new_content = replace_content(content, old_pkg, new_pkg)
    if new_content == content:
        return False
    if inplace:
        path.write_text(new_content, encoding="utf-8")
    else:
        return new_content
    return True


def copy_and_replace_tree(src: Path, dst: Path, old_pkg: str, new_pkg: str):
    if not src.exists():
        print(f"Source path does not exist: {src}")
        return
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        dst_item = dst / item.name

        if item.is_dir():
            copy_and_replace_tree(item, dst_item, old_pkg, new_pkg)
            continue

        if not item.is_file():
            continue

        try:
            if item.suffix in TEXT_EXT:
                content = item.read_text(encoding="utf-8", errors="ignore")
                new_content = replace_content(content, old_pkg, new_pkg)
                dst_item.parent.mkdir(parents=True, exist_ok=True)
                dst_item.write_text(new_content, encoding="utf-8")
                try:
                    shutil.copystat(item, dst_item)
                except Exception:
                    pass
                print(f"copy_and_replace_tree update text: {dst_item}")
            else:
                dst_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst_item)
                if item.suffix not in EXECUTE_EXT:
                    print(f"Unmatched file: {item}")
                else:
                    print(f"Matched file: {item}")
        except Exception as e:
            print(f"Copy failed: {item} -> {dst_item}: {e}")


def remove_empty_parents(start: Path, stop_at: Path):
    current = start
    while current != stop_at and current.parent != current:
        if current.exists():
            try:
                if not any(current.iterdir()):
                    current.rmdir()
            except Exception:
                pass
        current = current.parent


def _is_within(child: Path, parent: Path) -> bool:
    """Return True if child path is inside parent path."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def replace_package_res(path: Path, old_pkg: str, new_pkg: str):
    if not path.is_file():
        return False
    # exclude PACKAGE_PATH_PAIR_LIST
    for old_path, new_path in PACKAGE_PATH_PAIR_LIST:
        if _is_within(path, old_path) or _is_within(path, new_path):
            return False
    if replace_in_file(path, old_pkg, new_pkg, inplace=True):
        print(f"Resource files updated: {path}")
        return True


def rewrite_version(path: Path):
    if not path.is_file():
        return False
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    original = content

    # 覆写 VERSION_CODE=1
    content = re.sub(
        r"(?m)^(\s*VERSION_CODE\s*=\s*)([^\r\n]*)",
        lambda m: f"{m.group(1)}1",
        content,
    )

    # 若 VERSION_NAME 不含 -dhr60，则末尾追加 -dhr60
    def _name_repl(m: re.Match) -> str:
        prefix = m.group(1)
        value = m.group(2).strip()
        if "-dhr60" in value:
            return f"{prefix}{value}"
        return f"{prefix}{value}-dhr60"

    content = re.sub(
        r"(?m)^(\s*VERSION_NAME\s*=\s*)([^\r\n]*)",
        _name_repl,
        content,
    )

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    print(f"Old package: {OLD_PACKAGE}")
    print(f"New package: {NEW_PACKAGE}")
    for old_path, new_path in PACKAGE_PATH_PAIR_LIST:
        print(f"Old package path: {old_path}")
        print(f"New package path: {new_path}")

    # 检查是否已替换，防止重复执行
    if not replace_in_file(BUILD_GRADLE_FILE, OLD_PACKAGE, NEW_PACKAGE):
        print("Package name already updated.")
        return

    # 创建新的包目录结构
    NEW_PACKAGE_PATH.mkdir(parents=True, exist_ok=True)

    # 复制并替换源代码
    for old_path, new_path in PACKAGE_PATH_PAIR_LIST:
        if old_path.exists():
            copy_and_replace_tree(old_path, new_path, OLD_PACKAGE, NEW_PACKAGE)
        else:
            print(f"Skip missing source path: {old_path}")

    # 处理其他资源文件（包含子目录），但排除代码包目录
    for path in PACKAGE_PATH_LIST_KEEP:
        if path.is_file():
            # 如果是文件，直接处理，不受 TEXT_EXT 限制
            replace_package_res(path, OLD_PACKAGE, NEW_PACKAGE)
        elif path.is_dir():
            # 如果是目录，遍历指定扩展名的文件
            for ext in TEXT_EXT:
                for path_item in path.rglob(f"*{ext}"):
                    replace_package_res(path_item, OLD_PACKAGE, NEW_PACKAGE)
        else:
            print(f"Warning: Path does not exist: {path}")

    # 验证文件迁移完整性
    # 只统计文件（排除目录），以便正确比较迁移后的文件数量
    old_files_list = []
    new_files_list = []
    for old_path, new_path in PACKAGE_PATH_PAIR_LIST:
        old_files_list.extend(p for p in old_path.rglob("*") if p.is_file())
        new_files_list.extend(p for p in new_path.rglob("*") if p.is_file())
    if len(old_files_list) != len(new_files_list):
        print(
            f"Warning: {len(old_files_list)} files in old package, but {len(new_files_list)} files in new package."
        )
        print("Old files:")
        for f in old_files_list:
            print(f" - {f}")
        print("New files:")
        for f in new_files_list:
            print(f" - {f}")
    else:
        print(f"{len(old_files_list)} files migrated successfully.")

    # 删除旧包
    for old_path, _ in PACKAGE_PATH_PAIR_LIST:
        shutil.rmtree(old_path, ignore_errors=True)
        remove_empty_parents(old_path, PACKAGE_PATH)
        print(f"Deleted old package directory: {old_path}")

    # 检查是否还有旧包名残留
    for path in (PACKAGE_PATH).rglob("*"):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if OLD_PACKAGE in content or OLD_PACKAGE_SLASH in content:
            print(f"Found old package reference in: {path}")

    # 添加/更新 ProGuard 规则
    build_gradle = BUILD_GRADLE_FILE
    content = build_gradle.read_text(encoding="utf-8", errors="ignore")
    if ENABLE_PROGUARD:
        if REPLACE_PROGUARD:
            proguard_file = PROGUARD_FILE
            proguard_file.write_text(PROGUARD_CONTENT, encoding="utf-8")

        # 启用代码混淆（仅针对 release block，避免全局替换影响 debug）
        # Kotlin DSL (build.gradle.kts) 期望形如：isMinifyEnabled = false/true
        # 同时兼容 Groovy DSL 旧写法：minifyEnabled false/true 或 minifyEnabled = false/true
        content = re.sub(
            r"(release\s*\{[^}]*?)(isMinifyEnabled\s*=\s*|minifyEnabled\s*(?:=\s*)?)false",
            r"\1\2true",
            content,
            flags=re.S,
        )
        # 防止其它替换意外把 debug 的 minifyEnabled 设为 true，强制 debug 为 false
        content = re.sub(
            r"(debug\s*\{[^}]*?)(isMinifyEnabled\s*=\s*|minifyEnabled\s*(?:=\s*)?)true",
            r"\1\2false",
            content,
            flags=re.S,
        )
        # 确保 release 中 shrinkResources 为 true（同样仅在 release block）
        content = re.sub(
            r"(release\s*\{[^}]*?)(isShrinkResources\s*=\s*|shrinkResources\s*(?:=\s*)?)false",
            r"\1\2true",
            content,
            flags=re.S,
        )
        build_gradle.write_text(content, encoding="utf-8")
    else:
        # 将 (is)MinifyEnabled true -> false（仅 release block）
        content = re.sub(
            r"(release\s*\{[^}]*?)(isMinifyEnabled\s*=\s*|minifyEnabled\s*(?:=\s*)?)true",
            r"\1\2false",
            content,
            flags=re.S,
        )
        build_gradle.write_text(content, encoding="utf-8")
        # 将 (is)ShrinkResources true -> false（仅 release block）
        content = re.sub(
            r"(release\s*\{[^}]*?)(isShrinkResources\s*=\s*|shrinkResources\s*(?:=\s*)?)true",
            r"\1\2false",
            content,
            flags=re.S,
        )
        build_gradle.write_text(content, encoding="utf-8")

    # 禁用 Legacy Packaging（将 useLegacyPackaging 设为 false）
    # 兼容 Kotlin DSL: useLegacyPackaging = true 和 Groovy DSL: useLegacyPackaging true
    content = re.sub(
        r"(useLegacyPackaging\s*(?:=\s*)?)true",
        r"\1false",
        content,
    )
    build_gradle.write_text(content, encoding="utf-8")

    # 定义性能优化的 gradle 配置
    # performance_gradle_file = PERFORMANCE_GRADLE_FILE
    # performance_gradle_file.write_text(PERFORMANCE_GRADLE_CONTENT, encoding="utf-8")

    rewrite_version(VERSION_FILE)

    print("Refactoring completed successfully.")


if __name__ == "__main__":
    main()
