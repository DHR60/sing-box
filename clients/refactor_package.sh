#!/bin/bash

# 定义旧包名和新包名
OLD_PACKAGE="io.nekohasekai.sfa"
NEW_PACKAGE="com.clearpath.sfa"

# 定义旧包和新包的路径
OLD_PACKAGE_PATH="android/app/src/main/java/io/nekohasekai/sfa"
NEW_PACKAGE_PATH="android/app/src/main/java/com/clearpath/sfa"
# 定义AIDL路径
OLD_AIDL_PATH="android/app/src/main/aidl/io/nekohasekai/sfa"
NEW_AIDL_PATH="android/app/src/main/aidl/com/clearpath/sfa"
# 定义其他构建变体路径
OLD_OTHER_PATH="android/app/src/other/java/io/nekohasekai/sfa"
NEW_OTHER_PATH="android/app/src/other/java/com/clearpath/sfa"
OLD_PLAY_PATH="android/app/src/play/java/io/nekohasekai/sfa"
NEW_PLAY_PATH="android/app/src/play/java/com/clearpath/sfa"

# 添加删除空父目录的函数
remove_empty_parent_dirs() {
  local dir="$1"
  local base_dir="$2"  # 基础目录，不应该被删除
  
  # 获取父目录
  local parent_dir=$(dirname "$dir")
  
  # 如果已经到达基础目录或根目录，停止递归
  if [ "$parent_dir" = "$base_dir" ] || [ "$parent_dir" = "/" ] || [ "$parent_dir" = "." ]; then
    return
  fi
  
  # 如果父目录为空，删除它并继续递归
  if [ -d "$parent_dir" ] && [ -z "$(ls -A "$parent_dir" 2>/dev/null)" ]; then
    echo "删除空目录: $parent_dir"
    rmdir "$parent_dir"
    # 递归检查更上层的父目录
    remove_empty_parent_dirs "$parent_dir" "$base_dir"
  fi
}

echo "=============================="
echo "重构包名调试信息"
echo "当前工作目录: $(pwd)"
echo "旧包名: $OLD_PACKAGE"
echo "新包名: $NEW_PACKAGE"
echo "旧包路径: $OLD_PACKAGE_PATH"
echo "新包路径: $NEW_PACKAGE_PATH"
echo "旧AIDL路径: $OLD_AIDL_PATH"
echo "新AIDL路径: $NEW_AIDL_PATH"
echo "旧Other路径: $OLD_OTHER_PATH"
echo "新Other路径: $NEW_OTHER_PATH"
echo "旧Play路径: $OLD_PLAY_PATH"
echo "新Play路径: $NEW_PLAY_PATH"
echo "=============================="

echo "Refactoring package from $OLD_PACKAGE to $NEW_PACKAGE..."

# 检查是否已替换，防止重复执行
if grep -q "applicationId = \"$NEW_PACKAGE\"" android/app/build.gradle; then
  echo "Package name already updated to $NEW_PACKAGE"
  exit 0
fi

# 完全重构方法 - 使用sed直接全局替换所有文件内容
echo "执行完全重构..."

# 1. 先全局替换build.gradle文件
echo "步骤1: 更新Gradle配置..."
sed -i "s/$OLD_PACKAGE/$NEW_PACKAGE/g" android/app/build.gradle
sed -i "s/$OLD_PACKAGE/$NEW_PACKAGE/g" android/build.gradle

# 2. 创建新的包目录结构
echo "步骤2: 创建目标包目录..."
mkdir -p "$NEW_PACKAGE_PATH"

# 3. 复制所有文件到新位置，同时替换文件内容
echo "步骤3: 复制并替换文件内容..."
for file in $(find "$OLD_PACKAGE_PATH" -type f); do
  # 计算目标文件路径
  target_file="${file/$OLD_PACKAGE_PATH/$NEW_PACKAGE_PATH}"
  target_dir=$(dirname "$target_file")
  
  # 确保目标目录存在
  mkdir -p "$target_dir"
  
  # 复制文件到新位置，同时替换内容
  sed "s/$OLD_PACKAGE/$NEW_PACKAGE/g" "$file" > "$target_file"
  
  echo "处理: $file -> $target_file"
done

# 4. 处理其他资源文件（layout, manifest等）
echo "步骤4: 更新资源文件..."
find android/app/src/main -type f \( -name "*.xml" -o -name "*.properties" \) -exec sed -i "s/$OLD_PACKAGE/$NEW_PACKAGE/g" {} \;

# 5. 处理AIDL文件
echo "步骤5: 处理AIDL文件..."
if [ -d "$OLD_AIDL_PATH" ]; then
  # 创建新的AIDL目录结构
  mkdir -p "$NEW_AIDL_PATH"
  
  # 复制所有AIDL文件到新位置，同时替换文件内容
  for file in $(find "$OLD_AIDL_PATH" -type f -name "*.aidl"); do
    # 计算目标文件路径
    target_file="${file/$OLD_AIDL_PATH/$NEW_AIDL_PATH}"
    target_dir=$(dirname "$target_file")
    
    # 确保目标目录存在
    mkdir -p "$target_dir"
    
    # 复制文件到新位置，同时替换内容
    sed "s/$OLD_PACKAGE/$NEW_PACKAGE/g" "$file" > "$target_file"
    
    echo "处理AIDL: $file -> $target_file"
  done
  
  # 删除旧的AIDL目录
  rm -rf "$OLD_AIDL_PATH"
  # 删除空的父目录
  remove_empty_parent_dirs "$OLD_AIDL_PATH" "android/app/src/main/aidl"
  echo "旧AIDL目录已删除"
else
  echo "旧AIDL目录不存在，跳过AIDL处理"
fi

# 6. 处理other变体目录
echo "步骤6: 处理other变体目录文件..."
if [ -d "$OLD_OTHER_PATH" ]; then
  # 创建新的other目录结构
  mkdir -p "$NEW_OTHER_PATH"
  
  # 复制所有文件到新位置，同时替换文件内容
  for file in $(find "$OLD_OTHER_PATH" -type f); do
    # 计算目标文件路径
    target_file="${file/$OLD_OTHER_PATH/$NEW_OTHER_PATH}"
    target_dir=$(dirname "$target_file")
    
    # 确保目标目录存在
    mkdir -p "$target_dir"
    
    # 复制文件到新位置，同时替换内容
    sed "s/$OLD_PACKAGE/$NEW_PACKAGE/g" "$file" > "$target_file"
    
    echo "处理other文件: $file -> $target_file"
  done
  
  # 删除旧的other目录
  rm -rf "$OLD_OTHER_PATH"
  # 删除空的父目录
  remove_empty_parent_dirs "$OLD_OTHER_PATH" "android/app/src/other/java"
  echo "旧other目录已删除"
else
  echo "旧other目录不存在，跳过other处理"
fi

# 7. 处理play变体目录
echo "步骤7: 处理play变体目录文件..."
if [ -d "$OLD_PLAY_PATH" ]; then
  # 创建新的play目录结构
  mkdir -p "$NEW_PLAY_PATH"
  
  # 复制所有文件到新位置，同时替换文件内容
  for file in $(find "$OLD_PLAY_PATH" -type f); do
    # 计算目标文件路径
    target_file="${file/$OLD_PLAY_PATH/$NEW_PLAY_PATH}"
    target_dir=$(dirname "$target_file")
    
    # 确保目标目录存在
    mkdir -p "$target_dir"
    
    # 复制文件到新位置，同时替换内容
    sed "s/$OLD_PACKAGE/$NEW_PACKAGE/g" "$file" > "$target_file"
    
    echo "处理play文件: $file -> $target_file"
  done
  
  # 删除旧的play目录
  rm -rf "$OLD_PLAY_PATH"
  # 删除空的父目录
  remove_empty_parent_dirs "$OLD_PLAY_PATH" "android/app/src/play/java"
  echo "旧play目录已删除"
else
  echo "旧play目录不存在，跳过play处理"
fi

# 8. 更新AndroidManifest.xml中的活动和服务引用
echo "步骤8: 更新AndroidManifest.xml活动和服务引用..."
sed -i "s/android:name=\"\.$OLD_PACKAGE/android:name=\"\.$NEW_PACKAGE/g" android/app/src/main/AndroidManifest.xml
sed -i "s/android:name=\"$OLD_PACKAGE/android:name=\"$NEW_PACKAGE/g" android/app/src/main/AndroidManifest.xml

# 步骤9: 处理Room数据库schema文件
echo "步骤9: 处理Room数据库schema文件..."
# 定义schema相关路径
OLD_SCHEMAS_BASE="android/app/schemas/$OLD_PACKAGE"
NEW_SCHEMAS_BASE="android/app/schemas/$NEW_PACKAGE"

# 处理KeyValueDatabase schema
OLD_KV_SCHEMA="$OLD_SCHEMAS_BASE.database.preference.KeyValueDatabase/1.json"
NEW_KV_SCHEMA="$NEW_SCHEMAS_BASE.database.preference.KeyValueDatabase/1.json"
if [ -f "$OLD_KV_SCHEMA" ]; then
  # 确保目标目录存在
  mkdir -p "$(dirname "$NEW_KV_SCHEMA")"
  # 复制文件并替换包名引用
  sed "s/$OLD_PACKAGE/$NEW_PACKAGE/g" "$OLD_KV_SCHEMA" > "$NEW_KV_SCHEMA"
  echo "处理Schema: $OLD_KV_SCHEMA -> $NEW_KV_SCHEMA"
  # 删除旧文件
  rm -f "$OLD_KV_SCHEMA"
else
  echo "警告: KeyValueDatabase schema文件不存在: $OLD_KV_SCHEMA"
fi

# 处理ProfileDatabase schema
OLD_PROFILE_SCHEMA="$OLD_SCHEMAS_BASE.database.ProfileDatabase/1.json"
NEW_PROFILE_SCHEMA="$NEW_SCHEMAS_BASE.database.ProfileDatabase/1.json"
if [ -f "$OLD_PROFILE_SCHEMA" ]; then
  # 确保目标目录存在
  mkdir -p "$(dirname "$NEW_PROFILE_SCHEMA")"
  # 复制文件并替换包名引用
  sed "s/$OLD_PACKAGE/$NEW_PACKAGE/g" "$OLD_PROFILE_SCHEMA" > "$NEW_PROFILE_SCHEMA"
  echo "处理Schema: $OLD_PROFILE_SCHEMA -> $NEW_PROFILE_SCHEMA"
  # 删除旧文件
  rm -f "$OLD_PROFILE_SCHEMA"
else
  echo "警告: ProfileDatabase schema文件不存在: $OLD_PROFILE_SCHEMA"
fi

# 删除可能为空的旧目录
if [ -d "$(dirname "$OLD_SCHEMAS_BASE")" ]; then
  rm -rf "$(dirname "$OLD_SCHEMAS_BASE")"
  # 删除schemas目录下的空父目录
  remove_empty_parent_dirs "$(dirname "$OLD_SCHEMAS_BASE")" "android/app/schemas"
fi

# 在删除旧包之前添加验证步骤
echo "步骤10: 验证文件迁移完整性..."
OLD_FILES_COUNT=$(find "$OLD_PACKAGE_PATH" -type f | wc -l)
NEW_FILES_COUNT=$(find "$NEW_PACKAGE_PATH" -type f | wc -l)
echo "旧包文件数: $OLD_FILES_COUNT"
echo "新包文件数: $NEW_FILES_COUNT"

# 删除旧包
echo "删除旧包..."
rm -rf "$OLD_PACKAGE_PATH"
# 删除空的父目录
remove_empty_parent_dirs "$OLD_PACKAGE_PATH" "android/app/src/main/java"

# 步骤10.5: 全面检查android目录下是否还有旧包名残留
echo "步骤10.5: 检查android目录下旧包名残留..."
MISSING_FILES=0

# 检查是否还有包含旧包名的文件夹路径
OLD_PACKAGE_DIRS=$(find android -type d \( -path "*io/nekohasekai/sfa*" -o -path "*io.nekohasekai.sfa*" \) 2>/dev/null | wc -l)
if [ $OLD_PACKAGE_DIRS -gt 0 ]; then
  echo "发现 $OLD_PACKAGE_DIRS 个包含旧包路径的目录:"
  find android -type d \( -path "*io/nekohasekai/sfa*" -o -path "*io.nekohasekai.sfa*" \) 2>/dev/null
  MISSING_FILES=$((MISSING_FILES + OLD_PACKAGE_DIRS))
fi

# 检查是否还有包含旧包名的文件路径
OLD_PACKAGE_FILES=$(find android -type f \( -path "*io/nekohasekai/sfa*" -o -path "*io.nekohasekai.sfa*" \) 2>/dev/null | wc -l)
if [ $OLD_PACKAGE_FILES -gt 0 ]; then
  echo "发现 $OLD_PACKAGE_FILES 个包含旧包路径的文件:"
  find android -type f \( -path "*io/nekohasekai/sfa*" -o -path "*io.nekohasekai.sfa*" \) 2>/dev/null
  MISSING_FILES=$((MISSING_FILES + OLD_PACKAGE_FILES))
fi

# 检查schemas目录下是否还有旧包名相关文件或目录（使用两种包名格式）
if [ -d "android/app/schemas" ]; then
  OLD_SCHEMA_ITEMS=$(find android/app/schemas \( -name "*io.nekohasekai.sfa*" -o -name "*io/nekohasekai/sfa*" -o -path "*io.nekohasekai.sfa*" \) 2>/dev/null | wc -l)
  if [ $OLD_SCHEMA_ITEMS -gt 0 ]; then
    echo "发现 $OLD_SCHEMA_ITEMS 个schemas目录下的旧包名相关项:"
    find android/app/schemas \( -name "*io.nekohasekai.sfa*" -o -name "*io/nekohasekai/sfa*" -o -path "*io.nekohasekai.sfa*" \) 2>/dev/null
    MISSING_FILES=$((MISSING_FILES + OLD_SCHEMA_ITEMS))
  fi
else
  echo "schemas目录不存在，跳过schemas检查"
fi

# 检查文件内容中是否还包含旧包名引用（包括点号格式）
OLD_PACKAGE_CONTENT=$(grep -r -E "(io\.nekohasekai\.sfa|io/nekohasekai/sfa)" android --include="*.xml" --include="*.gradle" --include="*.properties" --include="*.json" --include="*.kt" --include="*.java" 2>/dev/null | wc -l)
if [ $OLD_PACKAGE_CONTENT -gt 0 ]; then
  echo "发现 $OLD_PACKAGE_CONTENT 处文件内容包含旧包名引用:"
  grep -r -E "(io\.nekohasekai\.sfa|io/nekohasekai/sfa)" android --include="*.xml" --include="*.gradle" --include="*.properties" --include="*.json" --include="*.kt" --include="*.java" 2>/dev/null | head -10
  if [ $OLD_PACKAGE_CONTENT -gt 10 ]; then
    echo "... 还有 $((OLD_PACKAGE_CONTENT - 10)) 处引用未显示"
  fi
  MISSING_FILES=$((MISSING_FILES + OLD_PACKAGE_CONTENT))
fi

# 额外检查：搜索所有可能的旧包名变体
echo "进行额外的旧包名变体检查..."
OLD_PACKAGE_VARIANTS=$(find android \( -name "*nekohasekai*" -o -name "*sfa*" \) -type f -o -type d 2>/dev/null | grep -E "(nekohasekai|io\.nekohasekai)" | wc -l)
if [ $OLD_PACKAGE_VARIANTS -gt 0 ]; then
  echo "发现 $OLD_PACKAGE_VARIANTS 个可能的旧包名变体:"
  find android \( -name "*nekohasekai*" -o -name "*sfa*" \) -type f -o -type d 2>/dev/null | grep -E "(nekohasekai|io\.nekohasekai)" | head -5
  if [ $OLD_PACKAGE_VARIANTS -gt 5 ]; then
    echo "... 还有 $((OLD_PACKAGE_VARIANTS - 5)) 项未显示"
  fi
  MISSING_FILES=$((MISSING_FILES + OLD_PACKAGE_VARIANTS))
fi

# 根据检查结果决定是否继续
if [ $MISSING_FILES -gt 0 ]; then
  echo "警告: 发现 $MISSING_FILES 处旧包名残留！"
  
  # 在自动化环境中使用环境变量控制行为
  if [ "${FORCE_CONTINUE:-false}" = "true" ]; then
    echo "FORCE_CONTINUE=true，即使有残留也继续执行"
  else
    echo "发现旧包名残留，请手动检查清理情况"
    exit 1
  fi
else
  echo "✓ 未发现旧包名残留，清理完成"
fi

# 11. 更新版本名称，添加-dhr60后缀
echo "步骤11: 更新版本名称..."
if [ -f "android/version.properties" ]; then
  # 检查是否已经添加了-dhr60后缀，避免重复添加
  if ! grep -q "VERSION_NAME=.*-dhr60" android/version.properties; then
    sed -i 's/VERSION_NAME=\(.*\)/VERSION_NAME=\1-dhr60/' android/version.properties
    echo "已添加-dhr60后缀到VERSION_NAME"
  else
    echo "VERSION_NAME已包含-dhr60后缀，跳过"
  fi
else
  echo "警告: android/version.properties 文件不存在"
fi

# 附加步骤: 修复通配符或子包引用...
echo "附加步骤: 修复通配符或子包引用..."
find $NEW_PACKAGE_PATH -type f -name "*.kt" -exec sed -i "s/import $OLD_PACKAGE\.\*/import $NEW_PACKAGE\.\*/g" {} \;
find $NEW_PACKAGE_PATH -type f -name "*.java" -exec sed -i "s/import $OLD_PACKAGE\.\*/import $NEW_PACKAGE\.\*/g" {} \;
find $NEW_PACKAGE_PATH -type f -name "*.xml" -exec sed -i "s/$OLD_PACKAGE\.\*/$NEW_PACKAGE\.\*/g" {} \;

# 新增步骤: 修复别名导入语句
echo "修复别名导入语句..."
find $NEW_PACKAGE_PATH -type f -name "*.kt" -exec sed -i "s/import $OLD_PACKAGE\([^*]\{1,\}\) as \([A-Za-z0-9_]\{1,\}\)/import $NEW_PACKAGE\1 as \2/g" {} \;
find $NEW_OTHER_PATH -type f -name "*.kt" -exec sed -i "s/import $OLD_PACKAGE\([^*]\{1,\}\) as \([A-Za-z0-9_]\{1,\}\)/import $NEW_PACKAGE\1 as \2/g" {} \;
find $NEW_PLAY_PATH -type f -name "*.kt" -exec sed -i "s/import $OLD_PACKAGE\([^*]\{1,\}\) as \([A-Za-z0-9_]\{1,\}\)/import $NEW_PACKAGE\1 as \2/g" {} \;

# 修复普通导入语句 (非通配符)
echo "修复普通导入语句..."
find $NEW_PACKAGE_PATH -type f -name "*.kt" -exec sed -i "s/import $OLD_PACKAGE\./import $NEW_PACKAGE./g" {} \;
find $NEW_OTHER_PATH -type f -name "*.kt" -exec sed -i "s/import $OLD_PACKAGE\./import $NEW_PACKAGE./g" {} \;
find $NEW_PLAY_PATH -type f -name "*.kt" -exec sed -i "s/import $OLD_PACKAGE\./import $NEW_PACKAGE./g" {} \;

# 处理 Java 文件中的导入
find $NEW_PACKAGE_PATH -type f -name "*.java" -exec sed -i "s/import $OLD_PACKAGE\./import $NEW_PACKAGE./g" {} \;
find $NEW_OTHER_PATH -type f -name "*.java" -exec sed -i "s/import $OLD_PACKAGE\./import $NEW_PACKAGE./g" {} \;
find $NEW_PLAY_PATH -type f -name "*.java" -exec sed -i "s/import $OLD_PACKAGE\./import $NEW_PACKAGE./g" {} \;

# 检查是否有遗漏的导入语句
echo "检查是否有遗漏的旧包名引用..."
MISSED_IMPORTS=$(grep -r "$OLD_PACKAGE" --include="*.kt" --include="*.java" $NEW_PACKAGE_PATH $NEW_OTHER_PATH $NEW_PLAY_PATH | wc -l)
if [ $MISSED_IMPORTS -gt 0 ]; then
  echo "警告: 发现 $MISSED_IMPORTS 处可能未替换的旧包名引用"
  grep -r "$OLD_PACKAGE" --include="*.kt" --include="*.java" $NEW_PACKAGE_PATH $NEW_OTHER_PATH $NEW_PLAY_PATH
fi

echo "=============================="
echo "重构完成，最终检查:"
echo "新包路径存在: $([ -d "$NEW_PACKAGE_PATH" ] && echo "是" || echo "否")"
echo "检测到的缺失文件数: $MISSING_FILES"
echo "=============================="

echo "Refactoring complete."

# 新增步骤: 添加/更新 ProGuard 规则以支持 Go Mobile
echo "=============================="
echo "步骤12: 配置 ProGuard 规则以支持 Go Mobile..."

PROGUARD_FILE="android/app/proguard-rules.pro"

# 定义 Go Mobile 相关的 ProGuard 规则
GO_MOBILE_RULES="
# Go Mobile ProGuard 规则 - 解决 Release 构建问题
# 保留泛型签名信息 - 解决 ClassCastException 与 ParameterizedType 相关问题
-keepattributes Signature

# 保留 Go Mobile 生成的 Java 桩代码
-keep class go.** { *; }

# 保留 libbox 相关的类（基于新包名）
-keep class $NEW_PACKAGE.** { *; }

# 保留所有 native 方法（Go Mobile 使用 JNI）
-keepclasseswithmembernames class * {
    native <methods>;
}

# 保留反射访问的类和方法
-keepattributes RuntimeVisibleAnnotations
-keepattributes RuntimeInvisibleAnnotations
-keepattributes InnerClasses
-keepattributes EnclosingMethod

# 保留 libbox 相关的类和接口（原始包名）
-keep interface io.nekohasekai.libbox.** { *; }
-keep class io.nekohasekai.libbox.** { *; }

# 保留可能通过反射访问的服务类
-keep class * extends android.app.Service { *; }
-keep class * implements android.os.Parcelable { *; }
"

# 检查 ProGuard 文件是否存在
if [ -f "$PROGUARD_FILE" ]; then
  # 检查是否已经包含 Go Mobile 规则
  if grep -q "Go Mobile ProGuard 规则" "$PROGUARD_FILE"; then
    echo "ProGuard 文件已包含 Go Mobile 规则，跳过添加"
  else
    echo "在现有 ProGuard 文件中添加 Go Mobile 规则..."
    echo "$GO_MOBILE_RULES" >> "$PROGUARD_FILE"
    echo "✓ Go Mobile ProGuard 规则已添加"
  fi
else
  echo "创建新的 ProGuard 文件并添加 Go Mobile 规则..."
  echo "$GO_MOBILE_RULES" > "$PROGUARD_FILE"
  echo "✓ 已创建 ProGuard 文件并添加 Go Mobile 规则"
fi

# 确保 build.gradle 中启用了 ProGuard
echo "检查 build.gradle 中的 ProGuard 配置..."
if grep -q "proguardFiles" android/app/build.gradle; then
  echo "✓ build.gradle 已配置 ProGuard"
else
  echo "警告: build.gradle 中未发现 proguardFiles 配置，请手动检查 Release 构建配置"
fi

echo "=============================="
echo "Go Mobile ProGuard 配置完成"
echo "ProGuard 文件位置: $PROGUARD_FILE"
echo "=============================="

# 清理项目
echo "清理并构建项目..."
cd android
./gradlew clean
cd ..
