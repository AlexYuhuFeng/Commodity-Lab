# 🚀 Commodity Lab 版本发布 - 快速参考

## 三行代码发布新版本 (全自动)

```bash
git tag -a v1.1.0 -m "Release v1.1.0: 新增功能"
git push origin v1.1.0
# GitHub Actions自动生成exe + Release
```

---

## 完整发布流程 (推荐)

### 步骤1️⃣: 更新版本号

编辑 `app/main.py`:
```python
__version__ = "1.1.0"  # 更新这里
```

编辑 `pyproject.toml`:
```toml
version = "1.1.0"  # 更新这里
```

### 步骤2️⃣: 本地测试构建 (可选)

**Windows**:
```powershell
.\build.ps1
```

**Linux/Mac**:
```bash
./build.sh
```

### 步骤3️⃣: 提交代码

```bash
git add .
git commit -m "feat: 新功能描述"
```

### 步骤4️⃣: 创建标签 (触发自动构建)

```bash
git tag -a v1.1.0 -m "Release v1.1.0: 新增X功能

- ✨ 新增X功能
- 🐛 修复Y问题
- 📚 改进Z文档"
```

### 步骤5️⃣: 推送标签 (触发GitHub Actions)

```bash
git push origin v1.1.0
```

### 步骤6️⃣: 监控构建 (等5-10分钟)

访问: https://github.com/AlexYuhuFeng/Commodity-Lab/actions

查看工作流运行状态 (应该显示绿色✅)

### 步骤7️⃣: 验证Release

访问: https://github.com/AlexYuhuFeng/Commodity-Lab/releases

会看到自动创建的Release，包含:
- ✅ Commodity-Lab-v1.1.0-win64.zip (EXE文件)
- ✅ 自动生成的Release Notes
- 📝 可选手动编辑说明

---

## 📋 版本号规范 (Semantic Versioning)

使用格式: `v主版本.次版本.修订版`

**例子**:
- `v1.0.0` - 首次发布
- `v1.1.0` - 新增小功能
- `v1.1.1` - 修复bug
- `v2.0.0` - 重大改版

**何时递增**:
- 主版本(1→2): 大功能、架构改变
- 次版本(0→1): 新增功能、改进
- 修订版(0→1): 修复bug、文档更新

---

## 🎯 VS Code快速构建 (本地测试)

1. **安装插件**: Action Buttons (VS Code扩展)

2. **查看状态栏**: VS Code底部会出现按钮
   - 🔨 Build EXE - 一键构建
   - 🧹 Clean Build - 清理并重建
   - 🚀 Run App - 运行应用
   - 📖 Building Guide - 查看文档

3. **点击按钮**进行构建和测试

---

## ✅ 发布清单

发布前检查:

- [ ] 更新了版本号 `app/main.py`
- [ ] 更新了版本号 `pyproject.toml`
- [ ] 本地构建通过 (运行 `build.ps1` 或 `build.sh`)
- [ ] 测试了exe功能
- [ ] 更新了CHANGELOG或Release Notes
- [ ] 提交了代码 (`git commit`)
- [ ] 创建了标签 (`git tag`)
- [ ] 推送了标签 (`git push origin v*`)

---

## 🔍 故障排除

### ❌ GitHub Actions失败

1. 访问Actions页面查看日志
2. 查看"Build EXE"步骤的错误信息
3. 常见原因:
   - 依赖缺失: 检查`requirements.txt`
   - PyInstaller配置: 检查`commodity_lab.spec`
   - 路径问题: 检查文件路径是否正确

### ✅ 解决步骤

```bash
# 1. 修复本地问题
./build.ps1
# 测试直到成功...

# 2. 再次提交和标签
git add .
git commit -m "fix: 修复构建问题"
git tag -a v1.1.1 -m "修复版本"
git push origin v1.1.1
```

---

## 💡 常见场景

### 场景1: 小修复，快速发布
```bash
# 修改文件
git add .
git commit -m "fix: 修复bug"
git tag -a v1.0.1 -m "修复版本"
git push origin v1.0.1
```

### 场景2: 新功能，版本升级
```bash
# 修改文件 + 更新版本
git add .
git commit -m "feat: 新增功能"
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

### 场景3: 本地构建测试
```bash
# Windows
.\build.ps1

# Linux/Mac
./build.sh

# 运行测试
.\dist\Commodity-Lab.exe
```

### 场景4: 重新构建 (清理旧文件)
```bash
# Windows
.\build.ps1 -Clean

# Linux/Mac
./build.sh --clean
```

---

## 📊 发布时间线

```
你执行      GitHub Actions    用户看到
(第0分钟)   (第2-10分钟)      (第10分钟)

git tag
    ↓
git push
    ↓
        GitHub Actions启动
            ↓
        收集依赖 (1分钟)
            ↓     
        PyInstaller构建 (5-8分钟)
            ↓
        上传artifact (1分钟)
            ↓
        创建Release ✅
            ↓
        Release页面可见 ✅
```

---

## 🌐 GitHub Release页面

Release会自动包含:

```
📌 Release v1.1.0
├─ 📝 Release Notes (自动生成)
├─ 📦 Commodity-Lab-v1.1.0-win64.zip
└─ ✅ Published (时间戳)
```

用户可以:
- 🔗 复制下载链接
- 📥 直接下载exe
- 💬 查看更新说明
- ⭐ 标星Release

---

## 🎓 更多参考

详细文档: [BUILD_AND_RELEASE.md](BUILD_AND_RELEASE.md)
完整指南: [PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)

---

**最后更新**: 2026年2月25日
**作者**: GitHub Copilot
