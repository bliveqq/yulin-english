# 雨林英语

面向安卓平板的初中英语学习与授课工具，当前版本 1.4.0。

## 功能

- 单词学习、三轮生词复习、语法与专项练习、错题记录。
- 按地区和年份查找全国中考真题，完整离线版 APK 内置原卷与听力。
- PDF 批注和手写白板。荧光笔以 10% 透明度置于手写字迹下方。
- 原生音频播放器、系统英语语音配置及可选 DeepSeek 接口。

## 目录

- `src/`：安卓原生代码与 WebView 桥接。
- `assets/`：界面、交互和离线教学逻辑。
- `res/`、`AndroidManifest.xml`：安卓资源及安装配置。
- `tools/`：本地资料导入和整理脚本。
- `tests/`：资料、桥接、复习流程和笔迹图层检查。
- `server/`：可选独立下载服务器部署配置，尚未完成公网部署。

## 构建条件

本仓库保存源码，不含题库原件、生成的大型数据集、APK、SDK 或签名密钥。只克隆源码不能直接生成完整离线 APK。

`build.py` 当前针对 macOS 上的本地 SDK/JDK 路径编写；构建前请核对并调整脚本中的 `CACHE`、`JDK`、`TOOLS`、`PLATFORM`。需要 JDK 17、Android API 35 平台文件与官方 Android 构建工具。签名材料保存在项目目录之外，不可提交到 Git。

完整离线构建还需恢复以下本地资料：

- `assets/library-v110.sqlite` 及导入脚本生成的清单。
- `assets/study-data.json`、`assets/national-*.json`、`assets/national/`。
- `assets/audio-compat.json`、`assets/audio-compat/`。
- `assets/builtin-manifest.json` 和 `cloud-deploy/public/` 下与其一致的 2,498 份资料。

相关导入流程见 `tools/` 和 `使用说明.md`。题库和教材内容的使用权限不因源码入库而改变。

准备好依赖和数据后执行 `python3 build.py`。输出位于 `release/`。现有版本使用相同签名进行覆盖升级；更换签名不能直接覆盖原版。

## 验证

```sh
node --test tests/ink-layers.test.mjs tests/native-bridge.test.mjs tests/study-progress.test.mjs
python3 tests/builtin-apk.test.py
```

第二条检查需要先生成完整离线 APK。本版已完成包内资料校验和签名检查，未完成安卓实机验收。

## 隐私与部署

学习记录和批注保存在设备中。AI 请求需要用户配置接口；密钥不得写入源码。独立服务器配置仅提供资料下载，不包含账号同步或 AI 后端。
