# 更新日志

## 2024-04-13 (0.23.39)
- 改进：优化UI界面元素尺寸，增加下拉框和标签的高度和字体大小
- 优化：增大QComboBox下拉菜单高度和字体，改善文字可读性
- 优化：调整RadioButton尺寸和字体，提高可用性
- 改进：增大"Download Model"按钮高度和字体，与其他UI元素保持一致
- 调整：适当增加窗口高度(600->650px)，确保所有UI元素正常显示

## 2024-04-13 (0.23.38)
- 改进：优化模型选择UI，修复下拉菜单中文字显示问题，改进文字和背景颜色对比度
- 新增：添加删除模型功能，可通过下拉菜单选择删除不再需要的模型
- 改进：已下载模型显示名称和文件大小信息，方便管理
- 新增：添加关于窗口，显示版本信息和项目链接
- 优化：关于窗口中添加项目GitHub链接和作者链接，支持点击直接打开

## 2024-04-12 (0.23.37)
- 修复：优化distil-small.en和distil-medium.en模型的检测逻辑，确保下载后能正确被识别
- 改进：增强了引擎中对不同模型类型的线程优化支持
- 修复：解决macOS应用打包中权限设置问题，确保应用能够正确请求麦克风和文本输入权限
- 技术：改进Info.plist处理方式，使用plistlib直接修改二进制plist文件，提高权限设置的可靠性

## 2024-03-21
- 改进了模型下载逻辑，使用 huggingface-cli 命令行工具
- 添加了模型缓存目录检查
- 优化了模型路径处理
- 添加了录音控制按钮（绿色开始/红色停止）
- 添加了空格键控制录音功能
- 添加了识别结果显示区域
- 改进了模型路径处理，优先使用已下载的模型
- 添加了默认模型路径检查
- 优化了模型加载逻辑
- 添加了主窗口界面，支持图形化操作
- 改进了模型下载路径处理，支持从缓存目录加载模型
- 添加了模型检查和下载状态显示
- 添加了录音和识别状态显示
- 改进了程序退出处理，支持窗口关闭和 Ctrl+C 退出
- 更新了模型下载方式，使用 huggingface-cli 进行下载
- 改进了程序退出处理，确保 Ctrl+C 可以正常退出
- 优化了模型下载错误处理
- 更新了模型下载路径（从 guillaumekln 更改为 Systran）
- 添加了程序退出处理，支持 Ctrl+C 正常退出
- 添加了模型下载错误处理
- 优化了模型加载的错误提示
- 更新了安装步骤，添加了环境激活说明
- Upgraded faster-whisper to version 1.1.1
- Added word-level timestamp support
- Improved model download and management features
- Added logging configuration
- Optimized model loading and recognition processes
- Added system resource detection and model recommendation features
- Fixed model download path issues
- Added model version compatibility checks
- Renamed platform directory to platform_specific to avoid conflicts with standard library
- Configured conda environment to resolve dependency installation issues

## 2024-03-22
- Added model detection feature to automatically detect and use downloaded models
- Added audio visualization with real-time waveform display
- Improved UI with better button states and visual feedback
- Added automatic input device selection
- Added text input functionality to current focus position
- Added pyautogui dependency for text input
- Removed custom window controls in favor of system window controls
- Added real-time audio level visualization
- Improved error handling and user feedback
- Added model detection logging

## 2024-04-08
- 重构了文本插入功能:
  - 全面改进macOS文本插入方式
  - 添加三种不同的输入方法备选
  - 增加剪贴板操作支持
  - 优化错误处理和日志记录
- 改进了平台兼容性:
  - 增强对MacOS的支持
  - 完善Windows和Linux支持
  - 添加详细的调试日志
- 增加了文本输入测试工具:
  - 添加独立测试脚本
  - 支持多种输入方法测试
  - 提供倒计时和状态反馈
- 版本号更新至 0.23.39

## 2024-04-08 (0.23.23)
- 修复了AudioRecorder的stop方法缺失问题
- 优化了设备选择逻辑，自动选择第一个可用的音频输入设备
- 改进了日志显示功能，确保所有日志正确输出到界面
- 优化了波形显示初始化，默认显示浅粉色波形
- 优化了录音控制逻辑，添加更详细的调试输出

## 2024-04-08 - 版本0.23.26
- 修复录音按钮点击后无反应的问题
- 增加信号连接，确保空格键和按钮能正确触发录音功能
- 修复设备变更信号连接问题，确保设备选择后能正确生效

## 0.23.27 - 2024-04-09
- 修复 AudioRecorder 类中缺少 stop 方法的问题
- 重构 AudioRecorder 类以提高稳定性：
  - 添加线程锁确保线程安全
  - 改进录音保存逻辑
  - 优化音频电平检测
  - 添加更完善的错误处理

## 0.23.28 - 2024-04-09
- 修复了 setup_logging() 函数参数问题
- 添加了 FloatingWindow 配置参数支持
- 实现了录音设备选择和状态管理接口
- 改进了日志系统，支持更好的日志文件管理
- 优化了用户界面状态更新机制
- 提升了录音设备管理接口

## 2024-04-08 - 版本0.23.27
- 修复录音按钮状态显示问题：确保录音时显示红色方块、停止时显示绿色三角形
- 添加临时录音文件自动清理功能：自动清理7天前的录音文件
- 修复UI状态更新问题，确保录音状态与按钮显示保持一致
- 优化日志输出，提供更清晰的状态变化记录

## 2024-04-09 - 版本0.23.28
- 添加录音模式选择功能：支持批量转写和实时转写两种模式
- 实现实时转写功能：录音时实时显示识别结果
- 优化录音文件管理：仅保留最近3个录音文件，自动清理其他文件
- 改进音频处理逻辑：添加实时处理回调机制
- 优化模型加载和初始化流程
- 完善状态提示和日志输出

## 2024-04-09 - 版本0.23.29
- 优化实时转写功能：提高响应速度和转写实时性
- 减少音频采样间隔：从0.5秒减少到0.3秒，提高实时感
- 优化音频缓冲区管理：防止缓冲区过大影响性能
- 调整转写参数：降低beam size和静音检测时间，加快处理速度
- 添加缓冲区大小限制：自动裁剪过旧数据，保持内存使用效率
- 改进状态显示：实时显示缓冲区大小和处理状态

## 2024-04-08 (0.23.24)
- 优化了文本输入功能，解决了中文输入法兼容性问题
- 添加了模型选择功能，支持选择和下载不同大小的模型
- 支持自动检测已下载的模型并优先使用
- 添加模型下载功能，支持下载base/small/medium/large-v3/distil-large-v3模型
- 优化了模型加载和切换逻辑，提高了系统响应性
- 多核CPU优化，充分利用可用线程提高转写性能
- 修复OpenMP库冲突问题，提高跨平台兼容性

### 改进
- 修复了下载模型时可能出现的"list index out of range"错误
- 增强模型下载逻辑中的错误处理，确保用户取消和无效选择的情况得到妥善处理
- 添加更多日志输出，帮助诊断模型下载过程中的问题

## 2024-04-08 (0.23.25)
- 修复了模型下载后界面未正确更新为"已下载"的问题
- 优化了应用图标，将文字从"BCC"改为"BongCaCa"并采用换行显示
- 修复了音频电平检测问题，确保波形能正确显示
- 优化了录音设备初始化过程，更明确地设置和使用选定设备
- 改进了录音线程管理，增加了更多错误处理和日志
- 在非录音状态下添加低电平波形显示，提高视觉反馈

## 2024-04-08 (0.23.26)
- 修复模型选择功能，确保选择模型后正确显示加载日志
- 修复模型下载功能，下载成功后自动将模型移至已下载区域
- 增强录音设备初始化过程，添加有效性检查和提示音
- 优化音频电平检测算法，使用RMS和对数比例计算更准确的电平值
- 添加录音线程启动检查，确保录音功能正常
- 改进UI交互体验，提供更清晰的状态反馈

## 2024-04-08 (0.23.27)
- 修复：解决模型下载功能中可能导致的"list index out of range"错误
- 优化：改进模型下载弹窗逻辑，使用按钮引用而非索引，提高代码健壮性
- 增强：添加更完善的错误处理逻辑以确保模型下载功能稳定性
- 版本号更新: 从0.23.26更新到0.23.27
- 确保AudioRecorder类包含stop方法
- 优化设备选择逻辑，自动选择第一个可用音频输入设备
- 优化日志显示功能，确保所有日志正确输出到界面
- 优化波形显示初始化，默认显示浅粉色波形
- 优化录音控制逻辑，增加更详细的调试输出
- 修复：解决了音频电平计算中的"invalid value encountered in sqrt"警告
- 优化：提高了音频电平计算的稳定性，确保在处理音频数据时不会出现无效值

## 2024-04-08 (0.23.28)
- 修复：解决了非录音状态下粉色波形不显示的问题
- 优化：添加定时器确保非录音状态下也能显示波形动画
- 改进：使用随机值生成非录音状态下的波形，提升视觉体验

## 2024-04-09 (0.23.29)
- 修复：录音时粉色电平显示问题，增加音频电平显示灵敏度
- 优化：改进音频电平计算方法，增强低音量视觉反馈
- 修复：macOS应用图标不显示问题，改进图标生成流程
- 新增：添加应用打包功能，支持创建macOS应用(.app和.dmg)和Windows应用(.exe和安装程序)
- 优化：减少日志频率，改为每0.5秒记录一次音频电平

## 2024-04-10 (0.23.30)
- 修复：解决语言设置问题，确保未选择语言时默认使用中文
- 优化：添加语言自动检测支持，可设置为"auto"由模型自动识别语言
- 改进：完善模型翻译功能，支持将语音直接翻译成指定语言输出
- 新增：添加了get_selected_language和get_target_language辅助方法，增强语言设置的灵活性
- 修复：修正了faster-whisper参数使用方式，确保语言和翻译参数配置正确
- 改进：优化了run_recording_loop函数，更好地支持批量和实时转写两种模式
- 修复：已下载模型点击下载按钮时出现的类型错误问题
- 优化：调整应用图标文字大小，使BongCaCa文字更加明显
- 新增：添加GitHub发布指南文档，详细说明如何将打包好的应用上传发布到GitHub
- 文档：添加GitHub Actions自动化构建和发布流程示例

## 2024-04-10 (0.23.31)
- 修复：解决模型下载过程中的"QTimer"未定义错误
- 修复：修复下载模型对话框点击"取消"按钮导致的索引越界错误
- 改进：优化模型检测逻辑，显示详细的模型路径和大小信息
- 新增：添加录音文件的详细统计信息(文件大小、录音时长、转写时间、字符数)
- 优化：在图形界面和日志中显示更详细的模型检测和录音统计信息

## 2024-04-10 (0.23.32)
- 修复：解决录音结束后出现的内存错误问题，修改帧数据处理方式
- 改进：在录音统计信息中增加显示当前使用的模型名称
- 优化：重构录音器的stop方法，增强稳定性和资源释放机制
- 优化：改进录音数据的保存过程，避免非对齐指针错误

## 2024-04-10 (0.23.33)
- 改进：转写结果现在会自动复制到系统剪贴板，方便用户直接粘贴到其他应用
- 新增：添加两种快捷键方式快速输入转写结果
  - Shift+V：直接输入最近的转写结果到当前光标位置
  - 双击Shift：同样可以输入最近的转写结果
- 优化：不再默认自动输入文本，避免干扰用户当前操作
- 改进：添加更友好的状态提示，清晰显示可用的粘贴快捷键

## 2024-04-10 (0.23.34)
- 改进：记住上次选择的模型，下次启动时自动选择
- 修复：解决某些系统上转写完成后出现segmentation fault崩溃的问题
- 优化：改进转写引擎内存管理，增强释放资源的机制
- 优化：重构临时文件处理方式，增加安全检查和清理
- 技术改进：优化segments和info对象的生命周期管理，避免悬挂引用

## 2024-04-10 (0.23.35)
- 修复：解决macOS构建应用时出现的`_struct.cpython-311-darwin.so is not a fat binary!`错误
- 优化：移除PyInstaller构建参数中的`--target-architecture=universal2`，以兼容conda环境
- 改进：构建脚本现在可以在conda环境中正常工作，生成适用于当前架构的应用程序
- 注意：如需构建通用二进制(Intel/Apple Silicon)，请使用系统Python而非conda环境

## 初始化安装步骤

1. 安装 Homebrew（如果没有）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. 安装 Miniconda（如果没有）
```bash
brew install --cask miniconda
```

3. 初始化 conda
```bash
conda init zsh  # 如果使用 bash，则运行 conda init bash
```

4. 关闭并重新打开终端

5. 创建并激活 conda 环境
```bash
conda create -n voice_typer python=3.11
conda activate voice_typer
```

6. 安装依赖
```bash
conda install -c conda-forge ctranslate2
conda install -c conda-forge pyside6
pip install -U huggingface_hub
pip install -r requirements.txt
```

7. 运行程序
```bash
conda activate voice_typer  # 确保环境已激活
python main.py
```

注意：如果遇到 PyQt6 相关错误，请使用 conda 安装 pyside6：
```bash
conda install -c conda-forge pyside6
```

注意：
1. 如果遇到 Qt 相关错误，请完全卸载并重新安装：
   ```bash
   pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip PySide6
   pip install --no-cache-dir PySide6
   ```

2. 如果仍然遇到 Qt 平台插件错误，请尝试：
   ```bash
   conda install -c conda-forge pyside6
   ``` 

  
conda activate voice_typer && python main.py



https://huggingface.co/Systran/faster-whisper-base
https://huggingface.co/Systran/faster-whisper-small
https://huggingface.co/Systran/faster-whisper-medium
https://huggingface.co/Systran/faster-distil-whisper-large-v3

