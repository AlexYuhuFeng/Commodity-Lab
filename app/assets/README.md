# 🎨 Commodity Lab 应用图标

## 📋 当前状态

此目录应包含应用图标：
- `icon.ico` - Windows应用图标 (256x256 推荐)
- `icon.png` - PNG格式备份 (可选)

## 🛠️ 生成图标

### 方式 1: 在线转换

1. 准备一个PNG图片 (256x256或更大)
2. 访问 [icoconvert.com](https://icoconvert.com/) 或类似网站
3. 上传PNG，下载ICO文件
4. 保存为 `icon.ico`

### 方式 2: 使用Python

```python
from PIL import Image

# 打开PNG图片
img = Image.open("icon.png")

# 调整大小为256x256
img = img.resize((256, 256), Image.Resampling.LANCZOS)

# 转换为ICO
img.save("icon.ico", format="ICO")
```

### 方式 3: 使用ImageMagick

```bash
convert icon.png -define icon:auto-resize=256,192,128,96,64,48,32,16 icon.ico
```

## 📐 推荐尺寸

PyInstaller默认使用以下尺寸：
- 256x256 - 高分辨率
- 128x128 - 标准
- 64x64 - 较小
- 32x32 - 任务栏
- 16x16 - 最小

所有尺寸最好在一个ICO文件中包含。

## 🎭 设计建议

### 应用于Commodity Lab的图标设计思路

1. **颜色方案**: 
   - 主色: 金色或深蓝色 (代表商品交易)
   - 次色: 绿色或红色 (涨跌)

2. **元素**:
   - 图表/柱状图 (代表数据分析)
   - 商品元素 (石油、金属等)
   - 实时数据流指示

3. **样式**:
   - 现代极简风格
   - 清晰易辨识
   - 支持深色和浅色背景

## 🖼️ 常用图标来源

- [Flaticon.com](https://www.flaticon.com/)
- [IconFinder.com](https://www.iconfinder.com/)
- [Material Design Icons](https://fonts.google.com/icons)
- [Font Awesome](https://fontawesome.com/)

## 📝 相关文件

- `build.ps1` - Windows构建脚本会自动使用此图标
- `build.sh` - Linux/Mac构建脚本会自动使用此图标
- `commodity_lab.spec` - PyInstaller配置会参考此路径

## ✅ 验证图标

### 检查图标是否有效

```bash
# Linux/Mac
file icon.ico

# Windows PowerShell
Get-Item icon.ico | Format-List
```

### 在exe中验证

构建后，检查exe的属性：
1. 右键点击 `Commodity-Lab.exe`
2. 选择"属性"
3. 验证图标正确显示

---

**作者**: Commodity Lab Team  
**更新**: 2026年2月25日
