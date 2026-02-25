# 🔨 Commodity Lab 打包和发布指南

## 📋 目录
1. [本地构建](#本地构建)
2. [自动化CI/CD](#自动化cicd)
3. [版本管理](#版本管理)
4. [Release发布](#release发布)
5. [故障排除](#故障排除)

---

## 🖥️ 本地构建

### Windows (PowerShell)

#### 快速开始
```powershell
# 设置执行策略允许脚本运行（如果需要）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 运行构建脚本
.\build.ps1

# 或清理后构建
.\build.ps1 -Clean

# 或不创建单文件exe（便于调试）
.\build.ps1 -OneFile:$false
```

#### 输出信息
```
✅ 构建成功！
📦 可执行文件:
   路径: dist\Commodity-Lab.exe
   大小: 150.23 MB
🚀 运行应用:
   & '.\dist\Commodity-Lab.exe'
```

### Linux/Mac (Bash)

#### 快速开始
```bash
# 赋予脚本执行权限
chmod +x build.sh

# 运行构建脚本
./build.sh

# 或清理后构建
./build.sh --clean
```

#### 手动构建（如果脚本不可用）

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Mac/Linux

# 2. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 3. 构建（选择一个方式）

# 方式1: 使用spec文件
pyinstaller commodity_lab.spec

# 方式2: 直接命令行
pyinstaller --onefile --windowed --name "Commodity-Lab" \
  --add-data "app:app" \
  --add-data "core:core" \
  --add-data "data:data" \
  --hidden-import=streamlit \
  --hidden-import=duckdb \
  --hidden-import=pandas \
  --hidden-import=plotly \
  --hidden-import=yfinance \
  --distpath dist \
  app/main.py
```

#### 输出目录
- **dist/** - 包含最终的可执行文件
- **build/** - 临时构建文件
- **.spec** - PyInstaller配置文件

---

## 🤖 自动化CI/CD

### GitHub Actions工作流

#### 配置位置
```
.github/workflows/build-and-release.yml
```

#### 工作流概览
```
推送标签 (v*.*.*)
    ↓
構建exe (Windows)
    ↓
验证构建
    ↓
创建Release + 自动release notes
```

#### 触发条件

1. **推送版本标签** (推荐方式)
```bash
# 创建本地标签
git tag -a v1.1.0 -m "Release version 1.1.0"

# 推送标签到GitHub
git push origin v1.1.0

# 工作流自动触发，生成exe + release
```

2. **手动触发**
```
GitHub仓库 → Actions → Build and Release → Run workflow
```

#### Release自动生成内容

工作流会自动生成：
- ✅ Windows 64-bit exe
- ✅ 压缩包 (Commodity-Lab-v1.1.0-win64.zip)
- ✅ Release Notes (自动从提交生成)
- ✅ Build artifact (30天保留)

#### Release Notes内容示例

```markdown
## Commodity Lab v1.1.0

### 📦 Version Information
- **Version**: v1.1.0
- **Release Date**: 2026-02-25
- **Platform**: Windows 64-bit

### 📥 Installation
1. Download: `Commodity-Lab-v1.1.0-win64.zip`
2. Extract the ZIP file
3. Run `Commodity-Lab.exe`

### 🆕 What's New
- 参考GitHub提交历史自动生成

### 🔧 System Requirements
- Windows 7 or later (64-bit)
- 500MB free disk space
- Internet connection (for data download)
```

---

## 📌 版本管理

### 版本号方案 (Semantic Versioning)

格式: `MAJOR.MINOR.PATCH-PRERELEASE+BUILD`

例子:
- `v1.0.0` - 第一个正式版本
- `v1.1.0` - 新增功能
- `v1.1.1` - Bug修复
- `v1.1.0-rc1` - 候选版本
- `v1.1.0-beta` - 测试版本

### 创建Release的步骤

#### 1️⃣ 更新版本号

在以下文件中更新版本（可选但推荐）：

```python
# app/main.py
__version__ = "1.1.0"
```

```toml
# pyproject.toml
version = "1.1.0"
```

#### 2️⃣ 更新CHANGELOG

编辑 `CHANGELOG.md` (如果有):

```markdown
## [1.1.0] - 2026-02-25

### Added
- 新增功能1
- 新增功能2

### Fixed
- 修复bug1
- 修复bug2

### Changed
- 改进功能1
```

#### 3️⃣ 提交更改

```bash
git add .
git commit -m "chore: prepare release v1.1.0

- Update version to 1.1.0
- Update CHANGELOG.md
- Final testing completed"
```

#### 4️⃣ 创建标签并推送

```bash
# 创建标签
git tag -a v1.1.0 -m "Release Commodity Lab v1.1.0

Features:
- 特性1
- 特性2

Fixes:
- 修复1
- 修复2"

# 推送标签触发CI/CD
git push origin v1.1.0
```

#### 5️⃣ 查看构建进度

访问: https://github.com/AlexYuhuFeng/Commodity-Lab/actions

等待工作流完成（通常5-10分钟）

#### 6️⃣ 验证Release

访问: https://github.com/AlexYuhuFeng/Commodity-Lab/releases/tag/v1.1.0

检查：
- ✅ exe文件已上传
- ✅ Release Notes已生成
- ✅ 下载链接可用

---

## 📢 Release发布

### 自动Release说明

GitHub Actions自动创建的Release包含：

| 文件 | 说明 |
|------|------|
| `Commodity-Lab-v1.1.0-win64.zip` | 完整可执行包 |
| `RELEASE_NOTES.md` | 发布说明 |
| Artifact | 30天可下载 |

### 手动编辑Release

如需补充信息，可在GitHub上手动编辑：

1. 访问 Release 页面
2. 点击"Edit"
3. 修改description和notes
4. 保存

### 发布通知

发布后可通过以下方式通知用户：

#### 邮件通知
- GitHub会自动发送给Watcher

#### 社交媒体
- 可在GitHub Release中添加链接

#### 项目主页
- 更新README.md的Latest Release部分

---

## 🆚 不同平台的支持

### 当前 (Windows)

✅ **GitHub Actions**使用`windows-latest`
- 生成: Win64 exe
- 自动化: 完整

### 未来扩展 (可选)

#### Mac构建
```yaml
build-macos:
  runs-on: macos-latest
  # 生成 .app 和 .dmg
```

#### Linux构建
```yaml
build-linux:
  runs-on: ubuntu-latest
  # 生成 AppImage 或 .deb
```

#### 多平台构建矩阵
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    include:
      - os: windows-latest
        artifact_name: Commodity-Lab.exe
      - os: macos-latest
        artifact_name: Commodity-Lab.app
      - os: ubuntu-latest
        artifact_name: Commodity-Lab.AppImage
```

---

## 🔧 构建配置文件

### commodity_lab.spec

PyInstaller的配置文件，定义：
- 入口点: `app/main.py`
- 打包方式: `--onefile` (单个exe)
- 数据文件: app, core, data目录
- 隐藏导入: streamlit, duckdb等

**修改建议**：
- 如需添加新的数据文件，在`datas`列表中添加
- 如需隐藏新的导入，在`hiddenimports`列表中添加

### requirements.txt

需要确保所有依赖都已列出：
```
streamlit>=1.28.0
pandas>=2.0.0
duckdb>=0.9.0
yfinance>=0.2.32
plotly>=5.17.0
```

验证方式：
```bash
pip install -r requirements.txt
pip freeze  # 查看已安装的所有包
```

---

## 🐛 故障排除

### 问题 1: PyInstaller找不到模块

**症状**:
```
ModuleNotFoundError: No module named 'streamlit'
```

**解决方案**:
```bash
# 检查虚拟环境是否激活
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\Activate.ps1  # Windows

# 重新安装依赖
pip install -r requirements.txt
```

### 问题 2: sqlite3导入错误

**症状**:
```
ImportError: DLL load failed while importing _sqlite3
```

**解决方案**:
```bash
# 添加到spec文件的hiddenimports
'sqlite3'

# 或使用PyInstaller选项
--hidden-import=sqlite3
```

### 问题 3: 生成的exe启动缓慢

**原因**: 首次启动需要解包和初始化

**解决方案**:
- 第一次启动可能需要10-30秒
- 后续启动会很快
- 可在spec中调整以改善启动时间

### 问题 4: 文件大小过大

**原因**: Streamlit和依赖包含丰富的资源

**解决方案**:
1. 使用`--onefile`（已配置）
2. 启用UPX压缩（spec中已配置）
3. 删除不必要的依赖

### 问题 5: GitHub Actions权限错误

**症状**:
```
Error: GITHUB_TOKEN permission error
```

**解决方案**:
1. 访问 Settings → Actions → General
2. 确保 "Workflow permissions" 设置为 "Read and write permissions"
3. 确保 "Allow GitHub Actions to create and approve pull requests" 被勾选

### 问题 6: Release创建失败

**症状**:
```
Error: failed to create release
```

**解决方案**:
1. 确认标签格式正确 (`v*.*.*)`)
2. 检查标签是否已存在: `git tag -l v1.1.0`
3. 删除本地标签重新创建: `git tag -d v1.1.0`

---

## 📚 相关资源

### 官方文档
- [PyInstaller文档](https://pyinstaller.org/)
- [GitHub Actions文档](https://docs.github.com/actions)
- [Semantic Versioning](https://semver.org/)

### 工具
- [PyInstaller](https://pyinstaller.org/) - Python应用打包
- [GitHub Actions](https://github.com/features/actions) - 自动化CI/CD
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release) - GitHub Release操作

---

## ✨ 最佳实践

1. **本地测试** ✓
   - 在发布前本地构建和测试exe
   - 确保所有功能正常

2. **版本一致性** ✓
   - 标签版本和代码版本保持一致
   - 更新CHANGELOG

3. **清晰的提交信息** ✓
   - 使用规范的提交消息
   - GitHub会自动生成更好的Release Notes

4. **定期发布** ✓
   - 周期性发布（如双周）
   - 累积足够的改进后发布

5. **监控构建** ✓
   - 关注Actions的构建进度
   - 及时处理失败

---

## 🎯 快速命令参考

### 本地构建
```powershell
# Windows
.\build.ps1 -Clean              # 清理并构建
.\build.ps1                     # 只构建

# Linux/Mac
./build.sh --clean              # 清理并构建
./build.sh                      # 只构建
```

### 创建Release
```bash
# 创建标签
git tag -a v1.1.0 -m "Release v1.1.0"

# 推送标签（触发CI/CD）
git push origin v1.1.0

# 查看现有标签
git tag -l

# 删除本地标签
git tag -d v1.1.0

# 删除远程标签
git push origin :v1.1.0
```

### 检查构建
```bash
# 查看Actions状态
# 访问: https://github.com/AlexYuhuFeng/Commodity-Lab/actions

# 查看具体workflow
# 访问: https://github.com/AlexYuhuFeng/Commodity-Lab/actions/workflows/build-and-release.yml
```

---

## 📞 支持

如遇到问题：
1. 查看 [故障排除](#故障排除) 部分
2. 检查 [GitHub Actions日志](https://github.com/AlexYuhuFeng/Commodity-Lab/actions)
3. 查看 [PyInstaller常见问题](https://pyinstaller.org/en/stable/common-issues-and-gotchas.html)

---

**最后更新**: 2026年2月25日  
**版本**: 1.0.0
