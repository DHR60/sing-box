#!/usr/bin/env python3
import re
import shutil
from pathlib import Path
import sys

OLD_PACKAGE = "io.nekohasekai.sfa"
NEW_PACKAGE = "com.clearpath.sfa"

OLD_PACKAGE_SLASH = OLD_PACKAGE.replace(".", "/")
NEW_PACKAGE_SLASH = NEW_PACKAGE.replace(".", "/")

PACKAGE_PATH = Path("android/app/src")

OLD_PACKAGE_PATH = PACKAGE_PATH / Path("main/java") / Path(OLD_PACKAGE_SLASH)
NEW_PACKAGE_PATH = PACKAGE_PATH / Path("main/java") / Path(NEW_PACKAGE_SLASH)
OLD_AIDL_PATH = PACKAGE_PATH / Path("main/aidl") / Path(OLD_PACKAGE_SLASH)
NEW_AIDL_PATH = PACKAGE_PATH / Path("main/aidl") / Path(NEW_PACKAGE_SLASH)
# 定义其他构建变体路径
OLD_OTHER_PATH = PACKAGE_PATH / Path("other/java") / Path(OLD_PACKAGE_SLASH)
NEW_OTHER_PATH = PACKAGE_PATH / Path("other/java") / Path(NEW_PACKAGE_SLASH)
OLD_PLAY_PATH = PACKAGE_PATH / Path("play/java") / Path(OLD_PACKAGE_SLASH)
NEW_PLAY_PATH = PACKAGE_PATH / Path("play/java") / Path(NEW_PACKAGE_SLASH)
# Room数据库schema文件
OLD_SCHEMAS_BASE_PATH1 = Path("android/app/schemas") / Path(
    f"{OLD_PACKAGE}.database.preference.KeyValueDatabase"
)
NEW_SCHEMAS_BASE_PATH1 = Path("android/app/schemas") / Path(
    f"{NEW_PACKAGE}.database.preference.KeyValueDatabase"
)
OLD_SCHEMAS_BASE_PATH2 = Path("android/app/schemas") / Path(
    f"{OLD_PACKAGE}.database.ProfileDatabase"
)
NEW_SCHEMAS_BASE_PATH2 = Path("android/app/schemas") / Path(
    f"{NEW_PACKAGE}.database.ProfileDatabase"
)

# replace and move
# must be folders, not files
PACKAGE_PATH_PAIR_LIST = [
    (OLD_PACKAGE_PATH, NEW_PACKAGE_PATH),
    (OLD_AIDL_PATH, NEW_AIDL_PATH),
    (OLD_OTHER_PATH, NEW_OTHER_PATH),
    (OLD_PLAY_PATH, NEW_PLAY_PATH),
    (OLD_SCHEMAS_BASE_PATH1, NEW_SCHEMAS_BASE_PATH1),
    (OLD_SCHEMAS_BASE_PATH2, NEW_SCHEMAS_BASE_PATH2),
]

# replace but keep original location
# may be folders or files
PACKAGE_PATH_LIST_KEEP = [
    PACKAGE_PATH,
    Path("android/app/build.gradle"),
    Path("android/build.gradle"),
]

BUILD_GRADLE_FILE = Path("android/app/build.gradle")

PROGUARD_FILE = Path("android/app/proguard-rules.pro")

PERFORMANCE_GRADLE_FILE = Path("android/gradle.properties")

VERSION_FILE = Path("android/version.properties")

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
    ".aidl",
}

EXECUTE_EXT = {
    "*.aar",
    "*.so",
    "*.dll",
    "*.dylib",
    "*.exe",
    "*.bin",
    "*.apk",
    "*.ipa",
    "*.app",
    "*.xctest",
    "*.jar",
}

ENABLE_PROGUARD = True

PROGUARD_CONTENT = """
-dontobfuscate

# ===== 保留所有应用类（解决 JNI 问题的最简单方法）=====
-keep class $NEW_PACKAGE.** { *; }

# ===== JNI 相关保护 =====
-keepclasseswithmembernames class * {
    native <methods>;
}

# ===== 保留静态成员 =====
-keepclassmembers class * {
    static <fields>;
    static <methods>;
}

# ===== Android 组件保护 =====
-keep class * extends android.app.Service { *; }
-keep class * extends android.content.BroadcastReceiver { *; }

# ===== 基本属性保留 =====
-keepattributes Signature
-keepattributes InnerClasses
-keepattributes EnclosingMethod

# ERROR: Missing classes detected while running R8.
-dontwarn com.squareup.okhttp.CipherSuite
-dontwarn com.squareup.okhttp.ConnectionSpec
-dontwarn com.squareup.okhttp.TlsVersion
-dontwarn org.bouncycastle.jsse.BCSSLSocket
-dontwarn org.bouncycastle.jsse.provider.BouncyCastleJsseProvider
-dontwarn org.conscrypt.Conscrypt$Version
-dontwarn org.conscrypt.Conscrypt
-dontwarn org.conscrypt.ConscryptHostnameVerifier
-dontwarn org.joda.convert.FromString
-dontwarn org.joda.convert.ToString
-dontwarn org.openjsse.javax.net.ssl.SSLParameters
-dontwarn org.openjsse.javax.net.ssl.SSLSocket
-dontwarn org.openjsse.net.ssl.OpenJSSE

""".replace(
    "$NEW_PACKAGE", NEW_PACKAGE
)

PERFORMANCE_GRADLE_CONTENT = """
# ===== JVM 优化配置 =====
# 增加 JVM 堆内存到 4GB（提升大项目构建性能）
org.gradle.jvmargs=-Xmx4g -XX:+UseParallelGC -Dfile.encoding=UTF-8

# ===== Gradle 构建优化 =====
# 启用并行构建（多模块项目性能提升）
org.gradle.parallel=true

# 启用构建缓存（重复构建时显著提速）
org.gradle.caching=true

# 启用配置缓存（Gradle 6.6+，实验性功能）
org.gradle.configureondemand=true

# ===== Android 构建优化 =====
# 启用 R8 全模式（更激进的优化）
android.enableR8.fullMode=true

# 启用增量编译
kotlin.incremental=true

# 启用 Kotlin 编译缓存
kotlin.incremental.useClasspathSnapshot=true

# ===== 项目特定配置（保留原有设置）=====
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
android.defaults.buildfeatures.buildconfig=true
android.nonFinalResIds=false

# ===== 内存和性能调优 =====
# 禁用守护进程监视（减少内存占用）
org.gradle.daemon.idletimeout=3600000

# 文件监视器优化
org.gradle.vfs.watch=true

"""


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
        copy_and_replace_tree(old_path, new_path, OLD_PACKAGE, NEW_PACKAGE)

    # 处理其他资源文件（包含子目录），但排除代码包目录
    for ext in TEXT_EXT:
        for path in PACKAGE_PATH_LIST_KEEP:
            for path_item in path.rglob(f"*{ext}"):
                replace_package_res(path_item, OLD_PACKAGE, NEW_PACKAGE)

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
        proguard_file = PROGUARD_FILE
        proguard_file.write_text(PROGUARD_CONTENT, encoding="utf-8")

        # 启用代码混淆（仅针对 release block，避免全局替换影响 debug）
        # 将 release block 中的 minifyEnabled false -> true
        content = re.sub(
            r"(release\s*\{[^}]*?)minifyEnabled\s+false",
            r"\1minifyEnabled true",
            content,
            flags=re.S,
        )
        # 防止其它替换意外把 debug 的 minifyEnabled 设为 true，强制 debug 为 false
        content = re.sub(
            r"(debug\s*\{[^}]*?)minifyEnabled\s+true",
            r"\1minifyEnabled false",
            content,
            flags=re.S,
        )
        # 确保 release 中 shrinkResources 为 true（同样仅在 release block）
        content = re.sub(
            r"(release\s*\{[^}]*?)shrinkResources\s+false",
            r"\1shrinkResources true",
            content,
            flags=re.S,
        )
        build_gradle.write_text(content, encoding="utf-8")
    else:
        # 将 minifyEnabled true -> false
        content = re.sub(
            r"(release\s*\{[^}]*?)minifyEnabled\s+true",
            r"\1minifyEnabled false",
            content,
            flags=re.S,
        )
        build_gradle.write_text(content, encoding="utf-8")
        # 将 shrinkResources true -> false
        content = re.sub(
            r"(release\s*\{[^}]*?)shrinkResources\s+true",
            r"\1shrinkResources false",
            content,
            flags=re.S,
        )
        build_gradle.write_text(content, encoding="utf-8")

    # 定义性能优化的 gradle 配置
    performance_gradle_file = PERFORMANCE_GRADLE_FILE
    performance_gradle_file.write_text(PERFORMANCE_GRADLE_CONTENT, encoding="utf-8")

    rewrite_version(VERSION_FILE)

    print("Refactoring completed successfully.")


if __name__ == "__main__":
    main()
