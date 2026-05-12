# BlueTimer 安装包构建

当前项目已经提供两种方式。

## 方式一：自包含安装器（已使用）

不依赖 Inno Setup，使用 PyInstaller 打包安装器：

```powershell
cd BlueTimer
cd installer
..\.venv\Scripts\pyinstaller.exe --clean uninstall.spec
..\.venv\Scripts\pyinstaller.exe --clean setup.spec
```

生成文件：

```text
installer\dist\BlueTimer_Setup_v0.1.0.exe
```

安装包会把 `BlueTimer.exe` 和 `Launcher.exe` 安装到：

```text
C:\Program Files\BlueTimer
```

并创建开始菜单快捷方式。桌面快捷方式可在安装时勾选。

## 方式二：Inno Setup 脚本

如果本机安装了 Inno Setup 6，也可以编译 `BlueTimer.iss`：

```powershell
cd BlueTimer
ISCC.exe .\installer\BlueTimer.iss
```
