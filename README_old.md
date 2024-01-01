<div align="center">
  <img src="imgs/proz_icon_old.ico" />
  <br />

[![](https://img.shields.io/badge/projz_renpy_translation-0.3.8-brightgreen.svg)](https://github.com/abse4411/projz_renpy_translation)
[![](https://img.shields.io/badge/license-GPLv3-blue)](https://github.com/abse4411/projz_renpy_translation/blob/devp/LICENSE)

[📘文档（Chinese only）](#) |
[🛠安装](#运行环境准备) |
[💡建议](https://github.com/abse4411/projz_renpy_translation/issues)

简体中文 | [English (N/A)](#帮助我们翻译help-us-translate-the-documentation)

</div>

# ✨新版本
- 无需RenPy SDK即可生成rpy翻译文件，和原生体验类似
- 可以检测和发现rpy文件中的错误
- 实现游戏注入，可以为RenPy游戏提供语言和字体管理菜单，支持实时生效
- 更简洁，规范的代码，支持实现自定义的翻译接口

## ✨新版本现在已经基本完成，我们支持直接生成rpy翻译文件到游戏中，并实现I18n插件注入。 欢迎体验：[projz_renpy-translator](https://github.com/abse4411/projz_renpy-translator)
## 🚨注意新版本不支持0.4.0之前的存档。后续开发完成后将直接更新到这个项目中。
## 🚨当前版本即将被覆盖为新版本，请逐步迁移到新版本


# 🍕RenPy翻译工具
- 本工具需要具有一定动手能力🔧，如果了解Renpy翻译流程更佳。
- 通过本工具，您可用来：
  - 以项目为单位来管理您RenPy游戏翻译版本(在您的翻译文件夹下`/your_renpy_game/game/tl`)，支持多种语言(`/game/tl`下的子文件夹)
  - 合并/迁移您的同一游戏旧版本的翻译文本到新版本中。这可以让旧版本的翻译文本得到复用。
  - 使用不同翻译方式翻译您的RenPy游戏。目前支持三种方式：
    - 利用Selenium调用Chrome的Web翻译🌐(可用的Web API翻译引擎：Google、Caiyun、Youdao、Baidu
    - 使用Microsof Edge的网页全文翻译功能或者使用excel文件上传到支持翻译网站
    - 使用来自[dl-translate](https://github.com/xhluca/dl-translate)的AI模型翻译🤖
  - 导入和导出游戏翻译文本，这使得您可手动翻译或者修改错误的翻译。
  - 使用一些辅助性工具(目前还在开发中)，比如将已翻译文本重置为未翻译状态，针对翻译项目的excel文件导入导出
- 常见问题在[这里](#常见问题)
- 命令说明在[这里](#命令说明)
- 常见概念在[这里](#常见问题)的术语
- 配置文件[config.ini](config.ini)说明在[这里](#configini配置说明)
- 我们项目参考了这些项目，见: [Acknowledgement](#Acknowledgement)
- 该代码仅供学习使用，我们不提供任何游戏文件❗
- 我们将运行环境和程序打包为exe，见代码目录下的[parse_console.exe](parse_console.exe)。因此您可以直接运行程序(仅限在64位的Windows系统)，而不需要安装任何依赖库(包括Python🐍!)。但是以下翻译功能将无法使用：
  - AI模型翻译🤖
  
  如果您想使用完整功能请安装完整的环境：[运行环境准备](#运行环境准备)
***

👀已经了解以上内容，想要开始使用，请跳转到👉[这里](#运行环境准备)👈

# 🙏帮助我们翻译(Help us translate the documentation)

如果您觉得本项目有用，即使您不会进行Python开发，也可以帮助我们翻译这个界面到其他语言。😀

If you like this project, you can help us translate this page. That would be great! 😀

***

# 📜Changelog:
<details>
<summary><b>点击展开</b></summary>

* V0.3.8a(功能改进):
  * 改进html保存格式，现在您可以使用Chrome网页翻译功能
  * 修复配置读取编码问题
  * 添加`reold`命令，现在您可以一个重新从一个已有翻译项目重新运行`old`命令，见[reold或ro](#reold或ro)。
  * 现在您可以在config.ini设置RenPy keywords, 帮助程序扫描更多的文本，见[configini配置说明](#configini配置说明)-KEYWORDS。
  * 现在您可以在config.ini配置translate和dltranslate命令去除{}标签，见[configini配置说明](#configini配置说明)-STRIP_TAGS。
  * 文档补充。

* V0.3.8: 
  
  * 添加了新命令`removeempty`，它可以帮助您把项目中空字符串的已翻译文本转换到未翻译的文本中(new_str='' while old_str!='')，以便重新翻译，见[update或up](#update或up)。
  * 在配置文件中[config.ini](config.ini)增加了新的配置项：`REMOVE_MARKS`，设置为True时，`apply`命令产生的文本不会有带有特殊标记（'@$'或'@@'）。
  * 修复`apply`命令的已知问题，添加一个新的参数`skip_unmatch`，设置为True时，apply命令在生成rpy文件时会跳过那些new_str!=old_str的文本。

* V0.3.7: 
  
  * 添加了新命令`revert`，其功能与`apply`命令相反，即把翻译的文本变成原始未翻译的文本, 见[revert或r](#revert或r)。
  * 改进了`dump`命令输出，现在您可以输出项目所有翻译和未翻译的文本到excel文件，且按文件分别输出到不同的sheet中，同一个sheet文本按行号排序。
  * 添加了新命令`update`，它可以配合`dump`命令使用，因此您可以通过修改`dump`命令导出excel文件来更正一个项目中翻译或者未翻译的文本。这类似`saveexcel`和`loadexcel`命令，见[update或up](#update或up)。

* V0.3.6: 修复了使用web翻译多线程的问题，部分命令功能改进。

* V0.3.5: 基于开源项目[dl-translate](https://github.com/xhluca/dl-translate)，我们集成AI模型进行翻译，实现离线翻译的功能。 对应的新命令为`dltranslate`，见[使用dltranslate命令进行ai翻译](#使用dltranslate命令进行ai翻译)。

* V0.3.4: 我们把程序和运行环境打包成exe，现在您不需要python环境就可以运行程序。仅支持64位的Windows 10, 11系统。

* V0.3.3: 修复`apply`命令替换空文本的问题；翻译文本识别改进；新命令`accept`:针对那些不需要翻译文本，现在您可以把未翻译文本合并到翻译的文本中。

* V0.3.2: 修复翻译文本识别问题，现在能识别更多的翻译文本；新命令`dump`:现在您可以把一个项目所有翻译文本导出为excel，见[dump或du](#dump或du)。

* V0.3.1: 添加excel文件的导入导出功能（`saveexcel`和`loadexcel`命令），功能与`savehtml`和`loadhtml`命令类似。

* V0.3.0: 改进翻译索引，减少对翻译文本的丢弃。

* V0.2.0: 使用`savehtml`和`loadhtml`快速翻译，见[使用savehtml和loadhtml快速翻译](#使用savehtml和loadhtml快速翻译浏览器自带网页翻译)。

</details>

***

## 使用`saveexcel`和`loadexcel`⚡快速⚡翻译
  
  使用`saveexcel`和`loadexcel`命令，导出未翻译文本为excel文件，然后借助Google翻译上传excel文件进行翻译，翻译完成覆盖原始html文件，实现翻译文本快速导入。请输入`help`命令获取详细信息。
  
### 使用步骤：
1. 使用`saveexcel {proj_idx}`命令，导出未翻译文本为excel文件，然后然后打开Google翻译（任何支持excel文档翻译的网站）使用文档翻译功能，上传该excel文件：![](./imgs/google_excel.png)
2. 等待翻译完成，下载翻译好的excel并覆盖原始的excel文件：

    ![](./imgs/google_excel_done.png)

3. 使用`loadexcel {proj_idx}`命令，把翻译过的excel文件导入项目。
4. 使用`apply {proj_idx}`命令生成rpy文件即可。

> **😕翻译网站不支持文件excel文件？**<br />
> 您可以把excel文件内容粘贴到doc文件中，再上传doc文件进行翻译。当翻译完成后，把doc文件内翻译的内容重新覆盖原始excel文件即可。
---

## 使用`savehtml`和`loadhtml`⚡快速⚡翻译（浏览器自带网页翻译）
  
  使用`savehtml`和`loadhtml`命令，导出未翻译文本为html文件，然后借助Microsoft Edge浏览器翻译网页并保存覆盖原始html文件，实现翻译文本快速导入。请输入`help`命令获取详细信息。
  
### 使用步骤：
1. 使用`savehtml {proj_idx}`命令，导出未翻译文本为html文件，然后Microsoft Edge打开它。
2. 右键，使用翻译网页功能,或者在地址栏右边找到翻译网页按钮：

    ![](imgs/trans_menu.png)
    ![](imgs/trans_edge.png)

3. 滚动界面让所有文本都翻译完毕。
4. `Ctrl + S` 保存文件，并覆盖原始的html文件。
5. 使用`loadhtml {proj_idx}`命令，把翻译过的html文件导入项目。
6. 使用`apply {proj_idx}`命令生成rpy文件即可。

---

## 使用`dltranslate`命令进行AI翻译🤖

使用方法和`translate`命令类似：`dltranslate {proj_idx} {model_name}`，🚨需要注意🚨的是：

* 需要安装Python3环境，见[运行环境准备](#运行环境准备)

* {model_name} 可选的模型有：m2m100, mbart50, and nllb200

* 可利用NVIDIA GPU进行加速，需要安装NVIDIA GPU支持CUDA的Pytorch版本，见[运行环境准备-步骤3](#3安装cuda支持的pytorch)。

* 如果在运行过程下载模型遇到以下问题：
  
    ![dlt_downloaderror.png](imgs/dlt_downloaderror.png)
  
    请手动下载模型到本地目录，假设您的保存模型目录为：`C:\hf_models`，可用模型下载地址如下：
  
    - m2m100：https://huggingface.co/facebook/m2m100_418M/tree/main
  
    - mbart50：https://huggingface.co/facebook/mbart-large-50-many-to-many-mmt/tree/main
  
    - nllb200：https://huggingface.co/facebook/nllb-200-distilled-600M/tree/main
  
    选择一个模型，在模型`C:\hf_models`目录下建立一个模型同名文件夹，如`m2m100`，`mbart50`，`nllb200`，然后把所有文件下(除了`rust_model.ot`)载到对应模型文件夹下，例如：`C:\hf_models\m2m100`：
  
    ![dlt_downloadmodel.png](imgs/dlt_downloadmodel.png)
  
    等文件都下载完后在配置文件`config.ini`中设置`MODEL_SAVE_PATH`选项：
  
  ```ini
  [GLOBAL]
  ...
  # path for saving deep models
  MODEL_SAVE_PATH=C:\hf_models
  ```
  
    最后[运行程序](#启动)即可。

### 使用步骤：

1. 输入`dltranslate {proj_idx} {model_name}`命令，可以参考`translate`命令，只是`model_name`可选的有：`m2m100`，`mbart50`，`nllb200`
2. 设置翻译目标，例如您想从英语翻译到中文，分别输入英语和中文对应索引号就行：
    ![dlt_settarget.png](imgs%2Fdlt_settarget.png)
3. 设置模型前向每次翻译文本数量，如果您不使用显卡加速根据您的电脑内存情况设置，如果用GPU加速则根据您的GPU内存决定：
    ![dlt_setbz.png](imgs%2Fdlt_setbz.png)
4. 等待翻译完后使用`apply {proj_idx}`命令生成rpy文件即可。

---
# 🛠运行环境准备

我们已经打包好所有环境依赖（Python3和依赖库）成exe文件，点击目录下的👉[parse_console.exe](parse_console.exe)即可运行。
也就是说您可以完全***跳过本步骤***，快进到⏩[快速开始](#快速开始)。如果使用exe运行，您将无法使用AI模型翻译🤖，而Web翻译需要🌐下载一些额外的软件，详细请见下的注意事项：

> **🚨注意🚨**<br />
> - 如果您想要使用Web翻译功能🌐，请根据下面的[步骤2](#2安装chrome浏览器和chrome-driver)安装Chrome浏览器和对应的chrome driver后在打开[parse_console.exe](parse_console.exe)运行。
> - 如果您想要使用AI翻译功能🤖，请根据下面的[步骤1](#1安装python3和依赖库)安装Python3环境，然后使用python脚本运行：`python3 parse_console.py`
> - 如果您想要*⚡加速⚡*AI翻译功能🤖，请根据下面的[步骤3](#3安装cuda支持的pytorch)的装支持的CUDA和对应的pytorch，然后使用python脚本运行：`python3 parse_console.py`

## 1.安装Python3和依赖库
建议使用[Miniconda](https://docs.conda.io/projects/miniconda/en/latest/)安装Python3虚拟环境。当您安装完成时，在当前代码目录下打开一个控制台窗口，并激活一个虚拟Python3环境，运行以下命令：
```bash
pip install -r requirements.txt
```
这将安装程序运行所需要Python依赖库。

## 2.安装Chrome浏览器和chrome driver
> **🚨注意🚨**<br />
> 如果您不想使用Web翻译功能，请跳过此步骤。

下载并安装[Chrome浏览器](https://www.google.com/chrome/)。安装完成后，进入：设置->关于Chrome，找到您的Chrome版本，前往以下链接下载对应的chrome driver：
* [Chrome版本116.x.xxxx.xxx以下](https://registry.npmmirror.com/binary.html?path=chromedriver/) 
* [Chrome版本116.x.xxxx.xxx或更高🆕](https://googlechromelabs.github.io/chrome-for-testing/#stable)

下载针对含有"win"(win64/win32取决于您的Windows系统。我们仅在Windows系统测试通过，理论上其他系统（Mac、Linux）也是支持的。)字样的chrome driver，并解压到自定义目录下。 在代码目录下的配置您的`chrome driver`文件路径，在`config.ini`中修改`CHROME_DRIVER`为您的`chromedriver.exe`文件的绝对路径。

```ini
[GLOBAL]
...
# The path of chrome driver (Your chromedriver.exe path here)
CHROME_DRIVER=D:\Users\Surface Book2\Downloads\chromedriver_win32\chromedriver.exe
...
```

## 3.安装CUDA支持的Pytorch
> **🚨注意🚨**<br />
> 如果您不想加快您的AI翻译速度，请跳过此步骤。因为在[步骤1](#1安装python3和依赖库)中已经安装了Pytorch，因此您可以使用CPU进行AI翻译（这意味着您需要较大内存来支持加载AI模型）。

无论您的电脑是否具有NVIDIA GPU，您都可以在安装完后Pytorch后使用AI模型翻译功能。假如您刚好具有一块NVIDIA GPU，那么您可以利用CUDA支持的Pytorch加快您的AI翻译速度。

在[步骤1](#1安装python3和依赖库)中，`requirements.txt`指定pytorch版本为`2.0.1+cu117`，意味着这里默认安装支持具有CUDA版本为11.7支持的Pytorch。如果您NVIDIA GPU的CUDA版本刚好11.7则可以跳过本步骤。
以下是步骤将引导您安装CUDA支持的Pytorch版本：
1. 打开控制台，使用以下命令查看您的CUDA版本：
    ```bash
    nvidia-smi
    ```
    一般它将输出如下信息：
    ```txt
    +-----------------------------------------------------------------------------+
    | NVIDIA-SMI 517.48       Driver Version: 517.48       CUDA Version: 11.7     |
    |-------------------------------+----------------------+----------------------+
    | GPU  Name            TCC/WDDM | Bus-Id        Disp.A | Volatile Uncorr. ECC |
    | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
    |                               |                      |               MIG M. |
    |===============================+======================+======================|
    |   0  NVIDIA GeForce ... WDDM  | 00000000:02:00.0 Off |                  N/A |
    | N/A   33C    P0    21W /  N/A |      0MiB /  6144MiB |      1%      Default |
    |                               |                      |                  N/A |
    +-------------------------------+----------------------+----------------------+
    
    +-----------------------------------------------------------------------------+
    | Processes:                                                                  |
    |  GPU   GI   CI        PID   Type   Process name                  GPU Memory |
    |        ID   ID                                                   Usage      |
    |=============================================================================|
    |  No running processes found                                                 |
    +-----------------------------------------------------------------------------+
    ```
    我们可以看到现在的CUDA版本为: 11.7

2. 为了确保安装指定版本的Pytorch，在安装新版本前使用以下命令卸载旧版本Pytorch和transformers库：
    ```bash
    pip uninstall torch torchaudio torchvision transformers
    ```
    然后接着前往[Pytorch官网](https://pytorch.org)找到对应CUDA的Pytorch版本，打开控制台按照指令安装。如果没有发现相关的CUDA版本可以在[此链接](https://pytorch.org/get-started/previous-versions/)找到旧的CUDA支持的Pytorch版本。例如，以下是我找到关于CUDA11.7的Pytorch安装信息：
      ```bash
    # For Linux and Windows
    # ROCM 5.4.2 (Linux only)
    pip install torch==2.0.1+rocm5.4.2 torchvision==0.15.2+rocm5.4.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/rocm5.4.2
    # CUDA 11.7
    pip install torch==2.0.1+cu117 torchvision==0.15.2+cu117 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu117
    # CUDA 11.8
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
    # CPU only
    pip install torch==2.0.1+cpu torchvision==0.15.2+cpu torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu
    ```
3. 完成上一步后，重新安装合适的transformers库：
    ```bash
    pip install transformers
    ```


# 🕹启动
您可以直接打开目录下[parse_console.exe](parse_console.exe)直接运行(部分功能将受限，见[运行环境准备](#运行环境准备))，或者在您安装上面Python3环境安装后使用Python脚本启动：
```bash
python3 parse_console.py
```

运行效果：

![](imgs/console_preview.png)


# 🏹快速开始
## 👀流程速览
![](imgs/pipeline.png)

## 1.从旧版本RenPy翻译构建(如果没有，请跳过)：

构建一个旧版本翻译项目，输入命令`old`或者`o`：

```shell
o {tl_dir} {游戏名} {版本}
```
<details>
<summary><b>💡关于old命令 (点击展开)</b></summary>

- 它会递归扫描{tl_dir}目录下所有后缀名为`.rpy`的文件。
- 它只获取每个rpy中的new_str!=old_str的文本，也就是我们认为原始文本"Hello world!"的翻译文本为："你好世界！"，如下所示：
    > ```txt
    > # game/ImaniEvents.rpy:11
    > translate chinese callimanimorning_88744462:
    > 
    >     # "Hello world!"   <= old_str
    >     "你好世界！"        <= new_str
    > ```
  并把"callimanimorning_88744462"作为翻译的索引号，这与RenPy行为保持一致。
</details>

`{tl_dir}`为游戏翻译文件所在目录，例如`D:\my_renpy\game\tl\chinese`。`{游戏名}`和`{版本}`请自定义，注意保存项目文件时候会用到它们（保存的项目文件为：`{游戏名}_{版本}.pt`），确保它们符合系统文件名要求。

一个例子：

![](imgs/old.png)

然后试试`list`或`l`命令，他将列出当前存在和翻译项目和它们对应索引号：

```shell
l
```

效果图：

![](imgs/list.png)

## 2.创建新版本的翻译项目

构建一个新版本翻译项目，输入命令`new`或者`n`：

```shell
n {tl_dir} {游戏名} {版本}
```
<details>
<summary><b>💡关于new命令 (点击展开)</b></summary>

- 它会递归扫描{tl_dir}目录下所有后缀名为`.rpy`的文件。
- 它只获取每个rpy中的new_str==old_str的文本，也就是我们认为原始文本"Hello world!"的待翻译文本，如下所示：
    > ```txt
    > # game/ImaniEvents.rpy:11
    > translate chinese callimanimorning_88744462:
    > 
    >     # "Hello world!"   <= old_str
    >     "Hello world!"     <= new_str
    > ```
  并把"callimanimorning_88744462"作为翻译的索引号，这与RenPy行为保持一致。
</details>
它参数说明和`old`命令类似。

一个例子：

![](imgs/new.png)

> **🚨注意🚨**<br />
> 我们使用RenPy SDK生成翻译文件时候需要保留原始文本，不要勾选未翻译生成空字符串的选项：

![](./imgs/renpy.png)

之后生成的rpy文件应该是这样的：

> ```txt
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "She doesn’t pick up."
>     "She doesn’t pick up."
> ```

只有这样格式的rpy，才能代码才可以识别原始文本然后进行替换。

## 3.从旧版本翻译项目合并到新版本中（如果您在第1步跳过，这里也请跳过）

首先查看我们已有项目，使用`l`命令：

![](imgs/list_new.png)

之后我们使用`merge`或者`m`命令来将旧版本`mygame v0.0.1`已有翻译文本被合并到新版`mygame v0.0.2`中，这会使得新版中存在的旧版本文本得到翻译，充分利用了旧版本的翻译文本。我们只需指定它们的索引进行操作：

```shell
 m {旧翻译项目索引} {新翻译项目索引}
```
<details>
<summary><b>💡关于merge命令 (点击展开)</b></summary>

- 它会根据具有相同的索引号的文本将一个翻译项目中的已经翻译文本应用到另一个项目的未翻译文本中。
- 注意它不会对任何rpy文件做出修改，合并过程只发生在保存的pt文件（这是我们翻译项目保存的二进制文件）中。pt文件所在目录你可以在[config.ini](config.ini)的`PROJECT_PATH`中找到。
</details>
一个例子：

![](imgs/merge.png)

这了需要输入`Y`或`y`来确认指令执行。输入完后，我们可以看到我们利用旧版本`mygame v0.0.1`中13条翻译过的文本到新版本`mygame v0.0.2`中，现在我们只需要翻译剩下的7条即可！！！

再次输入`l`命令看看：

![](imgs/list_merge.png)

我们看到新版本`mygame v0.0.2`中已翻译文本和未翻译的文本数量发生改变，这说明`merge`起作用了。

## 4.使用翻译引擎翻译剩余的文本：
在这里，您可以使用以下命令完成剩余文本的翻译：
- [savehtml和loadhtml命令](#使用savehtml和loadhtml快速翻译浏览器自带网页翻译)
- [dltranslate命令](#使用dltranslate命令进行ai翻译)
- [saveexcel和loadexcel命令](#使用saveexcel和loadexcel快速翻译)

下面我们将介绍最原始翻译命令：


> **🚨注意🚨**<br />
> 如果您没有完成[运行环境准备-步骤2](#2安装chrome浏览器和chrome-driver)，导致缺少Chrome浏览器和相应的chromedriver，`translate`命令将无法运行。

使用`translate`或者`t`命令，只需要指定要翻译项目索引和翻译引擎即可。
```shell
 t {project_idx} {translation_API} {num_workers=1}
```
可用的`{translation_API}`有caiyu, google, baidu, and youdao。我们移除旧版本的`deepl`，因为它的问题很多。
`{num_workers}` 是可选的，表示要启动的浏览器数量，数量越多翻译速度越快，但是资源消耗量大。

一个例子：

![](imgs/translate.png)

这里程序等待您的确认以开始执行。我们可以看到启动两个窗口，这里您可以配置您的翻译目标，如设置从英语到中文的翻译：

![](imgs/chrome_set.png)

记得，每个窗口保证相同的翻译目标设置。然后在输入`Y`或`y`在进行下一步操作，程序开始自动翻译：

![](imgs/translate_list.png)

我们使用`l`可以看到`mygame v0.0.2`已经翻译完了。

## 5.生成&替换

使用`apply`或`a`命令生成真实翻译文件，这也就是说：我么们之前操作并不会对原始文件进行修改，也不需要像旧版本那样拷贝rpy文件：

```shell
 a {project_idx}
```
<details>
<summary><b>💡关于apply命令 (点击展开)</b></summary>

- 注意它不会对任何rpy文件做出修改，生成的rpy文件所在目录你可以在`PROJECT_PATH/你的项目名_版本名`中找到。
- apply命令只使用翻译的文本替换未翻译的new_str，因此生成rpy文件结构不会改变。
- apply命令默认会为翻译文本添加特殊标记(`@@`或者`@$`)。
</details>
一个例子：

![](imgs/apply.png)

您可以在`./projz\mygame_v0.0.2`目录下找到它们，而且它具有和原始路径一样的目录结构：

![](imgs/apply_dir.png)

这意味您可以将这个文件夹剪切到新版本游戏中的原始目录进行替换，当然请记得做好备份工作。

> **🚨注意🚨**<br />
> 在使用`apply`命令后翻译文本前面会带有一些特殊符号：
> - 使用翻译引擎的翻译文本在前面会带有`@@`符号，它表明这段文本经过了机器翻译，这用于后期翻译润色工作。
> - 使用old命令产生的翻译文本在前面会带有`@$`符号，这用于指示这是来至旧版本的翻译。

> 如果您需要在去除它们，在配置文件中[config.ini](config.ini)设置配置项`REMOVE_MARKS`=True，重新启动程序后，再使用`apply`命令即可。

# 命令说明
关于`new`, `old`, `list`, `merge`, `apply`和`translate`命令说明见[这里](#快速开始)
> **💡提示💡**<br />
> 每个命令的详细说明可以使用在程序运行后输入`help`查看

## 关于greedy参数
在`new`, `old`, `reold`,` apply`命令中可以看到有个可选的参数是greedy, 这表示扫描rpy文件是否开启贪婪扫描。
一般的，用Renpy SDK生成翻译块的标准格式如下：
> ```txt
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "She doesn’t pick up."
>     "She doesn’t pick up."
> ```
其中，我们每一行的间隔都固定的。当greedy=False，扫描的rpy文件每个块都将进行严格的检查。
而当greedy=True，将会放宽这种检查，因此可以扫描到以下翻译块：
> ```txt
> translate chinese callimanimorning_88744462:
>     "She doesn’t pick up."
> ```
而这是greedy=False情况扫描不到的，一般的greedy默认True，基本可以扫描到所有翻译块。

## dump或du
```shell
dump {proj_idx} {lang} {scope}
```
- {lang} 是可选的，指定导出翻译语言
- {scope} 是可选的，指定导出文本范围：
  - `trans`：已翻译文本
  - `untrans`：未翻译文本
  - `all`：所有文本

说明：该命令将指定的项目中所有未翻译和已翻译的文本按所在rpy文件行顺序导出在excel文件中，每个rpy文件占用一个sheet。excel文件保存在`PROJECT_PATH/excel`中。它通常配合[update](#update或up)命令使用。

## update或up
```shell
update {proj_idx} {lang} {excel_file}
```
- {lang} 是可选的，指定导入的翻译语言
- {excel_file} 是可选的，指定导入的excel文件，默认从配置路径加载excel

说明：该命令默认从`PROJECT_PATH/excel`加载对应项目的excel文件，并根据excel内容更新项目中未翻译和已翻译的文本。这使得您可以手动修改翻译结果，因此它可以配合[dump](#dump或du)命令使用。
> **🚨注意🚨**<br />
> 该命令仅关注excel文件的`Translation Index (Don't modify)`和`Translated Text`所在列，修改其他列不会影响命令的执行，因此其他列所在内容不会进行相应更新。

## reold或ro
```shell
reold {proj_idx} {greedy=True}
```
- {greedy} 是可选的，默认为True，表示扫描跟多的翻译文本。
说明：指定一个项目的索引。该命令相当于重新针对该项目运行`old`命令：
```shell
old proj.tl_path proj.name proj.tag
```
这个命令用于当游戏tl文件夹下的翻译文件更新时，重新载入翻译项目的所有翻译文本。

## revert或r
```shell
revert {proj_idx}
```
说明：该命令将生成新的rpy文件，使得所有已翻译文本变为原始未翻译的状态（new_str <- old_str）。生成rpy文件可以在`PROJECT_PATH/你的项目名_版本名`下找到。
假设你所配置某个项目的tl目录下的某个rpy文件内容如下：
> ```txt
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "She doesn’t pick up."
>     "她没接听。"
> ```

那么使用`revert`命令生成的rpy文件将会是：

> ```txt
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "She doesn’t pick up."
>     "She doesn’t pick up."
> ```

> **🚨注意🚨**<br />
> 该命令不会影响到项目中已经翻译的文本，也就是说，项目中所有已翻译和未翻译文本不会发生改变。它只是一个工具，用于生成一个未翻译的rpy文件，这点和RenPy SDK生成翻译文件很像。

## removeempty或re
```shell
removeempty {proj_idx}
```
说明：该命令用于将一个项目中已翻译文本（new_str==''）为空，但是原始文本不为空（old_str!=''）的文本迁移到未翻译文本中，用于下次翻译。
已翻译文本为空，但是原始文本不为空的文本就如下面这种情况：
> ```txt
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "She doesn’t pick up." # 这是原始文本
>     ""  # 这是翻译文本
> ```
假设一个项目存在这样的已翻译文本，那么使用`removeempty 0`命令前：
```txt
+---------------+-------------------+----------------+--------------------+----------------------+
| Project Index |      Project      |      Tag       | Translated line(s) | Untranslated line(s) |
+---------------+-------------------+----------------+--------------------+----------------------+
|       0       |         a         |       a        |   chinese: 15      |      chinese: 0      |
+---------------+-------------------+----------------+--------------------+----------------------+
```
使用`removeempty 0`命令后：
```txt
+---------------+-------------------+----------------+--------------------+----------------------+
| Project Index |      Project      |      Tag       | Translated line(s) | Untranslated line(s) |
+---------------+-------------------+----------------+--------------------+----------------------+
|       0       |         a         |       a        |   chinese: 13      |      chinese: 2      |
+---------------+-------------------+----------------+--------------------+----------------------+
```

## accept或ac
```shell
accept {proj_idx}
```
说明：该命令用于将一个项目中未翻译文本强制迁移到已翻译的文本中。假设项目存在如下这种翻译文本，这些都是翻译文本都是符号，无需要再次翻译：
> ```txt
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "..." # 这是原始文本
>     "..."  # 这是翻译文本
> ```
假设一个项目存在这样的未翻译文本，那么使用`accept 0`命令前：
```txt
+---------------+-------------------+----------------+--------------------+----------------------+
| Project Index |      Project      |      Tag       | Translated line(s) | Untranslated line(s) |
+---------------+-------------------+----------------+--------------------+----------------------+
|       0       |         a         |       a        |   chinese: 15      |      chinese: 5      |
+---------------+-------------------+----------------+--------------------+----------------------+
```
使用`accept 0`命令后：
```txt
+---------------+-------------------+----------------+--------------------+----------------------+
| Project Index |      Project      |      Tag       | Translated line(s) | Untranslated line(s) |
+---------------+-------------------+----------------+--------------------+----------------------+
|       0       |         a         |       a        |   chinese: 20      |      chinese: 0      |
+---------------+-------------------+----------------+--------------------+----------------------+
```

# config.ini配置说明
```text
[GLOBAL]
# 日志文件目录
LOG_PATH=./projz/log
# 生成的rpy保存目录
PROJECT_PATH=./projz
# translate命令默认启动浏览器数量
NUM_WORKERS=2
# chrome driver路径，这与translate命令有关
CHROME_DRIVER=D:\Users\Surface Book2\Downloads\chromedriver_win32\chromedriver.exe
# AI翻译保存地址，这与dltranslate命令有关
MODEL_SAVE_PATH=
# 使用apply命令生成rpy文件，是否移除`@@`或者`@$`符号
REMOVE_MARKS=True
# 使用'translate'或'dltranslate'命令，是否要去除<i>, <size>, <color>等标签
STRIP_TAGS=False
# 添加RenPy一些关键字 (用','分割). 通过添加一些关键字，使得项目能够扫描下面这些翻译文本
# 如果不添加无法扫描到
#    # voice "sound/voice/eri/eri_0001.ogg"
#    # eri "hello world！"
#    voice "sound/voice/eri/eri_0001.ogg"
#    eri "你好世界！"
KEYWORDS=voice
```

# 常见问题
<details>
<summary>💡关于运行 (点击展开)</summary>

Q: 如何使用该工具？需要安装什么东西吗？<br />
A: 如果您是Windows系统用户，可以直接打开[parse_console.exe](parse_console.exe)运行该工具而无需安装任何东西。也可以使用Python脚本运行，但是您可能需要安装一些必要运行库。详细信息见：[运行环境准备](#运行环境准备)

</details>

<details>
<summary>💡关于翻译 (点击展开)</summary>

Q: 使用这个工具就可以翻一个RenPy游戏吗？<br />
A: 不行，这个工具只是工作在在RenPy SDK生成rpy翻译文件，将文件内待翻译文本进行翻译。因此您还需其他前置或者后置步骤进行翻译游戏，您可以参考RenPy官网或者网上获取更多信息。

Q: 使用这个工具会对原始游戏文件进行修改吗？<br />
A: 不会的，该工具部分命令最多扫描您指定`game/tl/`目录下的rpy翻译文件，不会产生任何修改。使用某些命令生成的rpy文件可以在`config.ini`中`PROJECT_PATH`指定的目录找到。

Q: 我在`./proz`发现的一些以`.pt`结尾文件，这是什么？<br />
A: 这是我们保存项目的状态文件，它记录了一个翻译项目所有翻译和未翻译文本的信息。它的文件大小跟游戏所包含的翻译文本量决定。一般情况下，您可以忽略它们。如果您不需要这个翻译项目，您可以手动删除它或者使用`delete`命令删除它。

Q: 我如何手动修改翻译结果或者手动翻译？<br />
A: 见[dump](#dump或du)和[update](#update或up)命令。

Q: 使用`apply`命令会在文本前面产生`@@`或者`@$`符号？<br />
A: 见[apply](#5生成替换)命令中的注意事项。
</details>

<details>
<summary>💡关于一些术语 (点击展开)</summary>

Q: 项目或者翻译项目<br />
A: 您可以使用`new`或者`old`命令创建一个（翻译）项目，这是命令操作基本单位。

Q: 项目索引<br />
A: 当您创建好一个项目时候，可以使用`list`命令查看存在的项目，其中`Project Index`所在列就是这个项目对应的索引，这就是很多命令中需要指定的{proj_idx}参数。使用`list`命令可以看到类似下面的输出：
```txt
+---------------+-------------------+----------------+--------------------+----------------------+
| Project Index |      Project      |      Tag       | Translated line(s) | Untranslated line(s) |
+---------------+-------------------+----------------+--------------------+----------------------+
|       0       |         a         |       a        |   chinese: 20      |      chinese: 0      |
+---------------+-------------------+----------------+--------------------+----------------------+
|       1       |         b         |       b        |   chinese: 0       |     chinese: 15      |
+---------------+-------------------+----------------+--------------------+----------------------+
```
Q: {lang}参数<br />
A: 一些命令可以指定{lang}参数，一般来说，当我们使用`new`或者`old`命令创建一个（翻译）项目，假设指定的目录为`game/tl/chinese`，那么这个项目一般只有这个`chinese`语言选项。一个项目可能的{lang}可以使用`list`命令查看`Translated line(s)`或者`Untranslated line(s)`所在列。对于所有带有{lang}参数的命令来说，一般您无需指定它，命令会选择默认的{lang}。

Q: 翻译索引，lang，new_str, old_str，原始文本，新文本<br />
A: 在一个rpy翻译文件中，一个翻译条目:
> ```txt
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "Hello world!"   <= old_str,原始文本
>     "你好世界！"        <= new_str,新文本
> ```
翻译索引是：callimanimorning_88744462<br />
lang是：chinese<br />
new_str或者新文本是：你好世界！<br />
old_str或者原始文本是：Hello world!<br />
</details>



# 🗒Todo List:

1. [x] ~~添加excel导入导出功能~~ (Done at 20230819)
2. [ ] 添加英语文档
3. [x] ~~添加AI模型翻译~~ (Done at 20230908)

# 🔗Acknowledgement

我们参考或调用代码：

* 早期项目代码（Web翻译）参考：[Maooookai(Mirage)](https://github.com/Maooookai/WebTranslator), [DrDRR](https://github.com/DrDRR/RenPy-WebTranslator/commits?author=DrDRR "View all commits by DrDRR")
* 使用的AI翻译库：[dl-translate](https://github.com/xhluca/dl-translate)
* 其他使用的python库见：[requirements.txt](./requirements.txt)
