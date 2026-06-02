# 🚀 Commodity Lab 打包方案选择指南

> NOTE: The project migrated to a Tauri-based desktop architecture. Legacy PyInstaller/Streamlit packaging is no longer the primary build path. See `tauri/README.md` and `.github/workflows/tauri-build.yml` for the new packaging flow.


## 📊 方案对比

### 方案 A: GitHub Actions CI/CD (推荐 ✅)

**原理**: 每次推送标签，GitHub自动构建并发布

```
推送标签 v1.1.0 → GitHub Actions自动触发
                    ↓
                Windows构建环境运行PyInstaller
                    ↓
                生成exe + Release + Release Notes
                    ↓
                自动发布到GitHub Releases
```

#### ✅ 优势
- **完全自动化**: tag推送 → exe生成 → Release发布 (全自动)
- **无需本地配置**: 不依赖本地环境
- **版本管理清晰**: 每个Release对应一个标签
- **多人协作方便**: 任何人都可以发起Release
- **自动Release Notes**: GitHub自动从提交生成
- **可靠稳定**: 在GitHub服务器上运行，不依赖个人电脑
- **免费**: GitHub免费提供

#### ⚠️  劣势
- **首次设置需要**: 配置.github/workflows (已完成 ✓)
- **需要网络**: 必须能访问GitHub
- **构建时间**: 5-10分钟完成

#### 👥 适合场景
- 团队开发
- 频繁Release
- 需要长期Releases
- 追求完全自动化

---

### 方案 B: VS Code插件 (手动构建辅助)

**原理**: 使用VS Code插件简化本地构建过程

#### 可用插件推荐

| 插件名称 | 功能 | 价格 |
|--------|------|------|
| **Action Buttons** | 一键执行任务 | 免费 |
| **Task Runner** | 任务管理 | 免费 |
| **Commands** | 命令快捷键 | 免费 |
| **Python** (官方) | Python开发工具 | 免费 |
| **Pylance** | Python语言服务器 | 免费 |

#### 推荐工作流: Action Buttons插件

**1. 安装插件**
```
VS Code → Extensions → 搜索"Action Buttons"
→ 安装作者为"helix-editor"的版本
```

**2. 配置 `.vscode/action-buttons.json`**

创建文件: `.vscode/action-buttons.json`
```json
{
  "buttons": [
    {
      "name": "🔨 Build EXE",
      "color": "#2196F3",
      "command": "cd ${workspaceRoot} && .\\build.ps1",
      "singleInstance": true,
      "showInStatusBar": true,
      "tooltip": "构建Windows EXE应用"
    },
    {
      "name": "🧹 Clean Build",
      "color": "#FFC107",
      "command": "cd ${workspaceRoot} && .\\build.ps1 -Clean",
      "singleInstance": true,
      "showInStatusBar": true,
      "tooltip": "清理并重新构建"
    },
    {
      "name": "🚀 Run EXE",
      "color": "#4CAF50",
      "command": "cd ${workspaceRoot} && .\\dist\\Commodity-Lab.exe",
      "singleInstance": true,
      "showInStatusBar": true,
      "tooltip": "运行已构建的EXE"
    }
  ]
}
```

**3. 使用**
- VS Code底部状态栏会出现3个按钮
- 点击按钮一键执行对应命令

#### ✅ 优势
- **实时反馈**: 看到即时的构建输出
- **本地完全控制**: 在自己电脑上构建
- **快速迭代**: 开发→构建→测试的快速循环
- **离线工作**: 不需要网络连接
- **调试方便**: 直接在VS Code中运行和调试

#### ⚠️  劣势
- **需要本地环境**: 需要安装所有依赖
- **手动发布**: 需要手动上传到GitHub
- **平台限制**: 只能在安装有Python的电脑上构建
- **不自动化Release**: 需要手动管理版本和Release Notes
- **多人协作复杂**: 每个开发者都需要本地环境

#### 👥 适合场景
- 本地开发测试
- 快速迭代
- 单人开发
- 不需要自动Release

---

## 🎯 推荐方案

### 最佳实践 (组合方案) ⭐

**开发阶段** → 使用VS Code插件快速构建和测试  
**Release阶段** → 使用GitHub Actions自动打包和发布

```
开发流程:
├─ 在VS Code中修改代码
├─ 点击"🔨 Build EXE"按钮快速构建
├─ 点击"🚀 Run EXE"按钮测试exe功能
├─ 反复迭代直到完美
└─ 完成后提交代码

发布流程:
├─ 更新版本号 (app/main.py, pyproject.toml)
├─ 更新CHANGELOG.md
├─ git commit -m "Release v1.1.0"
├─ git tag -a v1.1.0 -m "Release v1.1.0"
├─ git push origin main
├─ git push origin v1.1.0  ← GitHub Actions自动触发
└─ GitHub自动生成exe + Release
```

---

## 🔧 详细设置步骤

### 步骤1: GitHub Actions设置 (一次性)

✅ **已完成**

文件已创建：
- `.github/workflows/build-and-release.yml` - 自动构建工作流
- `commodity_lab.spec` - PyInstaller配置
- `BUILD_AND_RELEASE.md` - 详细文档
- `build.ps1` & `build.sh` - 本地构建脚本

**验证**:
```bash
# 查看工作流文件
ls -la .github/workflows/
find . -name "*.spec"
find . -name "build.*"
```

### 步骤2: 配置VS Code插件 (可选)

#### 2.1 安装Action Buttons

```
Extensions (Ctrl+Shift+X) → 搜索 "Action Buttons" → 安装
```

#### 2.2 创建配置文件

创建 `.vscode/action-buttons.json`:

```json
{
  "buttons": [
    {
      "name": "🔨 Build EXE (Windows)",
      "color": "#2196F3",
      "command": "pwsh -NoProfile -ExecutionPolicy Bypass -Command \"cd '${workspaceRoot}'; .\\build.ps1\"",
      "singleInstance": true,
      "showInStatusBar": true,
      "tooltip": "使用PyInstaller构建Windows EXE"
    },
    {
      "name": "🔨 Build EXE (Linux/Mac)",
      "color": "#2196F3",
      "command": "cd '${workspaceRoot}' && bash build.sh",
      "singleInstance": true,
      "showInStatusBar": true,
      "tooltip": "使用PyInstaller构建应用"
    },
    {
      "name": "🧹 Clean Build",
      "color": "#FFC107",
      "command": "pwsh -NoProfile -ExecutionPolicy Bypass -Command \"cd '${workspaceRoot}'; .\\build.ps1 -Clean\"",
      "singleInstance": true,
      "showInStatusBar": true,
      "tooltip": "清理旧构建文件并重新构建"
    },
    {
      "name": "🚀 Run App",
      "color": "#4CAF50",
      "command": "pwsh -Command \"& '${workspaceRoot}\\dist\\Commodity-Lab.exe'\"",
      "singleInstance": true,
      "showInStatusBar": true,
      "tooltip": "运行已构建的应用"
    },
    {
      "name": "📖 Build Guide",
      "color": "#9C27B0",
      "command": "code ${workspaceRoot}/BUILD_AND_RELEASE.md",
      "singleInstance": true,
      "showInStatusBar": false,
      "tooltip": "打开构建和发布指南"
    }
  ]
}
```

#### 2.3 验证

重启VS Code，在底部状态栏会看到5个按钮：
- 🔨 Build EXE (Windows)
- 🔨 Build EXE (Linux/Mac)
- 🧹 Clean Build
- 🚀 Run App
- 📖 Build Guide

### 步骤3: 创建Release

```bash
# 1. 更新代码和文档
# 修改需要的文件...

# 2. 更新版本
# 编辑 app/main.py 和 pyproject.toml

# 3. 提交
git add .
git commit -m "feat: add new features"

# 4. 创建标签
git tag -a v1.1.0 -m "Release v1.1.0"

# 5. 推送 (自动触发GitHub Actions)
git push origin main
git push origin v1.1.0

# 6. 等待构建 (访问 Actions 页面查看进度)
# 构建完成后，GitHub自动创建Release
```

---

## 🖥️ Windows用户快速开始

### 本地构建 (使用Action Buttons)

1. **打开项目**
   ```
   File → Open Folder → 选择Commodity-Lab目录
   ```

2. **点击状态栏按钮**
   ```
   底部 → 点击"🔨 Build EXE (Windows)"
   ```

3. **等待构建完成** (5-10分钟)

4. **测试应用**
   ```
   底部 → 点击"🚀 Run App"
   ```

5. **发布Release**
   ```
   git tag -a v1.1.0 -m "Release"
   git push origin v1.1.0
   # GitHub自动完成剩余工作
   ```

### 发布Release (全自动)

```bash
# 仅需这3个命令
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
# 完成！GitHub Actions自动生成exe和Release
```

---

## 📱 GitHub Actions工作流状态

### 监控构建进度

访问: https://github.com/AlexYuhuFeng/Commodity-Lab/actions

你会看到：
1. 工作流运行列表
2. 每个工作流的详细日志
3. artifact下载链接

### 常见状态

```
✅ Completed (成功)
   ├─ Build Executable ✅
   ├─ Test Build ✅
   └─ Notify Release ✅

🔄 In Progress (进行中)
   └─ Build Executable (构建中...)

❌ Failed (失败)
   └─ Build Executable
      └─ Error: ... (查看详细错误)
```

---

## 🎓 学习资源

### GitHub Actions
- [官方文档](https://docs.github.com/en/actions)
- [工作流语法](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

### PyInstaller
- [官方网站](https://pyinstaller.org/)
- [FAQ](https://pyinstaller.org/en/stable/FAQ.html)

### VS Code插件
- [Action Buttons](https://marketplace.visualstudio.com/items?itemName=helix-editor.action-buttons)
- [Task Runner](https://marketplace.visualstudio.com/items?itemName=actboy168.tasks)

---

## 🆘 常见问题

### Q: 可以同时使用两种方案吗?
**A**: 完全可以！建议：
- 日常开发: VS Code插件快速构建
- 正式发布: GitHub Actions自动化
- 这样既能快速迭代，又能保证发布的自动化

### Q: 哪个方案更容易?
**A**: 取决于用途：
- **仅用于自测**: VS Code插件 (一键构建)
- **需要发布**: GitHub Actions (完全自动)
- **两都都要**: 组合使用 (推荐 ⭐)

### Q: 需要手动编辑Release Notes吗?
**A**: 
- GitHub Actions自动生成初稿
- 可选手动补充信息
- 完全自动化也可行

### Q: 如何修复构建失败?
**A**: 
1. 查看GitHub Actions日志
2. 根据错误调整`commodity_lab.spec`
3. 本地用`build.ps1`复现问题
4. 修复后重新tag和push

### Q: 支持Mac和Linux吗?
**A**: 
- 当前: Windows (via GitHub Actions)
- 本地: Mac和Linux都支持 (使用build.sh)
- 未来: 可配置多平台GitHub Actions

### Q: Release多久发一次好?
**A**: 建议：
- 小修复: 1-2周
- 功能更新: 2-4周
- 重大版本: 1-3个月

---

## ✨ 总结

| 需求 | 方案 | 优势 |
|------|------|------|
| 快速本地构建 | VS Code插件 | 一键完成 |
| 自动化发布 | GitHub Actions | 完全自动 |
| 同时需要两者 | 组合使用 | 最佳体验 ⭐ |
| 团队协作 | GitHub Actions | 统一流程 |
| 单人开发 | VS Code插件 | 简单快速 |

---

**选择哪种方案？**

→ 推荐 **组合使用** (VS Code + GitHub Actions)

不用纠结，两个都设置上，根据场景选择：
- 开发中？使用VS Code快速构建
- 发布版本？使用GitHub Actions自动化

---

**更新时间**: 2026年2月25日
